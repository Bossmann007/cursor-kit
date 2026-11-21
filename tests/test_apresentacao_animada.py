import re, shutil, subprocess, unittest
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

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_render_script_parses(self):
        r = subprocess.run(["node", "--check", str(SKILL / "scripts" / "render.mjs")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
