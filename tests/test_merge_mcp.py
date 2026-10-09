import json, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "merge-mcp.py"


def run(client, f):
    return subprocess.run([sys.executable, str(SCRIPT), "--client", client, "--file", str(f)], capture_output=True, text=True)


class T(unittest.TestCase):
    def test_add_only_preserves_existing(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "mcp.json"
            f.write_text(json.dumps({"mcpServers": {"x": {"env": {"K": "v"}}, "context7": {"url": "keep"}}}))
            self.assertEqual(run("cursor", f).returncode, 0)
            m = json.loads(f.read_text())["mcpServers"]
            self.assertEqual(m["x"], {"env": {"K": "v"}})
            self.assertEqual(m["context7"], {"url": "keep"})
            self.assertIn("token-engine", m)
            self.assertEqual(f.stat().st_mode & 0o777, 0o600)
            self.assertIn("up to date", run("cursor", f).stdout)

    def test_gemini_uses_httpurl(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "settings.json"
            run("gemini", f)
            self.assertIn("httpUrl", json.loads(f.read_text())["mcpServers"]["ai-memory"])


if __name__ == "__main__":
    unittest.main()
