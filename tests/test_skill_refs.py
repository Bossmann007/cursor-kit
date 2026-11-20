import re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Backticked words in these skills that are not kit skills (a tool, a mode, a card field).
NOT_SKILLS = {"preview", "quick", "pip-audit"}


def kit_refs(skill):
    """Backticked bare names in a skill, minus pstack ones (another plugin): `pstack `x`` and the pstack section."""
    text = (ROOT / "skills" / skill / "SKILL.md").read_text().split("## pstack skills")[0]
    text = re.sub(r"pstack\s+`[^`]+`", "", text)
    names = set(re.findall(r"`([a-z][a-z0-9-]*)`", text))
    return names - NOT_SKILLS


class T(unittest.TestCase):
    def test_referenced_skills_exist(self):
        for skill in ("emode", "senior-check", "principles"):
            for name in kit_refs(skill):
                self.assertTrue((ROOT / "skills" / name / "SKILL.md").exists(), f"{skill} references missing skill {name}")

    def test_principles_is_wired_and_documented(self):
        self.assertIn("principles", kit_refs("emode"))
        self.assertIn("principles", kit_refs("senior-check"))
        for doc in ("README.md", "SKILLS-CURATED.md"):
            self.assertRegex((ROOT / doc).read_text(), r"`/?principles`", doc)


if __name__ == "__main__":
    unittest.main()
