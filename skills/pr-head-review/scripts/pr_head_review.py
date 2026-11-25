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
import subprocess
import sys
import tarfile
import tempfile
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


def load_run_dir(arg: str) -> tuple[Path, dict]:
    """Accept only a run dir this script created: a direct child of $TMPDIR with our prefix and meta file."""
    run = Path(arg).resolve()
    if run.parent != tmp_root() or not run.name.startswith(PREFIX) or run.name.startswith(PREFIX + "logs-"):
        raise UsageError(f"not a run dir under {tmp_root()}: {arg}")
    meta_path = run / META
    if not meta_path.is_file():
        raise UsageError(f"no {META} in {run} (run fetch first)")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    # Checks run untrusted code that can rewrite this file: trust only paths of the shape fetch creates.
    logs = Path(meta.get("logs", "")).resolve()
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
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "--no-verify", "-m", f"head {sha}"]):
            code = subprocess.run([*safe, *args], cwd=src, env=env, stdout=out, stderr=subprocess.STDOUT,
                                  timeout=300).returncode
            if code != 0:
                raise RuntimeError(f"git {args[0]} failed (exit {code}), see {log}")


def cmd_fetch(repo: str, sha: str, dry: bool) -> Path | None:
    validate_repo(repo)
    validate_sha(sha)
    api = ["gh", "api", "--method", "GET", f"repos/{repo}/tarball/{sha}"]
    if dry:
        say("step fetch: " + " ".join(api) + " > <run-dir>/head.tar.gz ; extract into <run-dir>/extract ; "
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
        git_snapshot(run, src, sha, logs / "fetch.log")
    except BaseException:
        shutil.rmtree(run, ignore_errors=True)
        say(f"fetch failed: removed {run}")
        raise
    meta["src"] = str(src)
    mark_step(run, meta, "fetch")
    say(f"fetch exit=0 src={src}")
    return run


def cmd_install(run_arg: str | None, dry: bool) -> int:
    if dry:
        say("step install: npm ci --ignore-scripts (npm_config_cache=<run-dir>/npm-cache), only with package-lock.json")
        return 0
    run, meta = load_run_dir(run_arg)
    if "fetch" not in meta.get("steps", []):
        raise UsageError("install before fetch")
    src, logs = Path(meta["src"]), Path(meta["logs"])
    if not (src / "package-lock.json").is_file():
        say("install skipped: no package-lock.json")
        mark_step(run, meta, "install")
        return 0
    log = logs / "install.log"
    with open(log, "wb") as out:
        code = subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=src,
                              env=check_env(run), stdout=out, stderr=subprocess.STDOUT, timeout=1800).returncode
    say(f"install exit={code} log={log}")
    mark_step(run, meta, "install")
    return 0 if code == 0 else 1


def has_dep(pkg: dict, name: str) -> bool:
    return any(name in (pkg.get(k) or {}) for k in ("dependencies", "devDependencies"))


def plan_checks(src: Path) -> list[tuple[str, list[str]]]:
    """Which checks to run, first rule that matches wins:
    1. scripts/verify exists: run it, nothing else.
    2. package.json: for each of typecheck, lint, test, run `npm run --ignore-scripts <name>` when the repo defines
       that script; otherwise the plain tool when it is a dependency (tsc --noEmit with a tsconfig.json,
       eslint ., vitest run), always with `npx --no-install`.
    3. Python (pyproject.toml, setup.py or a tests/ dir with .py files): python3 -I -m unittest discover.
    """
    verify = src / "scripts" / "verify"
    if verify.is_file():
        return [("verify", ["bash", "scripts/verify"] if not os.access(verify, os.X_OK) else ["scripts/verify"])]
    pkg_path = src / "package.json"
    if pkg_path.is_file():
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        scripts = pkg.get("scripts") or {}
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
        return checks
    tests = src / "tests"
    if (src / "pyproject.toml").is_file() or (src / "setup.py").is_file() or any(tests.glob("*.py")):
        args = ["-s", "tests"] if tests.is_dir() else []
        return [("unittest", ["python3", "-I", "-m", "unittest", "discover", *args])]
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
                code = subprocess.run(argv, cwd=src, env=env, stdout=out, stderr=subprocess.STDOUT,
                                      timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                code = 124
                out.write(f"\ntimeout after {timeout}s\n".encode())
            except FileNotFoundError as exc:
                code = 127
                out.write(f"\n{exc}\n".encode())
        say(f"check {name} exit={code} log={log}")
        worst = worst or (1 if code else 0)
    mark_step(run, meta, "check")
    return worst


def cmd_clean(run_arg: str | None, dry: bool) -> int:
    if dry:
        say("step clean: delete <run-dir>; the log dir stays")
        return 0
    run, meta = load_run_dir(run_arg)
    shutil.rmtree(run)
    say(f"clean: removed {run}; logs kept in {meta['logs']}")
    return 0


def cmd_run(repo: str, sha: str, dry: bool, timeout: int) -> int:
    if dry:
        cmd_fetch(repo, sha, True)
        cmd_install(None, True)
        cmd_check(None, True, timeout)
        cmd_clean(None, True)
        return 0
    run = None
    try:
        run = cmd_fetch(repo, sha, False)
        code = cmd_install(str(run), False)
        if code:
            return code
        return cmd_check(str(run), False, timeout)
    finally:
        if run is not None and run.exists():
            cmd_clean(str(run), False)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pr_head_review.py", description=__doc__.split("\n")[0])
    p.add_argument("--dry-run", action="store_true", help="print the steps, run nothing")
    p.add_argument("--timeout", type=int, default=900, help="seconds per check (default 900)")
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
