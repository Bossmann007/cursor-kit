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

    def test_unlinked_agent_warns(self):
        with tempfile.TemporaryDirectory() as d:
            agents = Path(d) / "Agents"
            (agents / "agent-1234").mkdir(parents=True)
            doctor.check_openbot(agents, Path(d) / "no-harden.py")
            self.assertEqual(doctor.results[-1][0], "WARN")


if __name__ == "__main__":
    unittest.main()
