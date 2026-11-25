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

    def test_more_wordings_and_fast_on_long_dotted_text(self):
        import time
        for s in ("I'd recommend X.", "We recommend X.", "Recomendado: X."):
            self.assertNotEqual(rec.verdict(s), {}, s)
        start = time.monotonic()
        rec.verdict("Recomendo " + "a." * 20000)
        self.assertLess(time.monotonic() - start, 1.0)

    def test_study_and_workflow_next_steps_pass(self):
        for s in ("Sugestão: revisar o capítulo 3.",
                  "Sugestão: faça os exercícios 1 a 5.",
                  "Recomendo: rode os testes de novo.",
                  "Sugiro revisar o capítulo 3.",
                  "Sugiro que você revise o capítulo 3 antes da prova.",
                  "Recomendo a leitura do capítulo 3.",
                  "Recomendo fazer os exercícios 1 a 5.",
                  "Sugestão: exercícios 1 a 5 da lista.",
                  "Recomendo estudar a matriz de transição e praticar com o simulado.",
                  "I recommend reviewing chapter 3 and practicing the problems.",
                  "O certo é rodar os testes de novo.",
                  "Sugiro rodar scripts/verify e abrir o PR.",
                  "Recomendo aguardar a review antes do merge.",
                  "I'd suggest running the tests again.",
                  "Recomendo:\n- revisar o capítulo 3\n- fazer os exercícios"):
            self.assertEqual(rec.verdict(s), {}, s)

    def test_tech_product_price_and_fact_recommendations_still_fire(self):
        for s in ("Recomendo usar Supabase.",
                  "Sugiro o plano Pro: o plano custa R$ 49 por mês.",
                  "Recomendo atualizar: a versão 2.1 corrigiu o vazamento.",
                  "Recomendo fazer deploy na Vercel.",
                  "Sugiro abrir conta na AWS.",
                  "Sugiro revisar o capítulo 3. Recomendo usar Supabase.",
                  "Sugiro estudar pelo curso X, que custa R$ 49.",
                  "I recommend Postgres 16 over MySQL.",
                  # a study or workflow verb does not cover a choice, a price or a second action in the sentence
                  "O certo é estudar Rust em vez de Go.",
                  "I recommend reading the docs: Postgres 16 is faster.",
                  "Recomendo revisar o cap 3, depois usar Supabase, que é grátis.",
                  "Recomendo revisar o contrato e assinar o plano Enterprise.",
                  "Recomendo ler o livro X por 49 reais.",
                  "Recomendo ler o livro, que custa USD 20.",
                  "Sugiro rodar o build na Vercel com Node 22.",
                  "Sugiro rodar os testes em Python 3.13, que é mais rápido.",
                  "Recomendo:\n- revisar o capítulo 3\n- usar Supabase",
                  "Recomendo revisar o código antes de migrar para Postgres 16.",
                  "Recomendo ler do cache Redis para cortar latência.",
                  "I suggest reading from the read replica.",
                  "Recomendo o estudo de caso da AWS sobre Aurora.",
                  "Sugiro revisar o cap. 3, depois migrar para o Next 15.",
                  "Recomendo revisar o capítulo 3 " + "x" * 700 + " e usar Supabase."):
            self.assertNotEqual(rec.verdict(s), {}, s)

    def test_tech_recommendations_with_a_source_pass(self):
        self.assertEqual(rec.verdict("Recomendo usar Supabase (https://supabase.com/docs)."), {})
        self.assertEqual(rec.verdict("Sugiro o plano Pro, que custa R$ 49 (https://example.test/pricing)."), {})
        self.assertEqual(rec.verdict("Recomendo atualizar: CHANGELOG.md:12 diz que a 2.1 corrigiu o vazamento."), {})

    def test_bare_claims_without_a_recommending_word_are_unchanged(self):
        # The hook keys on recommending words; a bare claim never fired and still does not.
        for s in ("O plano custa R$ 49.", "Próximo passo: revisar o capítulo 3.", "Faça os exercícios 1 a 5.",
                  "Rode os testes de novo."):
            self.assertEqual(rec.verdict(s), {}, s)

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
