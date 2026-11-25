#!/usr/bin/env python3
"""Review one exact head SHA: download, install, run the repo checks, clean up.

Run with `python3 -I`. Every step is its own subcommand so a reviewer runs one simple command per step:

  fetch   <owner/repo> <sha>   download the tarball of <sha> with gh (GET only), extract it into a new run dir
  install <run-dir>            npm ci --ignore-scripts with a cache inside the run dir (only with package-lock.json)
  check   <run-dir>            run the repo checks; full output of each goes to a log file outside the run dir
  clean   <run-dir>            delete the run dir; the log dir stays
  run     <owner/repo> <sha>   all four steps in order; the run dir is deleted even when a step fails

--dry-run prints the steps without running gh, npm or a check. Exit codes: 0 ok, 1 a step or check failed,
2 bad usage, 3 no check found. The downloaded code is untrusted: checks run with a scrubbed environment (no
tokens, HOME inside the run dir) and a timeout, but they still run the repo's own code.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

PREFIX = "pr-head-review-"
SHA_RE = re.compile(r"[0-9a-f]{40}")
# GitHub owner: letters, digits, single hyphens, no leading hyphen. Repo: letters, digits, . _ - but not a leading
# dot or hyphen, and never "." or "..".
REPO_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_][A-Za-z0-9._-]{0,99}")
META = "meta.json"
KEEP_ENV = ("PATH", "LANG", "LC_ALL", "TERM", "TZ")


class UsageError(Exception):
    pass


def say(msg: str) -> None:
    print(msg, flush=True)


def tmp_root() -> Path:
    return Path(tempfile.gettempdir()).resolve()


def validate_repo(repo: str) -> str:
    if not REPO_RE.fullmatch(repo) or ".." in repo:
        raise UsageError(f"bad owner/repo: {repo!r}")
    return repo


def validate_sha(sha: str) -> str:
    if not SHA_RE.fullmatch(sha):
        raise UsageError(f"bad sha (need 40 lowercase hex): {sha!r}")
    return sha


def run_dir_path(arg: str) -> Path:
    """A run dir has the shape fetch creates: a direct child of $TMPDIR named pr-head-review-* (not a log dir)."""
    run = Path(arg).resolve()
    if run.parent != tmp_root() or not run.name.startswith(PREFIX) or run.name.startswith(PREFIX + "logs-"):
        raise UsageError(f"not a run dir under {tmp_root()}: {arg}")
    return run


def load_run_dir(arg: str) -> tuple[Path, dict]:
    """Accept only a run dir this script created: the run dir shape plus a valid meta file."""
    run = run_dir_path(arg)
    meta_path = run / META
    if not meta_path.is_file():
        raise UsageError(f"no {META} in {run} (run fetch first)")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise UsageError(f"{META} is not valid JSON: {exc}") from exc
    if not isinstance(meta, dict):
        raise UsageError(f"{META} is not a JSON object")
    # Checks run untrusted code that can rewrite this file: trust only paths of the shape fetch creates.
    if not isinstance(meta.get("logs"), str) or not isinstance(meta.get("src", ""), str) \
            or not isinstance(meta.get("steps", []), list):
        raise UsageError(f"{META} has a field of the wrong type")
    logs = Path(meta["logs"]).resolve()
    if logs.parent != tmp_root() or not logs.name.startswith(PREFIX + "logs-"):
        raise UsageError(f"{META} has an unexpected log dir: {logs}")
    if "src" in meta and Path(meta["src"]).resolve().parent != run / "extract":
        raise UsageError(f"{META} has an unexpected src dir: {meta['src']}")
    return run, meta


def save_meta(run: Path, meta: dict) -> None:
    (run / META).write_text(json.dumps(meta, indent=1), encoding="utf-8")


def mark_step(run: Path, meta: dict, step: str) -> None:
    meta.setdefault("steps", []).append(step)
    save_meta(run, meta)


def check_env(run: Path) -> dict:
    """Environment for untrusted code: no tokens or other secrets, HOME and caches inside the run dir."""
    env = {k: os.environ[k] for k in KEEP_ENV if k in os.environ}
    home = run / "home"
    home.mkdir(exist_ok=True)
    env.update(HOME=str(home), TMPDIR=str(run / "tmp"), CI="1", npm_config_cache=str(run / "npm-cache"),
               npm_config_update_notifier="false", PYTHONDONTWRITEBYTECODE="1")
    (run / "tmp").mkdir(exist_ok=True)
    return env


def run_logged(argv: list[str], cwd: Path, env: dict, out, timeout: int) -> int:
    """Run in a new process group and kill the whole group at the end, so a timeout or a background process
    (`node server &`, test workers) does not outlive the step. Returns 124 on timeout."""
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
    timed_out = False
    try:
        # Wait without reaping (WNOWAIT): the exited leader stays a zombie, so its pid and process group id cannot
        # be reused by an unrelated process before killpg below.
        deadline = time.monotonic() + timeout
        while os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.05)
    finally:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        code = proc.wait()
    if timed_out:
        out.write(f"\ntimeout after {timeout}s\n".encode())
        return 124
    return code


def extract(tar_path: Path, dest: Path, sha: str) -> Path:
    with tarfile.open(tar_path, "r:gz") as tf:
        comment = tf.pax_headers.get("comment", "")
        if comment != sha:
            raise RuntimeError(f"tarball commit {comment!r} does not match {sha}")
        tf.extractall(dest, filter="data")
    tops = [p for p in dest.iterdir()]
    if len(tops) != 1 or not tops[0].is_dir():
        raise RuntimeError(f"expected one top dir in the tarball, found {len(tops)}")
    return tops[0]


def git_snapshot(run: Path, src: Path, sha: str, log: Path) -> None:
    """A tarball has no .git, and checks that call git (secret scans, diffs) fail without one. Make a local
    one-commit repo of the extracted files: no hooks, no signing, no user or system git config."""
    if not shutil.which("git"):
        say("git snapshot skipped: git not installed")
        return
    env = {**check_env(run), "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "pr-head-review",
           "GIT_AUTHOR_EMAIL": "pr-head-review@localhost", "GIT_COMMITTER_NAME": "pr-head-review",
           "GIT_COMMITTER_EMAIL": "pr-head-review@localhost"}
    safe = ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false"]
    with open(log, "ab") as out:
        # -f and --allow-empty: files the repo's own .gitignore matches are still part of the head.
        for args in (["init", "-q"], ["add", "-A", "-f"],
                     ["commit", "-q", "--no-verify", "--allow-empty", "-m", f"head {sha}"]):
            code = run_logged([*safe, *args], src, env, out, 300)
            if code != 0:
                raise RuntimeError(f"git {args[0]} failed (exit {code}), see {log}")


def gitattributes_subst(src: Path) -> list[str]:
    """Non-comment .gitattributes lines that set export-subst (not unset with - or !)."""
    hits = []
    for p in src.rglob(".gitattributes"):
        if not p.is_file() or ".git" in p.relative_to(src).parts:
            continue
        for line in p.read_text(errors="replace").splitlines():
            parts = line.strip().split()
            if parts and not parts[0].startswith("#") and ("export-subst" in parts[1:] or "export-subst=true" in parts[1:]):
                hits.append(f"{p.relative_to(src)}: {line.strip()[:80]}")
    return hits


def compare_tree(repo: str, sha: str, src: Path, run: Path, log: Path) -> None:
    """GitHub builds the tarball with git archive, which honors .gitattributes export-ignore and export-subst, so
    the extracted files can differ from the commit. Compare the file list with the git tree of the SHA: a
    difference, or a tree that cannot be read or is truncated, fails fetch: the checks would not run on a head we
    can prove."""
    subst = gitattributes_subst(src)
    if subst:
        raise RuntimeError(f"export-subst changes file contents in the tarball: {subst[:3]}")
    tree_path = run / "tree.json"
    try:
        with open(tree_path, "wb") as out, open(log, "ab") as err:
            code = subprocess.run(["gh", "api", "--method", "GET", f"repos/{repo}/git/trees/{sha}?recursive=1"],
                                  stdout=out, stderr=err, timeout=300).returncode
    except subprocess.TimeoutExpired:
        code = 124
    if code != 0:
        raise RuntimeError(f"could not read the git tree of the head (exit {code}), see {log}")
    try:
        tree = json.loads(tree_path.read_text(encoding="utf-8"))
        wanted = {e["path"] for e in tree["tree"] if e.get("type") == "blob"}
    except (ValueError, KeyError, TypeError, AttributeError, RecursionError) as exc:
        raise RuntimeError(f"unreadable git tree of the head ({exc})") from exc
    if tree.get("truncated"):
        raise RuntimeError("git tree truncated by GitHub: cannot prove the tarball matches the head")
    got = set()
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not (root == str(src) and d == ".git")]
        rel = Path(root).relative_to(src)
        got.update(str(rel / f) if str(rel) != "." else f for f in files)
        got.update(str(rel / d) for d in dirs if (Path(root) / d).is_symlink())
    missing, extra = sorted(wanted - got), sorted(got - wanted)
    if missing or extra:
        raise RuntimeError(f"tested files differ from the head (.gitattributes export-ignore?): {len(missing)} missing "
                           f"{missing[:5]}, {len(extra)} extra {extra[:5]}")
    say("tree check: extracted files match the git tree of the head")


def cmd_fetch(repo: str, sha: str, dry: bool) -> tuple[Path, Path] | None:
    validate_repo(repo)
    validate_sha(sha)
    api = ["gh", "api", "--method", "GET", f"repos/{repo}/tarball/{sha}"]
    if dry:
        say("step fetch: " + " ".join(api) + " > <run-dir>/head.tar.gz ; extract into <run-dir>/extract ; compare with the git tree ; "
            "local one-commit git repo of the files")
        return None
    run = Path(tempfile.mkdtemp(prefix=PREFIX, dir=tmp_root()))
    logs = Path(tempfile.mkdtemp(prefix=f"{PREFIX}logs-{sha[:7]}-", dir=tmp_root()))
    meta = {"repo": repo, "sha": sha, "logs": str(logs), "steps": []}
    save_meta(run, meta)
    say(f"run dir: {run}")
    say(f"log dir: {logs}")
    tar_path = run / "head.tar.gz"
    try:
        with open(tar_path, "wb") as out, open(logs / "fetch.log", "wb") as err:
            code = subprocess.run(api, stdout=out, stderr=err, timeout=600).returncode
        if code != 0:
            say(f"fetch exit={code} log={logs / 'fetch.log'}")
            raise RuntimeError("gh api failed")
        extract_dir = run / "extract"
        extract_dir.mkdir()
        src = extract(tar_path, extract_dir, sha)
        tar_path.unlink()
        compare_tree(repo, sha, src, run, logs / "fetch.log")
        git_snapshot(run, src, sha, logs / "fetch.log")
    except BaseException:
        shutil.rmtree(run, ignore_errors=True)
        say(f"fetch failed: removed {run}")
        raise
    meta["src"] = str(src)
    mark_step(run, meta, "fetch")
    say(f"fetch exit=0 src={src}")
    return run, logs


def cmd_install(run_arg: str | None, dry: bool) -> int:
    if dry:
        say("step install: npm ci --ignore-scripts (npm_config_cache=<run-dir>/npm-cache), only with package-lock.json; "
            "refused when a .npmrc exists or a dependency is not from registry.npmjs.org")
        return 0
    run, meta = load_run_dir(run_arg)
    if "fetch" not in meta.get("steps", []):
        raise UsageError("install before fetch")
    src, logs = Path(meta["src"]), Path(meta["logs"])
    if not (src / "package-lock.json").is_file():
        say("install skipped: no package-lock.json")
        mark_step(run, meta, "install")
        return 0
    refused = install_risks(src)
    if refused:
        say("install refused: " + "; ".join(refused) + ". Read them before installing by hand.")
        return 1
    log = logs / "install.log"
    with open(log, "wb") as out:
        code = run_logged(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], src, check_env(run), out, 1800)
    say(f"install exit={code} log={log}")
    mark_step(run, meta, "install")
    return 0 if code == 0 else 1


NPM_REGISTRY = "https://registry.npmjs.org/"
VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.+-]+)?")  # an exact registry version
RANGE_RE = re.compile(r"(?!\s*\.)[0-9A-Za-z.*^~<>=|+ -]*")  # semver range or dist-tag; no ':', '/' or leading '.'
ALIAS_RE = re.compile(r"npm:(?:@[\w.-]+/)?[\w.-]+(?:@[0-9A-Za-z.*^~<>=|+ -]*)?")


def install_risks(src: Path) -> list[str]:
    """--ignore-scripts is not a barrier: a repo .npmrc can set git=<script>, which npm runs to fetch a git
    dependency. Allowlist, not a list of bad prefixes: refuse any .npmrc, any package.json dependency spec that is
    not a registry range or npm: alias, and any lockfile package that does not resolve to the npm registry."""
    risks = [f"{p.relative_to(src)} present" for p in src.rglob(".npmrc") if ".git" not in p.relative_to(src).parts]
    try:
        pkg = json.loads((src / "package.json").read_text(encoding="utf-8")) if (src / "package.json").is_file() else {}
        for field in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            for name, spec in (pkg.get(field) or {}).items():
                if not isinstance(spec, str) or not (RANGE_RE.fullmatch(spec) or ALIAS_RE.fullmatch(spec)):
                    risks.append(f"package.json {field}.{name} = {str(spec)[:80]}")
        lock = json.loads((src / "package-lock.json").read_text(encoding="utf-8"))
        packages = lock.get("packages")
        if packages is not None:  # v2/v3: npm ci reads only this section; v2's legacy "dependencies" is ignored
            for key, entry in packages.items():
                fetched = key.startswith("node_modules/") or "/node_modules/" in key
                # inBundle is trusted only inside another package (shipped in that package's registry tarball).
                nested = key.count("node_modules/") > 1
                risks += lock_entry_risks(src, f"packages[{key!r}]", entry, fetched, nested)
        else:  # lockfile v1, nested
            stack = [(k, v, False) for k, v in (lock.get("dependencies") or {}).items()]
            while stack:
                name, entry, nested = stack.pop()
                risks += lock_entry_risks(src, f"dependencies.{name}", entry, True, nested)
                if isinstance(entry, dict):
                    stack += [(f"{name}>{k}", v, True) for k, v in (entry.get("dependencies") or {}).items()]
    except (ValueError, AttributeError, TypeError, RecursionError) as exc:
        risks.append(f"package.json or package-lock.json unreadable ({exc})")
    return risks


def inside(src: Path, rel) -> bool:
    if not isinstance(rel, str) or ":" in rel or "\\" in rel or rel.startswith(("/", "~")):
        return False
    return (src / rel).resolve().is_relative_to(src.resolve())


def lock_entry_risks(src: Path, label: str, entry, fetched: bool, nested: bool) -> list[str]:
    """A fetched package must resolve to the registry; a workspace link must point inside the tree."""
    if not isinstance(entry, dict):
        return [f"lockfile {label} is not an object"]
    if nested and (entry.get("inBundle") or entry.get("bundled")):
        return []
    resolved, version = entry.get("resolved"), entry.get("version")
    if entry.get("link"):
        return [] if inside(src, resolved) else [f"lockfile {label} links to {str(resolved)[:80]}"]
    if version is not None and not (isinstance(version, str) and (VERSION_RE.fullmatch(version) or ALIAS_RE.fullmatch(version))):
        return [f"lockfile {label} version {str(version)[:80]}"]
    if resolved is not None and not (isinstance(resolved, str) and resolved.startswith(NPM_REGISTRY)):
        return [f"lockfile {label} resolves to {str(resolved)[:80]}"]
    if fetched and resolved is None:
        return [f"lockfile {label} has no resolved registry URL"]
    return []


def has_dep(pkg: dict, name: str) -> bool:
    return any(isinstance(pkg.get(k), dict) and name in pkg[k] for k in ("dependencies", "devDependencies"))


def plan_checks(src: Path) -> list[tuple[str, list[str]]]:
    """Which checks to run, first rule that matches wins:
    1. scripts/verify exists: run it, nothing else.
    2. package.json: for each of typecheck, lint, test, run `npm run --ignore-scripts <name>` when the repo defines
       that script; otherwise the plain tool when it is a dependency (tsc --noEmit with a tsconfig.json,
       eslint ., vitest run), always with `npx --no-install`.
    3. Python (pyproject.toml, setup.py or a tests/ dir with .py files): python3 -I -m unittest discover, also when
       a package.json planned no check. With tests/__init__.py the repo root is the top dir (so tests can import
       the package); without it only tests/ is importable, because -I keeps the cwd off sys.path.
    """
    verify = src / "scripts" / "verify"
    if verify.is_file():
        return [("verify", ["bash", "scripts/verify"] if not os.access(verify, os.X_OK) else ["scripts/verify"])]
    pkg_path = src / "package.json"
    if pkg_path.is_file():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise RuntimeError(f"package.json is not valid JSON: {exc}") from exc
        if not isinstance(pkg, dict):
            raise RuntimeError("package.json is not a JSON object")
        scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
        fallback = {
            "typecheck": (has_dep(pkg, "typescript") and (src / "tsconfig.json").is_file(), ["tsc", "--noEmit"]),
            "lint": (has_dep(pkg, "eslint"), ["eslint", "."]),
            "test": (has_dep(pkg, "vitest"), ["vitest", "run"]),
        }
        checks = []
        for name, (ok, tool) in fallback.items():
            if name in scripts:
                checks.append((name, ["npm", "run", "--ignore-scripts", name]))
            elif ok:
                checks.append((name, ["npx", "--no-install", *tool]))
        if checks:
            return checks
    tests = src / "tests"
    if (src / "pyproject.toml").is_file() or (src / "setup.py").is_file() or any(tests.glob("*.py")):
        args = ["-s", "tests"] if tests.is_dir() else []
        if (tests / "__init__.py").is_file():
            args += ["-t", "."]
        # The same interpreter as this script, so the 3.12+ "exit 5 when no tests ran" holds.
        return [("unittest", [sys.executable, "-I", "-m", "unittest", "discover", *args])]
    return []


def cmd_check(run_arg: str | None, dry: bool, timeout: int) -> int:
    if dry:
        say("step check: scripts/verify, else package.json typecheck/lint/test, else python3 -I -m unittest; "
            "one log file per check in the log dir")
        return 0
    run, meta = load_run_dir(run_arg)
    if "fetch" not in meta.get("steps", []):
        raise UsageError("check before fetch")
    src, logs = Path(meta["src"]), Path(meta["logs"])
    checks = plan_checks(src)
    if not checks:
        say("check: no scripts/verify, package.json checks or Python tests found")
        mark_step(run, meta, "check")
        return 3
    env = check_env(run)
    worst = 0
    for name, argv in checks:
        log = logs / f"check-{name}.log"
        with open(log, "wb") as out:
            out.write(("$ " + " ".join(argv) + "\n").encode())
            out.flush()
            try:
                code = run_logged(argv, src, env, out, timeout)
            except FileNotFoundError as exc:
                code = 127
                out.write(f"\n{exc}\n".encode())
        say(f"check {name} exit={code} log={log}")
        if name == "unittest" and code == 5:  # Python 3.12+: no tests ran (e.g. pytest-style tests)
            say("check unittest ran no tests: report no checks, not a pass")
            worst = worst or 3
        elif code:
            worst = 1
    mark_step(run, meta, "check")
    return worst


def cmd_clean(run_arg: str | None, dry: bool) -> int:
    if dry:
        say("step clean: delete <run-dir>; the log dir stays")
        return 0
    # Only the path shape is checked, not meta.json: the checks ran untrusted code that may have deleted or
    # rewritten it, and the run dir must still go.
    run = run_dir_path(run_arg)
    if not run.is_dir():
        raise UsageError(f"no run dir at {run}")
    shutil.rmtree(run)
    say(f"clean: removed {run}; logs kept in the log dir fetch printed")
    return 0


def cmd_run(repo: str, sha: str, dry: bool, timeout: int) -> int:
    if dry:
        cmd_fetch(repo, sha, True)
        cmd_install(None, True)
        cmd_check(None, True, timeout)
        cmd_clean(None, True)
        return 0
    fetched = None
    try:
        fetched = cmd_fetch(repo, sha, False)
        code = cmd_install(str(fetched[0]), False)
        if code:
            return code
        return cmd_check(str(fetched[0]), False, timeout)
    finally:
        # Not cmd_clean: it re-reads meta.json, which the checks could have rewritten.
        if fetched is not None and fetched[0].exists():
            shutil.rmtree(fetched[0], ignore_errors=True)
            say(f"clean: removed {fetched[0]}; logs kept in {fetched[1]}")


def positive_int(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return n


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 12):
        print("error: needs Python 3.12+ (tarfile extraction filter, unittest exit 5 when no tests ran)",
              file=sys.stderr)
        return 2
    p = argparse.ArgumentParser(prog="pr_head_review.py", description=__doc__.split("\n")[0])
    p.add_argument("--dry-run", action="store_true", help="print the steps, run nothing")
    p.add_argument("--timeout", type=positive_int, default=900, help="seconds per check (default 900)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("fetch", "run"):
        s = sub.add_parser(name)
        s.add_argument("repo")
        s.add_argument("sha")
    for name in ("install", "check", "clean"):
        sub.add_parser(name).add_argument("run_dir")
    try:
        a = p.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        if a.cmd == "fetch":
            cmd_fetch(a.repo, a.sha, a.dry_run)
            return 0
        if a.cmd == "run":
            return cmd_run(a.repo, a.sha, a.dry_run, a.timeout)
        if a.cmd == "install":
            return cmd_install(a.run_dir, a.dry_run)
        if a.cmd == "check":
            return cmd_check(a.run_dir, a.dry_run, a.timeout)
        return cmd_clean(a.run_dir, a.dry_run)
    except UsageError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 2
    except (RuntimeError, tarfile.TarError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
