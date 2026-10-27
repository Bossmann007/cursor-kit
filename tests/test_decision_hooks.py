import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "hooks" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


rec = load("recommend_needs_source", "recommend-needs-source.py")
bak = load("backup_before_edit", "backup-before-edit.py")


def transcript(*entries):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    for e in entries:
        f.write(json.dumps(e) + "\n")
    f.close()
    return Path(f.name)


def say(role, text):
    return {"type": role, "message": {"content": [{"type": "text", "text": text}]}}


class Recommend(unittest.TestCase):
    def test_recommendation_without_source_blocks(self):
        self.assertIn("additionalContext", rec.verdict("Recomendo usar Full em todos os bots.")["hookSpecificOutput"])

    def test_recommendation_with_url_or_file_line_passes(self):
        self.assertEqual(rec.verdict("Recomendo Ask first (https://example.test/docs)."), {})
        self.assertEqual(rec.verdict("Recomendo manter: claude-client.ts:885 carrega só user."), {})

    def test_not_verified_passes(self):
        self.assertEqual(rec.verdict("Recomendo isso, mas não verifiquei a licença."), {})

    def test_no_recommendation_passes(self):
        self.assertEqual(rec.verdict("Pronto, os testes passaram."), {})

    def test_reads_only_the_last_turn(self):
        t = transcript(say("assistant", "Recomendo X."), say("user", "ok"), say("assistant", "Feito."))
        self.assertEqual(rec.last_assistant_text(t), "Feito.")

    def test_tool_results_do_not_reset_the_turn(self):
        tool = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "x"}]}}
        t = transcript(say("user", "go"), say("assistant", "Recomendo X."), tool, say("assistant", "E Y."))
        self.assertIn("Recomendo X.", rec.last_assistant_text(t))


    def test_main_uses_last_assistant_message(self):
        import io, contextlib, sys
        sys.stdin = io.StringIO(json.dumps({"last_assistant_message": "Recomendo X.", "stop_hook_active": False}))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rec.main()
        sys.stdin = sys.__stdin__
        self.assertIn("additionalContext", out.getvalue())


class Backup(unittest.TestCase):
    def test_protected_names(self):
        self.assertTrue(bak.protected(Path("/x/bots/dev/AGENTS.md")))
        self.assertTrue(bak.protected(Path("/x/.claude/settings.local.json")))
        self.assertTrue(bak.protected(Path.home() / ".claude" / "skills" / "emode" / "SKILL.md"))
        self.assertFalse(bak.protected(Path.home() / ".claude" / "projects" / "a.jsonl"))
        self.assertFalse(bak.protected(Path("/x/src/app.py")))

    def test_backup_copies_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "AGENTS.md"
            src.write_text("v1")
            bak.BACKUPS = Path(d) / "backups"
            dest = bak.backup(src)
            self.assertEqual(dest.read_text(), "v1")


if __name__ == "__main__":
    unittest.main()
