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
