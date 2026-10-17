import subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_local_links_resolve(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/validate-docs.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
