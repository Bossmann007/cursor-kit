import shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_shell_scripts_parse(self):
        files = [*ROOT.glob("*.sh"), *(ROOT / "scripts").glob("*.sh")]
        self.assertTrue(files)
        for f in files:
            r = subprocess.run(["bash", "-n", str(f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{f.name}: {r.stderr}")

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_skill_node_scripts_parse(self):
        files = list((ROOT / "skills").glob("*/scripts/*.mjs"))
        self.assertTrue(files)
        for f in files:
            r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{f.name}: {r.stderr}")


if __name__ == "__main__":
    unittest.main()
