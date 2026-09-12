"""Validate kit packaging: hooks.json and plugin manifest paths."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_plugin_json_declares_existing_components(self) -> None:
        plugin = json.loads((ROOT / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "cursor-kit")
        skills = ROOT / plugin["skills"].lstrip("./")
        rules = ROOT / plugin["rules"].lstrip("./")
        hooks = ROOT / plugin["hooks"].lstrip("./")
        self.assertTrue(skills.is_dir(), skills)
        self.assertTrue(rules.is_dir(), rules)
        self.assertTrue(hooks.is_file(), hooks)

    def test_plugin_hooks_json_shape(self) -> None:
        data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 1)
        for event in (
            "sessionStart",
            "postToolUse",
            "postToolUseFailure",
            "afterFileEdit",
            "stop",
        ):
            self.assertIn(event, data["hooks"])
            cmd = data["hooks"][event][0]["command"]
            self.assertIn("CURSOR_PLUGIN_ROOT", cmd)

    def test_hooks_template_placeholder(self) -> None:
        text = (ROOT / "hooks.json.template").read_text(encoding="utf-8")
        self.assertIn("__CURSOR_HOOKS_DIR__", text)
        data = json.loads(text.replace("__CURSOR_HOOKS_DIR__", "/tmp/hooks"))
        self.assertIn("sessionStart", data["hooks"])

    def test_required_rules_exist(self) -> None:
        names = {
            "ponytail.mdc",
            "caveman.mdc",
            "token-engine.mdc",
            "cbm-first.mdc",
            "session-continuity.mdc",
            "memory-security.mdc",
        }
        present = {p.name for p in (ROOT / "rules").glob("*.mdc")}
        self.assertTrue(names.issubset(present), present)


if __name__ == "__main__":
    unittest.main()
