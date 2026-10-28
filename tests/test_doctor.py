import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("doctor", str(ROOT / "scripts" / "doctor"))
spec = importlib.util.spec_from_loader("doctor", loader)
doctor = importlib.util.module_from_spec(spec)
loader.exec_module(doctor)


class Doctor(unittest.TestCase):
    def setUp(self):
        doctor.results.clear()

    def test_broken_skill_link_fails(self):
        with tempfile.TemporaryDirectory() as d:
            skills = Path(d)
            (skills / "ok").mkdir()
            (skills / "gone").symlink_to(Path(d) / "missing")
            doctor.check_skill_links(skills)
            self.assertEqual(doctor.results[-1][0], "FAIL")
            self.assertIn("gone", doctor.results[-1][2])

    def test_missing_hook_file_and_unregistered_hook_fail(self):
        with tempfile.TemporaryDirectory() as d:
            real = Path(d) / "backup-before-edit.py"
            real.write_text("")
            s = Path(d) / "settings.json"
            s.write_text(json.dumps({"hooks": {"Stop": [{"hooks": [
                {"command": f"python3 {real}"}, {"command": f"python3 {d}/nope.py"}]}]}}))
            doctor.check_hooks(s)
            by_name = {n: st for st, n, _ in doctor.results}
            self.assertEqual(by_name["hook files"], "FAIL")
            self.assertEqual(by_name["hook backup-before-edit.py"], "PASS")
            self.assertEqual(by_name["hook recommend-needs-source.py"], "FAIL")

    def test_missing_skills_folder_fails(self):
        doctor.check_skill_links(Path("/nonexistent/skills"))
        self.assertEqual(doctor.results[-1][0], "FAIL")

    def test_hook_paths_expand_home_and_keep_spaces(self):
        s = {"hooks": {"Stop": [{"hooks": [{"command": "python3 ~/.claude/hooks/a.py"},
                                           {"command": '"/x/App Support/h.sh" --flag'},
                                           {"command": "/x/a.pyc"}]}]}}
        files = doctor.hook_files(s)
        self.assertIn(str(Path.home() / ".claude/hooks/a.py"), files)
        self.assertIn("/x/App Support/h.sh", files)
        self.assertIn("/x/a.pyc", files)
        self.assertNotIn("/x/a.py", files)

    def test_mcp_status_parsing(self):
        from unittest import mock
        out = ("token-engine: python -m x - ✔ Connected\ncodebase-memory: y - ✘ Failed to connect\n"
               "context7: https://z - ✔ Connected\n")
        with mock.patch.object(doctor.subprocess, "run", return_value=mock.Mock(stdout=out)):
            doctor.check_mcp()
        by = {n: s for s, n, _ in doctor.results}
        self.assertEqual(by["mcp token-engine"], "PASS")
        self.assertEqual(by["mcp codebase-memory"], "FAIL")
        self.assertEqual(by["mcp ai-memory"], "FAIL")  # missing from the list

    def test_agent_without_persona_warns(self):
        with tempfile.TemporaryDirectory() as d:
            agents = Path(d) / "Agents"
            (agents / "agent-1234").mkdir(parents=True)
            doctor.check_openbot(agents, Path(d) / "no-harden.py")
            self.assertEqual(doctor.results[-2][0], "WARN")
            self.assertEqual(doctor.results[-1][0], "SKIP")

    def test_real_agent_folder_passes_and_link_warns(self):
        with tempfile.TemporaryDirectory() as d:
            agents = Path(d) / "Agents"
            (agents / "agent-1234").mkdir(parents=True)
            (agents / "agent-1234" / "AGENTS.md").write_text("x")
            doctor.check_openbot(agents, Path(d) / "no-harden.py")
            self.assertEqual(doctor.results[-2][0], "PASS")
            (agents / "agent-5678").symlink_to(agents / "agent-1234")
            doctor.check_openbot(agents, Path(d) / "no-harden.py")
            self.assertEqual(doctor.results[-2][0], "WARN")


if __name__ == "__main__":
    unittest.main()
