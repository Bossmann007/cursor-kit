"""Tests for cursor_state — checkpoint, session, failure memory."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
import cursor_state  # noqa: E402


class CursorStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_track_and_merge_files(self) -> None:
        cursor_state.save_checkpoint({"task": "auth", "status": "in_progress"}, self.root)
        cursor_state.track_file("src/auth.py", self.root)
        cursor_state.track_file("src/auth.py", self.root)
        checkpoint = cursor_state.merge_session_into_checkpoint(self.root, status="completed")
        self.assertIn("src/auth.py", checkpoint["files"])
        session = cursor_state.load_session(self.root)
        self.assertEqual(session["files"], [])

    def test_append_failure(self) -> None:
        cursor_state.append_failure({"task": "x", "error": "boom"}, self.root)
        path = cursor_state.state_dir(self.root) / "failures.jsonl"
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        row = json.loads(lines[0])
        self.assertEqual(row["error"], "boom")
        self.assertIn("at", row)

    def test_append_failure_bounds_fields(self) -> None:
        cursor_state.append_failure({"error": "x" * 5000 + "real error", "command": "c" * 1000}, self.root)
        path = cursor_state.state_dir(self.root) / "failures.jsonl"
        row = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(row["error"].endswith("real error"))
        self.assertLessEqual(len(row["error"]), cursor_state.FAILURE_ERROR_CHARS + 1)
        self.assertLessEqual(len(row["command"]), cursor_state.FAILURE_COMMAND_CHARS + 1)

    def test_append_failure_keeps_last_lines(self) -> None:
        for i in range(cursor_state.FAILURE_MAX_LINES + 5):
            cursor_state.append_failure({"error": f"e{i}"}, self.root)
        path = cursor_state.state_dir(self.root) / "failures.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), cursor_state.FAILURE_MAX_LINES)
        self.assertEqual(json.loads(lines[-1])["error"], f"e{cursor_state.FAILURE_MAX_LINES + 4}")

    def test_failures_split_only_on_newline(self) -> None:
        weird = "a\u2028b\u2029c\x85d"
        cursor_state.append_failure({"error": weird}, self.root)
        for i in range(cursor_state.FAILURE_MAX_LINES):
            cursor_state.append_failure({"error": f"e{i}"}, self.root)
        cursor_state.append_failure({"error": weird}, self.root)
        path = cursor_state.state_dir(self.root) / "failures.jsonl"
        raw = path.read_text(encoding="utf-8")
        self.assertNotIn("\u2028", raw)
        rows = [json.loads(line) for line in raw.split("\n") if line]
        self.assertEqual(len(rows), cursor_state.FAILURE_MAX_LINES)
        self.assertEqual(rows[-1]["error"], weird)

    def test_concurrent_writers_keep_whole_records(self) -> None:
        import subprocess

        hooks = Path(__file__).resolve().parents[1] / "hooks"
        script = (
            "import sys; sys.path.insert(0, sys.argv[1]); import cursor_state; from pathlib import Path\n"
            "for i in range(150): cursor_state.append_failure({'error': sys.argv[3] + str(i) + 'x' * 250}, Path(sys.argv[2]))"
        )
        procs = [
            subprocess.Popen([sys.executable, "-c", script, str(hooks), str(self.root), name])
            for name in ("w1-", "w2-")
        ]
        self.assertEqual([proc.wait() for proc in procs], [0, 0])
        state = cursor_state.state_dir(self.root)
        lines = [line for line in (state / "failures.jsonl").read_text(encoding="utf-8").split("\n") if line]
        self.assertEqual(len(lines), cursor_state.FAILURE_MAX_LINES)
        for line in lines:
            self.assertRegex(json.loads(line)["error"], r"^w[12]-\d+x+$")
        self.assertEqual(sorted(p.name for p in state.iterdir() if p.name.startswith("failures.jsonl.")), ["failures.jsonl.lock"])

    def test_failures_are_redacted(self) -> None:
        cursor_state.append_failure(
            {
                "command": 'curl -H "Authorization: Bearer abc.def123456" "x?api_key=sk-123"',
                "error": "password=hunter2 ana@clinica.com.br 123.456.789-09 (41) 99876-5432 12345678901",
            },
            self.root,
        )
        raw = (cursor_state.state_dir(self.root) / "failures.jsonl").read_text(encoding="utf-8")
        for secret in ("abc.def123456", "sk-123", "hunter2", "ana@clinica", "123.456.789-09", "99876-5432", "12345678901"):
            self.assertNotIn(secret, raw)
        self.assertIn("[REDACTED]", raw)

    def test_hook_skips_bare_exit_1(self) -> None:
        import subprocess

        hook = Path(__file__).resolve().parents[1] / "hooks" / "tool-failure.py"
        (self.root / ".claude" / "state").mkdir(parents=True)
        for error in ("Exit code 1", "Exit code 2\nboom"):
            payload = {"cwd": str(self.root), "tool_name": "Bash", "error": error, "tool_input": {"command": "grep x"}}
            subprocess.run([sys.executable, str(hook)], input=json.dumps(payload), text=True, check=True, capture_output=True)
        path = cursor_state.state_dir(self.root) / "failures.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([row["error"] for row in rows], ["Exit code 2\nboom"])

    def test_checkpoint_summary(self) -> None:
        text = cursor_state.checkpoint_summary(
            {"task": "login", "status": "in_progress", "pending": ["tests"], "next_action": "run pytest"}
        )
        self.assertIn("login", text)
        self.assertIn("pytest", text)

    def test_ensure_checkpoint_creates_file(self) -> None:
        cursor_state.ensure_checkpoint_exists(self.root)
        self.assertTrue(cursor_state.checkpoint_path(self.root).is_file())


if __name__ == "__main__":
    unittest.main()
