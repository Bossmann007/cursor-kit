import os, subprocess, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/senior-check/scripts/senior-check.sh"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def run(repo, *args):
    r = subprocess.run(["/bin/bash", str(SCRIPT), str(repo), *args], capture_output=True, text=True)
    lines = {l.split()[1]: l.split()[0] for l in r.stdout.splitlines() if l[:4] in ("PASS", "WARN", "FAIL")}
    return r.returncode, lines


def git(d, *a):
    subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True, env=ENV)


def git_repo(files, commit=False):
    d = Path(tempfile.mkdtemp())
    git(d, "init", "-q", "-b", "main")
    for name, text in files.items():
        p = d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    if commit:
        git(d, "add", "-A")
        git(d, "commit", "-qm", "init")
    return d


def with_remote(d):
    remote = Path(tempfile.mkdtemp()) / "remote.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(d), str(remote)], check=True, capture_output=True)
    git(d, "remote", "add", "origin", str(remote))
    git(d, "fetch", "-q", "origin")
    git(d, "branch", "-q", "--set-upstream-to=origin/main")
    return d


class T(unittest.TestCase):
    def test_bad_usage_exits_2(self):
        d = git_repo({"README.md": "x"}, commit=True)
        for args in (["/nonexistent"], [str(d), "--run-verfy"], [str(d), "--run-verify", "extra"]):
            r = subprocess.run(["/bin/bash", str(SCRIPT), *args], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, args)

    def test_no_manifest_needs_no_lockfile(self):
        _, lines = run(git_repo({"README.md": "x"}))
        self.assertEqual(lines["lockfile"], "PASS")

    def test_manifest_without_lockfile_fails(self):
        code, lines = run(git_repo({"package.json": '{"version": "1.0.0"}'}))
        self.assertEqual(lines["lockfile"], "FAIL")
        self.assertEqual(code, 1)

    def test_ignored_lockfile_is_not_committed(self):
        d = git_repo({"package.json": "{}", ".gitignore": "package-lock.json\n", "package-lock.json": "{}"}, commit=True)
        _, lines = run(d)
        self.assertEqual(lines["lockfile"], "FAIL")

    def test_no_remote_is_not_a_pass(self):
        _, lines = run(git_repo({"README.md": "x"}, commit=True))
        self.assertEqual(lines["pr-flow"], "WARN")
        self.assertEqual(lines["pushed"], "FAIL")

    def test_merge_commit_prs_are_prs(self):
        d = git_repo({"README.md": "x"}, commit=True)
        for i in range(5):
            (d / f"d{i}").write_text("x"); git(d, "add", "-A"); git(d, "commit", "-qm", f"direct {i}")
        for i in range(8):
            git(d, "checkout", "-qb", f"f{i}"); (d / f"f{i}").write_text("x"); git(d, "add", "-A")
            git(d, "commit", "-qm", f"feat {i}"); git(d, "checkout", "-q", "main")
            git(d, "merge", "-q", "--no-ff", f"f{i}", "-m", f"Merge pull request #{i} from f{i}")
        _, lines = run(with_remote(d))
        self.assertNotEqual(lines["pr-flow"], "FAIL")
        self.assertEqual(lines["pushed"], "PASS")

    def test_no_readme_fails(self):
        _, lines = run(git_repo({"main.py": "x"}, commit=True))
        self.assertEqual(lines["readme"], "FAIL")

    def test_pipe_in_pr_subject_is_still_a_pr(self):
        d = git_repo({"README.md": "x"}, commit=True)
        for i in range(3):  # old "|" split counted these as direct: 1 + 3 = 4 -> WARN
            (d / f"a{i}").write_text("x"); git(d, "add", "-A"); git(d, "commit", "-qm", f"fix: a | b (#{i})")
        code, lines = run(with_remote(d))
        self.assertEqual(lines["pr-flow"], "PASS")

    def test_dotnet_lockfile_counts(self):
        d = git_repo({"README.md": "x", "App.csproj": "<Project/>", "packages.lock.json": "{}"}, commit=True)
        _, lines = run(d)
        self.assertEqual(lines["lockfile"], "PASS")

    def test_subfolder_audits_the_repo_root(self):
        d = git_repo({"README.md": "x", "src/a.py": "x"}, commit=True)
        _, lines = run(d / "src")
        self.assertEqual(lines["readme"], "PASS")

    def test_git_checks_run_before_verify(self):
        d = git_repo({"README.md": "x", "scripts/verify": "#!/bin/sh\ntouch build-output.txt\n"})
        os.chmod(d / "scripts/verify", 0o755)
        git(d, "add", "-A"); git(d, "commit", "-qm", "init")
        _, lines = run(d, "--run-verify")
        self.assertEqual(lines["worktree"], "PASS")
        self.assertNotIn("on-default", lines)
        self.assertEqual(lines["verify-clean"], "WARN")


if __name__ == "__main__":
    unittest.main()
