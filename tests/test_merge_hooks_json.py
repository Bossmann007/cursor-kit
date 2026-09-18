"""Tests for merge-safe hooks.json companion preservation."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MERGE_PATH = ROOT / "scripts" / "merge-hooks-json.py"


def _load_merge():
    spec = importlib.util.spec_from_file_location("merge_hooks_json", MERGE_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class MergeHooksJsonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merge = _load_merge()

    def test_fresh_install_writes_kit(self):
        kit = {
            "version": 1,
            "hooks": {
                "sessionStart": [{"command": "python3 /tmp/hooks/token-engine-session.py"}],
            },
        }
        out = self.merge.merge_hooks(None, kit)
        self.assertEqual(out, kit)

    def test_preserves_ai_memory_and_rtk(self):
        kit = {
            "version": 1,
            "hooks": {
                "sessionStart": [
                    {"command": "python3 /new/hooks/token-engine-session.py"}
                ],
                "stop": [{"command": "python3 /new/hooks/checkpoint-stop.py"}],
            },
        }
        existing = {
            "version": 1,
            "hooks": {
                "sessionStart": [
                    {"command": "python3 /old/hooks/token-engine-session.py"},
                    {
                        "command": "/Applications/ai-memory/ai-memory hook --event sessionStart"
                    },
                ],
                "stop": [{"command": "python3 /old/hooks/checkpoint-stop.py"}],
                "preToolUse": [{"command": "rtk hook cursor", "matcher": "Shell"}],
            },
        }
        out = self.merge.merge_hooks(existing, kit)
        session = out["hooks"]["sessionStart"]
        self.assertEqual(session[0]["command"], "python3 /new/hooks/token-engine-session.py")
        self.assertTrue(any("ai-memory" in e.get("command", "") for e in session))
        self.assertEqual(out["hooks"]["preToolUse"][0]["command"], "rtk hook cursor")
        self.assertEqual(out["hooks"]["stop"][0]["command"], "python3 /new/hooks/checkpoint-stop.py")

    def test_cli_roundtrip(self):
        kit = {
            "version": 1,
            "hooks": {
                "afterFileEdit": [
                    {"command": "python3 /h/track-edits.py"}
                ]
            },
        }
        existing = {
            "version": 1,
            "hooks": {
                "afterFileEdit": [
                    {"command": "python3 /old/track-edits.py"},
                    {"command": "ai-memory hook --event afterFileEdit"},
                ]
            },
        }
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            kit_path = td_path / "kit.json"
            existing_path = td_path / "existing.json"
            out_path = td_path / "out.json"
            kit_path.write_text(json.dumps(kit), encoding="utf-8")
            existing_path.write_text(json.dumps(existing), encoding="utf-8")
            import subprocess

            proc = subprocess.run(
                [
                    "python3",
                    str(MERGE_PATH),
                    "--kit",
                    str(kit_path),
                    "--existing",
                    str(existing_path),
                    "--out",
                    str(out_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)
            merged = json.loads(out_path.read_text(encoding="utf-8"))
            cmds = [e["command"] for e in merged["hooks"]["afterFileEdit"]]
            self.assertEqual(cmds[0], "python3 /h/track-edits.py")
            self.assertIn("ai-memory hook --event afterFileEdit", cmds)


if __name__ == "__main__":
    unittest.main()
