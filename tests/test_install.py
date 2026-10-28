import os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_install_scaffolds_claude_state(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as home:
            (Path(home) / "Projects").mkdir()
            os.symlink(ROOT, Path(home) / "Projects" / "cursor-kit")
            r = subprocess.run(["bash", str(ROOT / "install.sh"), d], env={**os.environ, "HOME": home}, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(d) / ".claude/state/checkpoint.json").exists())
            self.assertFalse((Path(d) / ".cursor/state").exists())
            self.assertIn(".claude/state/checkpoint.json", (Path(d) / ".gitignore").read_text())

    def test_mcp_template_is_pinned(self):
        t = (ROOT / "mcp.json.template").read_text()
        self.assertNotIn("@latest", t)


if __name__ == "__main__":
    unittest.main()
