"""pr-head-review script: argument validation and step order, offline (stub gh and npm on PATH)."""

import io, json, os, re, subprocess, sys, tarfile, tempfile, time, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/pr-head-review/scripts/pr_head_review.py"
SHA = "41567f521dfa0e5f2b1791095cd062bead1061db"  # a public cursor-kit merge commit
OTHER_SHA = "6251c03" + "0" * 33
STUB_AUTH = "stub-auth-for-test"  # stands in for GH_TOKEN; never a real value


def make_tarball(path, files, sha=SHA, tree=None):
    """The tarball plus the git tree JSON the gh stub serves next to it (default: the same file list)."""
    blobs = sorted(files) if tree is None else tree
    Path(f"{path}.tree.json").write_text(json.dumps({"truncated": False, "tree": [{"path": p, "type": "blob"} for p in blobs]}))
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
        (self.bin / "gh").write_text(stub % "gh" + f'case "$*" in *git/trees*) cat {self.tarball}.tree.json ;; *) cat {self.tarball} ;; esac\n')
        (self.bin / "npm").write_text(stub % "npm" + "exit ${NPM_EXIT:-0}\n")
        for f in ("gh", "npm"):
            (self.bin / f).chmod(0o755)

    def run_script(self, *args):
        # npm_config_cache is set on purpose: the stubs log it, and a reviewer running this suite through the
        # skill has one whose path contains "npm"; call matching must use the command name, not a substring.
        env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}", "TMPDIR": str(self.tmpdir),
               "GH_TOKEN": STUB_AUTH, "npm_config_cache": str(self.tmp / "outer-npm-cache")}
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, env=env)

    def calls_list(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def commands(self, name):
        """Stub calls of one command, matched by the command name (first word), never by substring."""
        return [c for c in self.calls_list() if c.split()[0] == name]

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
            f"gh api --method GET repos/o/r/git/trees/{SHA}?recursive=1",
            "npm ci --ignore-scripts --no-audit --no-fund",
            "npm run --ignore-scripts lint",
            "npm run --ignore-scripts test",
        ])
        # gh keeps the caller's auth; the untrusted steps never see the token and use a cache inside $TMPDIR.
        self.assertIn(f"token={STUB_AUTH}", calls[0])
        self.assertIn("tree check: extracted files match", r.stdout)
        for c in calls[2:]:
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

    def test_clean_works_after_check_deletes_meta(self):
        make_tarball(self.tarball, {"scripts/verify": "#!/bin/sh\nrm -f ../../meta.json\n"})
        r = self.run_script("fetch", "o/r", SHA)
        run_dir = re.search(r"^run dir: (.+)$", r.stdout, re.M).group(1)
        self.assertEqual(self.run_script("check", run_dir).returncode, 0)
        # check rewrites meta.json when it ends; delete it as a still-running child of the PR code could.
        (Path(run_dir) / "meta.json").unlink()
        self.assertEqual(self.run_script("check", run_dir).returncode, 2)
        r = self.run_script("clean", run_dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(Path(run_dir).exists())
        # Still only inside the run root: a log dir or anything outside $TMPDIR is refused.
        for bad in (str(self.tmp), str(self.tmpdir / "pr-head-review-logs-x")):
            self.assertEqual(self.run_script("clean", bad).returncode, 2, bad)

    def test_install_refuses_npmrc_and_non_registry_deps(self):
        pkg = '{"scripts": {"test": "x"}}'
        reg = {"packages": {"": {}, "node_modules/a": {"resolved": "https://registry.npmjs.org/a/-/a-1.tgz"}}}
        git = {"packages": {"node_modules/b": {"resolved": "git+ssh://git@github.com/x/b.git#abc"}}}
        cases = [
            ({"package.json": pkg, "package-lock.json": json.dumps(reg), ".npmrc": "git=./evil.sh\n"}, ".npmrc present"),
            ({"package.json": pkg, "package-lock.json": json.dumps(git)}, "resolves to git+ssh"),
            ({"package.json": pkg, "package-lock.json": json.dumps({"dependencies": {"c": {"version": "github:x/c"}}})},
             "version github:x/c"),
        ]
        for files, reason in cases:
            make_tarball(self.tarball, files)
            r = self.run_script("run", "o/r", SHA)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("install refused", r.stdout)
            self.assertIn(reason, r.stdout)
            self.assertEqual(self.leftover_run_dirs(), [])
        self.assertEqual(self.commands("npm"), [])
        make_tarball(self.tarball, {"package.json": pkg, "package-lock.json": json.dumps(reg)})
        self.assertEqual(self.run_script("run", "o/r", SHA).returncode, 0)

    def test_tree_mismatch_fails_closed(self):
        make_tarball(self.tarball, {"package.json": "{}"}, tree=["package.json", "tests/hidden_by_export_ignore.py"])
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("tested files differ from the head", r.stderr)
        self.assertIn("tests/hidden_by_export_ignore.py", r.stderr)
        self.assertEqual(self.leftover_run_dirs(), [])

    def test_export_subst_fails_but_comment_does_not(self):
        make_tarball(self.tarball, {"package.json": "{}", ".gitattributes": "VERSION export-subst\n", "VERSION": "$Format:%H$"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("export-subst", r.stderr)
        make_tarball(self.tarball, {"scripts/verify": "#!/bin/sh\n", ".gitattributes": "# no export-subst here\n*.sh -export-subst\n"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_tree_unreadable_or_truncated_fails_closed(self):
        for tree_text in ('{"truncated": true, "tree": []}', "not json"):
            make_tarball(self.tarball, {"package.json": "{}"})
            Path(f"{self.tarball}.tree.json").write_text(tree_text)
            r = self.run_script("run", "o/r", SHA)
            self.assertEqual(r.returncode, 1, (tree_text, r.stdout, r.stderr))
            self.assertEqual(self.leftover_run_dirs(), [])

    def test_deeply_nested_lockfile_is_refused_cleanly(self):
        make_tarball(self.tarball, {"package.json": "{}", "package-lock.json": "[" * 100000})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 1, r.stderr[-300:])
        self.assertIn("install refused", r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_install_guard_allowlist_cases(self):
        reg = "https://registry.npmjs.org/b/-/b-1.0.0.tgz"
        cases = {
            "github spec, lockfile without resolved": (
                {"dependencies": {"b": "github:x/b"}}, {"packages": {"node_modules/b": {"version": "1.0.0"}}}, "package.json dependencies.b"),
            "registry entry, no resolved": (
                {}, {"packages": {"node_modules/b": {"version": "1.0.0"}}}, "has no resolved"),
            "v1 nested git": (
                {}, {"dependencies": {"a": {"version": "1.0.0", "resolved": reg,
                                             "dependencies": {"b": {"version": "git+ssh://git@github.com/x/b.git#abc"}}}}}, "a>b version git+ssh"),
            "gitlab shorthand": ({}, {"dependencies": {"c": {"version": "gitlab:x/c"}}}, "version gitlab:x/c"),
            "same key in packages and dependencies": (
                {}, {"packages": {"node_modules/b": {"resolved": "git+ssh://git@github.com/x/b.git"}},
                     "dependencies": {"node_modules/b": {"version": "1.0.0", "resolved": reg}}}, "resolves to git+ssh"),
            "link outside the tree": ({}, {"packages": {"node_modules/l": {"link": True, "resolved": "../outside"}}}, "links to ../outside"),
            "malformed lockfile": ({}, {"packages": [1]}, "unreadable"),
            "top-level inBundle git": (
                {}, {"packages": {"node_modules/b": {"inBundle": True, "version": "1.0.0",
                                                     "resolved": "git+ssh://git@github.com/x/b.git"}}}, "resolves to git+ssh"),
            "link with .. in the middle": (
                {}, {"packages": {"node_modules/l": {"link": True, "resolved": "packages/../../outside"}}}, "links to packages/../../outside"),
            "file spec as a dot path": ({"dependencies": {"b": ".."}}, {"packages": {}}, "package.json dependencies.b"),
            "file spec as a tarball name": ({"dependencies": {"b": "vendor.TGZ"}}, {"packages": {}}, "package.json dependencies.b"),
            "nested inBundle git": (
                {}, {"packages": {"node_modules/a": {"version": "1.0.0", "resolved": reg},
                                  "node_modules/a/node_modules/b": {"inBundle": True, "version": "1.0.0",
                                                                    "resolved": "git+ssh://attacker/b.git"}}}, "resolves to git+ssh"),
            "legacy dependencies next to clean packages (npm 6)": (
                {}, {"packages": {"node_modules/b": {"version": "1.0.0", "resolved": reg}},
                     "dependencies": {"evil": {"version": "1.0.0", "resolved": "git+https://attacker/x.git"}}}, "dependencies.evil resolves"),
            "git dep nested below a workspace entry": (
                {}, {"packages": {"node_modules/w": {"link": True, "resolved": "packages/w"}},
                     "dependencies": {"w": {"version": "file:packages/w", "dependencies": {
                         "evil": {"version": "1.0.0", "resolved": "git+ssh://attacker/x.git"}}}}}, "w>evil resolves"),
            "tar-gz lookalike spec": ({"dependencies": {"b": "vendor.tar-gz"}}, {"packages": {}}, "package.json dependencies.b"),
            "legacy file: without a link": (
                {}, {"packages": {}, "dependencies": {"w": {"version": "file:packages/w"}}}, "dependencies.w version file:"),
        }
        for label, (pkg, lock, reason) in cases.items():
            make_tarball(self.tarball, {"package.json": json.dumps(pkg), "package-lock.json": json.dumps(lock)})
            r = self.run_script("run", "o/r", SHA)
            self.assertEqual(r.returncode, 1, (label, r.stdout, r.stderr))
            self.assertIn("install refused", r.stdout, label)
            self.assertIn(reason, r.stdout, label)
            self.assertNotIn("Traceback", r.stderr, label)
        make_tarball(self.tarball, {"package.json": "{}", "package-lock.json": '{"packages": {}}', "npm-shrinkwrap.json": "{}"})
        r = self.run_script("run", "o/r", SHA)
        self.assertIn("npm-shrinkwrap.json present", r.stdout)
        self.assertEqual(self.commands("npm"), [])
        ok_pkg = {"dependencies": {"b": "^1.0.0", "c": "npm:@s/c@2", "d": "latest"}}
        # lockfileVersion 2 workspace: the legacy dependencies section has file: versions that npm ci ignores.
        ok_lock = {"lockfileVersion": 2,
                   "packages": {"": {}, "packages/w": {"version": "0.1.0"}, "node_modules/w": {"link": True, "resolved": "packages/w"},
                                "node_modules/b": {"version": "1.0.0", "resolved": reg},
                                "node_modules/b/node_modules/inner": {"version": "1.0.0", "inBundle": True}},
                   "dependencies": {"w": {"version": "file:packages/w"}}}
        make_tarball(self.tarball, {"package.json": json.dumps(ok_pkg), "package-lock.json": json.dumps(ok_lock)})
        r = self.run_script("run", "o/r", SHA)
        self.assertNotIn("install refused", r.stdout, r.stdout)

    def test_sha_mismatch_fails_and_cleans(self):
        make_tarball(self.tarball, {"package.json": "{}"}, sha=OTHER_SHA)
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not match", r.stderr)
        self.assertEqual(self.leftover_run_dirs(), [])
        self.assertEqual(self.commands("gh"), [self.calls_list()[0]])
        self.assertEqual(self.commands("npm"), [])

    def test_failed_install_stops_before_checks(self):
        make_tarball(self.tarball, {"package.json": '{"scripts": {"test": "x"}}', "package-lock.json": "{}"})
        env_exit = self.bin / "npm"
        env_exit.write_text(env_exit.read_text().replace("${NPM_EXIT:-0}", "7"))
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 1)
        self.assertIn("install exit=7", r.stdout)
        self.assertEqual([c.split()[1] for c in self.commands("npm")], ["ci"])
        self.assertEqual(self.leftover_run_dirs(), [])

    def test_python_repo_runs_isolated_unittest(self):
        test = "import unittest\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
        make_tarball(self.tarball, {"pyproject.toml": "", "tests/test_a.py": test})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = re.search(r"^check unittest exit=0 log=(\S+)$", r.stdout, re.M)
        self.assertTrue(log, r.stdout)
        text = Path(log.group(1)).read_text()
        self.assertIn(f"{sys.executable} -I -m unittest discover -s tests", text)
        self.assertIn("Ran 1 test", text)

    def test_python_package_tests_import_from_root(self):
        test = "import unittest, mypkg\nclass A(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(mypkg.X, 1)\n"
        make_tarball(self.tarball, {"mypkg/__init__.py": "X = 1\n", "tests/__init__.py": "", "tests/test_a.py": test})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_pytest_style_tests_are_not_a_pass(self):
        make_tarball(self.tarball, {"pyproject.toml": "", "tests/test_b.py": "def test_x():\n    pass\n"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("ran no tests", r.stdout)

    def test_tooling_only_package_json_falls_through_to_python(self):
        test = "import unittest\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
        make_tarball(self.tarball, {"package.json": '{"devDependencies": {"prettier": "3"}}', "tests/test_a.py": test})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("check unittest exit=0", r.stdout)

    def test_bad_package_json_is_a_clean_error(self):
        for text in ('{"scripts": {"test": "x"},}', "[]"):
            make_tarball(self.tarball, {"package.json": text})
            r = self.run_script("run", "o/r", SHA)
            self.assertEqual(r.returncode, 1, r.stderr)
            self.assertIn("package.json is not", r.stderr)
            self.assertNotIn("Traceback", r.stderr)
            self.assertEqual(self.leftover_run_dirs(), [])

    def test_bad_timeout_is_usage_error(self):
        for value in ("0", "-5", "x"):
            self.assertEqual(self.run_script("--timeout", value, "run", "o/r", SHA).returncode, 2, value)
        self.assertEqual(self.calls_list(), [])

    def test_snapshot_keeps_ignored_files(self):
        verify = "#!/bin/sh\ngit ls-files\n"
        make_tarball(self.tarball, {".gitignore": "*\n", "scripts/verify": verify, "data.txt": "x"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = re.search(r"log=(\S+check-verify.log)", r.stdout).group(1)
        self.assertIn("data.txt", Path(log).read_text())

    def test_run_cleans_even_when_check_corrupts_meta(self):
        # A dir where meta.json was: check cannot rewrite it afterwards, and a meta-reading clean would refuse it.
        make_tarball(self.tarball, {"scripts/verify": "#!/bin/sh\nrm ../../meta.json\nmkdir ../../meta.json\n"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("clean: removed", r.stdout)
        self.assertEqual(self.leftover_run_dirs(), [])

    def test_meta_with_wrong_types_is_usage_error(self):
        make_tarball(self.tarball, {"package.json": "{}"})
        r = self.run_script("fetch", "o/r", SHA)
        run_dir = Path(re.search(r"^run dir: (.+)$", r.stdout, re.M).group(1))
        good = json.loads((run_dir / "meta.json").read_text())
        for bad in ({"logs": 5}, {"src": 5}, {"steps": "x"}):
            (run_dir / "meta.json").write_text(json.dumps({**good, **bad}))
            r = self.run_script("check", str(run_dir))
            self.assertEqual(r.returncode, 2, (bad, r.stderr))
            self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(self.run_script("clean", str(run_dir)).returncode, 0)

    def test_background_process_is_killed_after_check(self):
        make_tarball(self.tarball, {"scripts/verify": "#!/bin/sh\nsleep 300 &\necho pid=$!\n"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = re.search(r"log=(\S+check-verify.log)", r.stdout).group(1)
        pid = int(re.search(r"pid=(\d+)", Path(log).read_text()).group(1))
        # The killed sleep may stay a zombie for a moment before launchd/init reaps it: poll briefly.
        deadline = time.monotonic() + 5
        while True:
            state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
            if not state or state.startswith("Z") or time.monotonic() > deadline:
                break
            time.sleep(0.1)
        self.assertTrue(not state or state.startswith("Z"), state)

    def test_timeout_kills_check(self):
        make_tarball(self.tarball, {"scripts/verify": "#!/bin/sh\nsleep 300\n"})
        r = self.run_script("--timeout", "1", "run", "o/r", SHA)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("check verify exit=124", r.stdout)

    def test_no_checks_exit_3(self):
        make_tarball(self.tarball, {"README.md": "x"})
        r = self.run_script("run", "o/r", SHA)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertEqual(self.leftover_run_dirs(), [])


if __name__ == "__main__":
    unittest.main()
