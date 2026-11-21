import re, unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "apresentacao-animada"


class T(unittest.TestCase):
    def test_skill_stays_short_and_files_it_names_exist(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertLess(len(text.splitlines()), 150)
        for name in ("estilos.md", "pedido.md", "exemplo.html", "scripts/render.mjs", "scripts/ncs.py"):
            self.assertTrue((SKILL / name).exists(), name)
        desc = re.search(r"^description: (.*)$", text, re.M).group(1)
        for trigger in ("motion graphics", "vídeo para as redes", "prompt de vídeo", "storyboard"):
            self.assertIn(trigger, desc)


if __name__ == "__main__":
    unittest.main()
