"""claude/skill-overrides.json and scripts/apply-skill-curation.py."""

from __future__ import annotations

import importlib.util
import json
import re
import stat
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "claude/skill-overrides.json").read_text())
KIT = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
WORKFLOW = ["emode", "senior-check", "performance", "improve"]

_spec = importlib.util.spec_from_file_location("apply_skill_curation", ROOT / "scripts/apply-skill-curation.py")
curation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(curation)


def referenced(text: str) -> set[str]:
    """Skill names a SKILL.md tells the agent to use: `x` (kit skill or plugin suffix) and pstack `x`."""
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


class SkillOverridesTests(unittest.TestCase):
    def test_no_kit_skill_is_off(self) -> None:
        self.assertEqual(sorted(KIT & set(CFG["off"])), [])

    def test_no_skill_named_by_workflow_skills_is_off(self) -> None:
        for s in WORKFLOW:
            with self.subTest(skill=s):
                refs = referenced((ROOT / "skills" / s / "SKILL.md").read_text())
                self.assertEqual(sorted(refs & set(CFG["off"])), [])

    def test_lists_are_disjoint(self) -> None:
        self.assertEqual(sorted(set(CFG["on"]) & set(CFG["off"] + CFG["name-only"])), [])
        self.assertNotIn("senior-engineering-partner:senior-engineering-partner", CFG["off"] + CFG["on"])


class ApplyCurationTests(unittest.TestCase):
    def test_on_removes_off_sets_unknown_untouched(self) -> None:
        cfg = {"off": ["a", "b"], "on": ["c", "missing"], "name-only": ["d"]}
        settings = {"model": "x", "skillOverrides": {"a": "off", "c": "off", "keep": "off", "d": "on"}}
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp) / "settings.json"
            s.write_text(json.dumps(settings))
            n = curation.apply(s, cfg)
            got = json.loads(s.read_text())
            self.assertEqual(got["skillOverrides"], {"a": "off", "b": "off", "keep": "off", "d": "name-only"})
            self.assertEqual(got["model"], "x")
            self.assertEqual(n, (2, 1, 1))  # b and d set, c removed, a already
            backups = list(Path(tmp).glob("settings.json.bak.*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(json.loads(backups[0].read_text()), settings)
            self.assertEqual(stat.S_IMODE(backups[0].stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(s.stat().st_mode), 0o600)
            self.assertEqual(curation.apply(s, cfg), (0, 0, 3))  # idempotent, no new backup
            self.assertEqual(len(list(Path(tmp).glob("settings.json.bak.*"))), 1)

    def test_overlap_between_on_and_off_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp) / "settings.json"
            s.write_text("{}")
            with self.assertRaises(SystemExit):
                curation.apply(s, {"off": ["a"], "on": ["a"]})
            self.assertEqual(s.read_text(), "{}")


if __name__ == "__main__":
    unittest.main()
