"""Kit Claude settings: deny rules, hook timeouts, merge behaviour, hook guard."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
import cursor_state  # noqa: E402


class ClaudeSettingsTests(unittest.TestCase):
    def test_template_hooks_have_timeouts_and_deny_rules(self) -> None:
        t = json.loads((ROOT / "claude-hooks.json.template").read_text())
        for groups in t["hooks"].values():
            for g in groups:
                for h in g["hooks"]:
                    self.assertIn("timeout", h, h["command"])
        self.assertIn("Read(~/.claude/.credentials.json)", t["permissions"]["deny"])

    def test_merge_adds_timeouts_drops_empty_matcher_and_unions_deny(self) -> None:
        existing = {
            "permissions": {"deny": ["Read(~/.ssh/**)"]},
            "hooks": {
                "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "other-tool stop"}]}],
                "SessionEnd": [{"hooks": [{"type": "command", "command": "other-tool end"}]}],
                "PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "x", "timeout": 3}]}],
            },
        }
        with tempfile.TemporaryDirectory() as d:
            ex, out = Path(d) / "s.json", Path(d) / "o.json"
            ex.write_text(json.dumps(existing))
            subprocess.run([sys.executable, str(ROOT / "scripts/merge-claude-settings.py"),
                            "--kit", str(ROOT / "claude-hooks.json.template"), "--existing", str(ex), "--out", str(out)], check=True)
            m = json.loads(out.read_text())
        other_stop = m["hooks"]["Stop"][0]
        self.assertNotIn("matcher", other_stop)
        self.assertEqual(other_stop["hooks"][0]["timeout"], 10)
        self.assertEqual(m["hooks"]["SessionEnd"][0]["hooks"][0]["timeout"], 2)
        self.assertEqual(m["hooks"]["PreToolUse"][0]["hooks"][0]["timeout"], 3)
        deny = m["permissions"]["deny"]
        self.assertEqual(deny.count("Read(~/.ssh/**)"), 1)
        self.assertIn("Read(**/.env)", deny)

    def test_should_run_needs_project_and_respects_switches(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertFalse(cursor_state.should_run("track-edits", root))
            (root / ".git").mkdir()
            self.assertTrue(cursor_state.should_run("track-edits", root))
            os.environ["CLAUDE_DISABLED_HOOKS"] = "track-edits"
            try:
                self.assertFalse(cursor_state.should_run("track-edits", root))
                self.assertTrue(cursor_state.should_run("tool-failure", root))
            finally:
                del os.environ["CLAUDE_DISABLED_HOOKS"]
            os.environ["CLAUDE_HOOKS_PROFILE"] = "minimal"
            try:
                self.assertFalse(cursor_state.should_run("tool-failure", root))
            finally:
                del os.environ["CLAUDE_HOOKS_PROFILE"]


if __name__ == "__main__":
    unittest.main()
