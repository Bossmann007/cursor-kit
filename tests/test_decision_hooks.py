import importlib.util
import json
import sys
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


def run_main(module, payload):
    import contextlib, io, sys
    old = sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload))
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            module.main()
    finally:
        sys.stdin = old
    return out.getvalue().strip()


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


    def test_wording_false_positives_and_negatives(self):
        self.assertEqual(rec.verdict("As suggested, done."), {})
        self.assertEqual(rec.verdict("Não recomendo mexer nisso."), {})
        self.assertNotEqual(rec.verdict("Sugestão: usar X em todos."), {})
        self.assertNotEqual(rec.verdict("Recomendo X, roda em 127.0.0.1:8080."), {})

    def test_main_uses_last_assistant_message(self):
        out = run_main(rec, {"last_assistant_message": "Recomendo X.", "stop_hook_active": False})
        self.assertIn("additionalContext", out)

    def test_main_lets_the_second_stop_through(self):
        self.assertEqual(run_main(rec, {"last_assistant_message": "Recomendo X.", "stop_hook_active": True}), "{}")


class Backup(unittest.TestCase):
    def test_protected_names(self):
        self.assertTrue(bak.protected(Path("/x/bots/dev/AGENTS.md")))
        self.assertTrue(bak.protected(Path("/x/.claude/settings.local.json")))
        self.assertTrue(bak.protected(Path.home() / ".claude" / "skills" / "emode" / "SKILL.md"))
        self.assertFalse(bak.protected(Path.home() / ".claude" / "projects" / "a.jsonl"))
        self.assertFalse(bak.protected(Path("/x/src/app.py")))
        self.assertTrue(bak.protected(Path.home() / ".claude" / "projects" / "p" / "memory" / "MEMORY.md"))

    def test_backup_copies_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "AGENTS.md"
            src.write_text("v1")
            bak.BACKUPS = Path(d) / "backups"
            dest = bak.backup(src)
            self.assertEqual(dest.read_text(), "v1")


    def test_main_never_blocks_and_skips_tracked_files(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            bak.BACKUPS = Path(d) / "backups"
            self.assertEqual(run_main(bak, {"tool_input": {"file_path": str(Path(d) / "missing.md")}}), "{}")
            self.assertEqual(run_main(bak, "not a dict"), "{}")
            repo = Path(d) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            f = repo / "AGENTS.md"
            f.write_text("v1")
            subprocess.run(["git", "-C", str(repo), "add", "AGENTS.md"], check=True)
            run_main(bak, {"tool_input": {"file_path": str(f)}})
            self.assertFalse(bak.BACKUPS.exists())
            loose = Path(d) / "AGENTS.md"
            loose.write_text("v1")
            run_main(bak, {"tool_input": {"file_path": str(loose)}})
            run_main(bak, {"tool_input": {"file_path": str(loose)}})
            self.assertEqual(len(list(bak.BACKUPS.rglob("*AGENTS.md.*"))), 2)


class Merge(unittest.TestCase):
    def test_every_template_hook_is_kit_owned_and_merge_is_idempotent(self):
        import re, subprocess
        tpl = (ROOT / "claude-hooks.json.template").read_text()
        kit_src = (ROOT / "scripts" / "merge-claude-settings.py").read_text()
        for name in set(re.findall(r"([\w-]+\.py)", tpl)):
            self.assertIn(f'"{name}"', kit_src, f"{name} missing from KIT in merge-claude-settings.py")
        with tempfile.TemporaryDirectory() as d:
            kit = Path(d) / "kit.json"
            kit.write_text(tpl.replace("__CLAUDE_HOOKS_DIR__", "/h").replace("__TE_PY__", "python3"))
            cur = Path(d) / "s.json"
            cur.write_text("{}")
            counts = []
            for _ in range(3):
                subprocess.run([sys.executable, str(ROOT / "scripts" / "merge-claude-settings.py"), "--kit", str(kit),
                                "--existing", str(cur), "--out", str(cur)], check=True)
                hooks = json.loads(cur.read_text())["hooks"]
                counts.append({k: len(v) for k, v in hooks.items()})
            self.assertEqual(counts[0], counts[2])


if __name__ == "__main__":
    unittest.main()
