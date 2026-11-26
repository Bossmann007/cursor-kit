"""scripts/skill-lint.py: one passing and one failing fixture per check, plus the changed-skills gate."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "skill-lint.py"
spec = importlib.util.spec_from_file_location("skill_lint", SCRIPT)
skill_lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_lint)

GOOD = """---
name: good
description: >
  Does one thing. Use when the user asks for it.
---

# good

1. Run `scripts/verify`.
   Check: it exits 0 before step 2.
2. Open the PR with `gh pr create`.
   Done when: the command prints the PR URL.

## Error recovery

| Failure | Fix |
|---|---|
| `scripts/verify` exits 1 | Read the first failing test and fix it |
| `gh` says not logged in | Run `gh auth login` |
"""


def lint_text(text):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "SKILL.md"
        f.write_text(text)
        return skill_lint.lint(f)


def run(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args], capture_output=True, text=True)


class Checks(unittest.TestCase):
    def test_good_fixture_passes_every_check(self):
        self.assertEqual(lint_text(GOOD), ({}, []))

    def test_frontmatter_fails_without_description(self):
        errors, _ = lint_text(GOOD.replace("description: >\n  Does one thing. Use when the user asks for it.\n", ""))
        self.assertEqual(list(errors), ["frontmatter"])

    def test_long_description_warns_but_passes(self):
        errors, warns = lint_text(GOOD.replace("Does one thing.", "x" * 700))
        self.assertEqual(errors, {})
        self.assertIn("description is", warns[0])

    def test_length_fails_at_500_body_lines(self):
        errors, _ = lint_text(GOOD + "filler\n" * 500)
        self.assertEqual(list(errors), ["length"])

    def test_steps_fail_when_a_step_has_no_check(self):
        errors, _ = lint_text(GOOD.replace("   Done when: the command prints the PR URL.\n", ""))
        self.assertEqual(errors, {"steps": ["1/2 without a check"]})

    def test_steps_fail_when_none_are_numbered(self):
        errors, _ = lint_text(GOOD.replace("1. Run", "- Run").replace("2. Open", "- Open"))
        self.assertEqual(errors, {"steps": ["no numbered steps"]})

    def test_numbered_headings_count_as_steps(self):
        text = GOOD.replace("1. Run", "### 1. Verify\n\nRun").replace("2. Open", "### 2. Ship\n\nOpen")
        self.assertEqual(lint_text(text), ({}, []))

    def test_recovery_fails_when_the_only_fix_is_try_again(self):
        text = GOOD.split("| `scripts/verify`")[0] + "| `gh` times out | Try again. |\n"
        errors, _ = lint_text(text)
        self.assertEqual(list(errors), ["recovery"])

    def test_recovery_list_form_passes(self):
        text = GOOD.split("| Failure")[0] + "- `gh` times out → check `gh status`, then rerun with `--debug`\n"
        self.assertEqual(lint_text(text), ({}, []))

    def test_numbered_recovery_list_is_not_counted_as_steps(self):
        text = GOOD.split("| Failure")[0] + "1. `gh` not logged in → run `gh auth login`\n"
        self.assertEqual(lint_text(text), ({}, []))

    def test_heading_step_includes_its_subheadings(self):
        text = GOOD.replace("1. Run `scripts/verify`.\n   Check: it exits 0 before step 2.", "### 1. Build\n\nRun `make`.\n\n#### Verify\n\nCheck: exit 0.")
        text = text.replace("2. Open", "### 2. Ship\n\nOpen")
        self.assertEqual(lint_text(text), ({}, []))

    def test_second_table_header_is_not_a_fix(self):
        text = GOOD.split("| Failure")[0] + "| Failure | Fix |\n|---|---|\n| `gh` hangs | Retry |\n\n| Failure | Fix |\n|---|---|\n"
        errors, _ = lint_text(text)
        self.assertEqual(list(errors), ["recovery"])


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git("init", "-q", "-b", "master")
        self.write("legacy", "---\nname: legacy\ndescription: old\n---\nno steps\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "base")
        self.git("branch", "base")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
             "-c", "core.hooksPath=/dev/null", *args], check=True)

    def write(self, name, text):
        (self.root / "skills" / name).mkdir(parents=True, exist_ok=True)
        (self.root / "skills" / name / "SKILL.md").write_text(text)

    def test_unchanged_failing_skill_is_reported_not_gated(self):
        r = run(self.root, "--base", "base")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("FAIL  legacy", r.stdout)
        self.assertIn("1 skills, 0 pass, 1 fail", r.stdout)

    def test_new_failing_skill_fails_the_gate(self):
        self.write("fresh", "---\nname: fresh\ndescription: new\n---\n1. do it\n")
        r = run(self.root, "--base", "base")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("changed skills failing: fresh", r.stdout)

    def test_new_passing_skill_passes_the_gate(self):
        self.write("fresh", GOOD)
        r = run(self.root, "--base", "base")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("1 changed skill(s), none failing", r.stdout)

    def test_edited_legacy_skill_is_gated(self):
        self.write("legacy", "---\nname: legacy\ndescription: edited\n---\nno steps\n")
        self.git("commit", "-q", "-am", "edit")
        self.assertEqual(run(self.root, "--base", "base").returncode, 1)

    def test_no_git_base_skips_the_gate_loudly(self):
        r = run(self.root, "--base", "no-such-ref")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("gate SKIPPED", r.stdout)


class Repo(unittest.TestCase):
    def test_reports_every_kit_skill(self):
        r = run(ROOT, "--changed", "")
        self.assertEqual(r.returncode, 0, r.stdout)
        n = len(list((ROOT / "skills").glob("*/SKILL.md")))
        self.assertIn(f"skill-lint: {n} skills,", r.stdout)


if __name__ == "__main__":
    unittest.main()
