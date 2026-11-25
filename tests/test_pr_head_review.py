"""pr-head-review script: argument validation and step order, offline (stub gh and npm on PATH)."""

import io, json, os, re, subprocess, sys, tarfile, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/pr-head-review/scripts/pr_head_review.py"
SHA = "41567f521dfa0e5f2b1791095cd062bead1061db"  # a public cursor-kit merge commit
OTHER_SHA = "6251c03" + "0" * 33


def make_tarball(path, files, sha=SHA):
    with tarfile.open(path, "w:gz", format=tarfile.PAX_FORMAT, pax_headers={"comment": sha}) as tf:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(f"o-r-{sha[:7]}/{name}")
            info.size = len(data)
            info.mode = 0o755 if name == "scripts/verify" else 0o644
            tf.addfile(info, io.BytesIO(data))


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.tmpdir = self.tmp / "t"
        self.tmpdir.mkdir()
        self.calls = self.tmp / "calls.log"
        self.tarball = self.tmp / "head.tar.gz"
        # Stubs log their argv (and whether a token leaked) to one file, so the test sees the real call order.
        stub = "#!/bin/sh\necho \"%s $* token=${GH_TOKEN:-none} cache=${npm_config_cache:-none}\" >> " + str(self.calls) + "\n"
        (self.bin / "gh").write_text(stub % "gh" + f"cat {self.tarball}\n")
        (self.bin / "npm").write_text(stub % "npm" + "exit ${NPM_EXIT:-0}\n")
        for f in ("gh", "npm"):
            (self.bin / f).chmod(0o755)

    def run_script(self, *args):
        env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}", "TMPDIR": str(self.tmpdir),
               "GH_TOKEN": "fake-token-for-test"}
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, env=env)

    def calls_list(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def leftover_run_dirs(self):
        return [p for p in self.tmpdir.iterdir() if p.name.startswith("pr-head-review-") and "logs-" not in p.name]

    def test_bad_arguments_exit_2_and_call_nothing(self):
        bad = [
            ["run", "owner", SHA], ["run", "-x/repo", SHA], ["run", "o/..", SHA], ["run", "o/.hidden", SHA],
            ["run", "o/r;rm", SHA], ["run", "o/r/x", SHA], ["run", "o/r", SHA[:39]], ["run", "o/r", SHA.upper()],
            ["run", "o/r", SHA + "\n"], ["run", "o/r", "HEAD"], ["fetch", "o/r", "g" * 40],
            ["check", str(self.tmp)], ["clean", "/"], ["install", str(self.tmpdir / "pr-head-review-nope")],
            ["nosuch"], [],
        ]
        for args in bad:
            r = self.run_script(*args)
            self.assertEqual(r.returncode, 2, (args, r.stdout, r.stderr))
        self.assertEqual(self.calls_list(), [])

    def test_dry_run_prints_steps_in_order(self):
        r = self.run_script("--dry-run", "run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stderr)
        steps = re.findall(r"^step (\w+):", r.stdout, re.M)
        self.assertEqual(steps, ["fetch", "install", "check", "clean"])
        self.assertIn(f"gh api --method GET repos/o/r/tarball/{SHA}", r.stdout)
        self.assertEqual(self.calls_list(), [])

    def test_run_node_repo_order_env_logs_and_cleanup(self):
        pkg = {"scripts": {"lint": "eslint .", "test": "vitest run"}, "devDependencies": {"typescript": "5"}}
        make_tarball(self.tarball, {"package.json": json.dumps(pkg), "package-lock.json": "{}"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        calls = self.calls_list()
        self.assertEqual([c.split(" token=")[0] for c in calls], [
            f"gh api --method GET repos/o/r/tarball/{SHA}",
            "npm ci --ignore-scripts --no-audit --no-fund",
            "npm run --ignore-scripts lint",
            "npm run --ignore-scripts test",
        ])
        # gh keeps the caller's auth; the untrusted steps never see the token and use a cache inside $TMPDIR.
        self.assertIn("token=fake-token-for-test", calls[0])
        for c in calls[1:]:
            self.assertIn("token=none", c)
            cache = c.split("cache=")[1]
            self.assertTrue(cache.startswith(str(self.tmpdir)), cache)
            self.assertNotIn(".npm", cache)
        self.assertEqual(self.leftover_run_dirs(), [])
        logs = re.findall(r"log=(\S+)", r.stdout)
        self.assertEqual([Path(p).name for p in logs], ["install.log", "check-lint.log", "check-test.log"])
        for p in logs:
            self.assertTrue(Path(p).is_file(), p)

    def test_separate_commands_fetch_check_clean(self):
        verify = "#!/bin/sh\necho verify-ran\ngit log -1 --format=%s\nexit 4\n"
        make_tarball(self.tarball, {"scripts/verify": verify, "package.json": "{}"})
        r = self.run_script("fetch", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stderr)
        run_dir = re.search(r"^run dir: (.+)$", r.stdout, re.M).group(1)
        r = self.run_script("install", run_dir)
        self.assertIn("install skipped: no package-lock.json", r.stdout)
        r = self.run_script("check", run_dir)
        self.assertEqual(r.returncode, 1)
        line = re.search(r"^check verify exit=4 log=(\S+)$", r.stdout, re.M)
        self.assertTrue(line, r.stdout)
        log_text = Path(line.group(1)).read_text()
        self.assertIn("verify-ran", log_text)
        self.assertIn(f"head {SHA}", log_text)  # the local git snapshot exists for checks that call git
        r = self.run_script("clean", run_dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(Path(run_dir).exists())
        self.assertTrue(Path(line.group(1)).is_file())

    def test_tampered_meta_is_refused(self):
        make_tarball(self.tarball, {"package.json": "{}"})
        r = self.run_script("fetch", "o/r", SHA)
        run_dir = Path(re.search(r"^run dir: (.+)$", r.stdout, re.M).group(1))
        meta_path = run_dir / "meta.json"
        good = json.loads(meta_path.read_text())
        for key, value in (("src", str(self.tmp)), ("logs", str(self.tmp))):
            meta_path.write_text(json.dumps({**good, key: value}))
            r = self.run_script("check", str(run_dir))
            self.assertEqual(r.returncode, 2, (key, r.stdout, r.stderr))
        meta_path.write_text(json.dumps(good))
        self.assertEqual(self.run_script("clean", str(run_dir)).returncode, 0)

    def test_sha_mismatch_fails_and_cleans(self):
        make_tarball(self.tarball, {"package.json": "{}"}, sha=OTHER_SHA)
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not match", r.stderr)
        self.assertEqual(self.leftover_run_dirs(), [])
        self.assertFalse(any("npm" in c for c in self.calls_list()))

    def test_failed_install_stops_before_checks(self):
        make_tarball(self.tarball, {"package.json": '{"scripts": {"test": "x"}}', "package-lock.json": "{}"})
        env_exit = self.bin / "npm"
        env_exit.write_text(env_exit.read_text().replace("${NPM_EXIT:-0}", "7"))
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 1)
        self.assertIn("install exit=7", r.stdout)
        self.assertFalse(any("npm run" in c for c in self.calls_list()))
        self.assertEqual(self.leftover_run_dirs(), [])

    def test_python_repo_runs_isolated_unittest(self):
        test = "import unittest\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
        make_tarball(self.tarball, {"pyproject.toml": "", "tests/test_a.py": test})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = re.search(r"^check unittest exit=0 log=(\S+)$", r.stdout, re.M)
        self.assertTrue(log, r.stdout)
        text = Path(log.group(1)).read_text()
        self.assertIn("python3 -I -m unittest discover -s tests", text)
        self.assertIn("Ran 1 test", text)

    def test_no_checks_exit_3(self):
        make_tarball(self.tarball, {"README.md": "x"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertEqual(self.leftover_run_dirs(), [])


if __name__ == "__main__":
    unittest.main()
