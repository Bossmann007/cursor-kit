import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_harness_section(self):
        with tempfile.TemporaryDirectory() as h:
            d = Path(h, ".claude/projects/p"); d.mkdir(parents=True)
            rows = [
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "um dois tres"}, {"type": "tool_use", "id": "1", "name": "Skill", "input": {"skill": "emode"}}]}},
                {"type": "user", "message": {"content": "<command-name>/goal</command-name>"}},
            ]
            (d / "s.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
            r = subprocess.run([sys.executable, str(ROOT / "scripts/token-report.py")], capture_output=True, text=True, env={**os.environ, "HOME": h})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("'emode': 1", r.stdout)
            self.assertIn("/goal runs: 1", r.stdout)
            self.assertIn("median 3 words", r.stdout)

    def test_save_keeps_report_600_and_shows_previous(self):
        with tempfile.TemporaryDirectory() as h:
            env = {**os.environ, "HOME": h}
            run = lambda: subprocess.run([sys.executable, str(ROOT / "scripts/token-report.py"), "7", "--save"], capture_output=True, text=True, env=env)
            first = run()
            self.assertEqual(first.returncode, 0, first.stderr)
            f = Path(h, ".claude/state/harness-report-last.txt")
            self.assertTrue(f.exists())
            self.assertEqual(f.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("previous harness section", first.stdout)
            self.assertIn("previous harness section", run().stdout)


if __name__ == "__main__":
    unittest.main()
