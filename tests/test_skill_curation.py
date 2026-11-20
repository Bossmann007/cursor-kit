"""claude/skill-overrides.json and scripts/apply-skill-curation.py."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/apply-skill-curation.py"
CFG = json.loads((ROOT / "claude/skill-overrides.json").read_text())
KIT = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
WORKFLOW = ["emode", "senior-check", "performance", "improve"]


def load_curation():
    """Import the script as a module. Callers must have HOME pointed at a temp dir."""
    spec = importlib.util.spec_from_file_location("apply_skill_curation", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def referenced(text: str) -> set[str]:
    """Skill names a SKILL.md tells the agent to use: `x` (kit skill or an off name) and pstack `x`."""
    off_by_suffix = {n.split(":", 1)[-1]: n for n in CFG["off"]}
    names = set()
    for m in re.finditer(r"(pstack\s+)?`/?([a-z0-9:-]+)`", text):
        t = m.group(2)
        if m.group(1):
            names.add(f"pstack:{t}")
        elif t in KIT or ":" in t:
            names.add(t)
        elif t in off_by_suffix:
            names.add(off_by_suffix[t])
    return names


class HomeIsolated(unittest.TestCase):
    """No test may reach the real ~/.claude: HOME (and so Path.home()) is a temp dir."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        p = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        p.start()
        self.addCleanup(p.stop)


class SkillOverridesTests(HomeIsolated):
    def test_no_kit_skill_is_off(self) -> None:
        self.assertEqual(sorted(KIT & set(CFG["off"])), [])

    def test_no_skill_named_by_workflow_skills_is_off(self) -> None:
        for s in WORKFLOW:
            with self.subTest(skill=s):
                refs = referenced((ROOT / "skills" / s / "SKILL.md").read_text())
                self.assertEqual(sorted(refs & set(CFG["off"])), [])

    def test_lists_are_disjoint(self) -> None:
        self.assertEqual(sorted(set(CFG["on"]) & set(CFG["off"] + CFG["name-only"])), [])

    def test_no_plugin_keys(self) -> None:
        # skillOverrides does not apply to plugin skills (managed through /plugin).
        names = CFG["off"] + CFG["on"] + CFG["name-only"]
        self.assertEqual([n for n in names if ":" in n], [])

    def test_on_and_name_only_are_kit_skills(self) -> None:
        self.assertEqual(sorted(set(CFG["on"] + CFG["name-only"]) - KIT), [])


class ApplyCurationTests(HomeIsolated):
    def test_import_does_not_touch_settings(self) -> None:
        self.assertEqual(Path.home(), self.home)
        claude = self.home / ".claude"
        claude.mkdir()
        s = claude / "settings.json"
        s.write_text('{"skillOverrides": {}}')
        before = sorted(p.name for p in claude.iterdir())
        load_curation()
        self.assertEqual(s.read_text(), '{"skillOverrides": {}}')
        self.assertEqual(sorted(p.name for p in claude.iterdir()), before)

    def test_on_removes_off_sets_unknown_untouched(self) -> None:
        curation = load_curation()
        cfg = {"off": ["a", "b"], "on": ["c", "missing"], "name-only": ["d"]}
        settings = {"model": "x", "note": "café", "skillOverrides": {"a": "off", "c": "off", "keep": "off", "d": "on"}}
        s = self.home / "settings.json"
        s.write_text(json.dumps(settings))
        n = curation.apply(s, cfg)
        got = json.loads(s.read_text())
        self.assertEqual(got["skillOverrides"], {"a": "off", "b": "off", "keep": "off", "d": "name-only"})
        self.assertEqual(got["model"], "x")
        self.assertIn("café", s.read_text(encoding="utf-8"))  # ensure_ascii=False
        self.assertEqual(n, (2, 1, 1))  # b and d set, c removed, a already
        backups = list(self.home.glob("settings.json.bak.*"))
        self.assertEqual(len(backups), 1)
        self.assertRegex(backups[0].name, r"\.bak\.\d{20}$")  # microseconds
        self.assertEqual(json.loads(backups[0].read_text()), settings)
        self.assertEqual(stat.S_IMODE(backups[0].stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(s.stat().st_mode), 0o600)
        self.assertEqual(curation.apply(s, cfg), (0, 0, 3))  # idempotent, no new backup
        self.assertEqual(len(list(self.home.glob("settings.json.bak.*"))), 1)
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), sorted(["settings.json", backups[0].name]))

    def test_overlap_between_on_and_off_is_rejected(self) -> None:
        curation = load_curation()
        s = self.home / "settings.json"
        s.write_text("{}")
        with self.assertRaises(SystemExit):
            curation.apply(s, {"off": ["a"], "on": ["a"]})
        self.assertEqual(s.read_text(), "{}")


if __name__ == "__main__":
    unittest.main()
