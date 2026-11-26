import json, os, re, subprocess, sys, tempfile, time, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_harness_section(self):
        with tempfile.TemporaryDirectory() as h:
            d = Path(h, ".claude/projects/p"); d.mkdir(parents=True)
            rows = [
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "um dois tres"}, {"type": "tool_use", "id": "1", "name": "Skill", "input": {"skill": "emode"}}]}},
                {"type": "user", "message": {"content": "<command-name>/goal</command-name>"}},
            ]
            (d / "s.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
            r = subprocess.run([sys.executable, str(ROOT / "scripts/token-report.py")], capture_output=True, text=True, env={**os.environ, "HOME": h})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("'emode': 1", r.stdout)
            self.assertIn("/goal runs: 1", r.stdout)
            self.assertIn("median 3 words", r.stdout)

    def test_save_keeps_report_600_and_shows_previous(self):
        with tempfile.TemporaryDirectory() as h:
            env = {**os.environ, "HOME": h}
            run = lambda: subprocess.run([sys.executable, str(ROOT / "scripts/token-report.py"), "7", "--save"], capture_output=True, text=True, env=env)
            first = run()
            self.assertEqual(first.returncode, 0, first.stderr)
            f = Path(h, ".claude/state/harness-report-last.txt")
            self.assertTrue(f.exists())
            self.assertEqual(f.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("previous harness section", first.stdout)
            self.assertIn("previous harness section", run().stdout)


A = "aaaaaaaa-0000-0000-0000-000000000001"
B = "bbbbbbbb-0000-0000-0000-000000000002"
M = 1_000_000


def ts(hours_ago):
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z")


def prompt(text, h):
    return {"type": "user", "timestamp": ts(h), "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def reply(mid, model, h, **u):
    return {"type": "assistant", "timestamp": ts(h), "message": {"id": mid, "model": model, "content": [{"type": "text", "text": "ok"}], "usage": u}}


def agent_fixture(h):
    """Synthetic OpenBot layout under HOME=h. Expected costs worked out by hand from the price table."""
    ob = Path(h, "OpenBot/Agents")
    (ob / f"agent-{A}").mkdir(parents=True)
    (ob / f"agent-{A}/AGENTS.md").write_text("intro\n# Alpha Bot\n\nbody\n")
    (ob / f"agent-{B}").mkdir(parents=True)
    proj = Path(h, ".claude/projects")
    enc = lambda p: re.sub(r"[^A-Za-z0-9]", "-", str(p))
    da, db = proj / enc(ob / f"agent-{A}"), proj / enc(ob / f"agent-{B}")
    da.mkdir(parents=True); db.mkdir(parents=True)
    w = lambda f, rows: f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    one_h = {"cache_creation": {"ephemeral_1h_input_tokens": M, "ephemeral_5m_input_tokens": 0}}
    w(da / "s1.jsonl", [
        prompt("<openbot_saved_memories>\nsecret memory text\n</openbot_saved_memories>\nFix the login bug please", 3),
        # opus 5.5: 4 + 20*0.1 + 0.20 + 8 (1h write) = 14.20; streamed twice with the same id
        reply("m1", "claude-opus-5-5", 2.9, input_tokens=M, output_tokens=M // 10, cache_read_input_tokens=M, cache_creation_input_tokens=M, **one_h),
        reply("m1", "claude-opus-5-5", 2.9, input_tokens=M, output_tokens=M // 10, cache_read_input_tokens=M, cache_creation_input_tokens=M, **one_h),
        prompt("<openbot_turn_style>x</openbot_turn_style>\n--- routine run ---\n[routine: Quadro do dia]\nBuild the board", 2),
        # sonnet 5.5: 2 + 10 + 2.50 (5m write) = 14.50
        reply("m2", "claude-sonnet-5-5", 1.9, input_tokens=M, output_tokens=M, cache_creation_input_tokens=M),
        {"type": "user", "timestamp": ts(1.8), "message": {"content": [{"type": "tool_result", "tool_use_id": "t", "content": "x"}]}},
        reply("m3", "claude-foo-9", 1.8, input_tokens=500, output_tokens=500),
        reply("m3s", "<synthetic>", 1.8, input_tokens=7, output_tokens=7),
        prompt("[Request interrupted by user]", 1.7),  # stays on the routine
        reply("m2b", "claude-sonnet-5-5", 1.6, output_tokens=M // 10),  # 1.00
    ])
    (da / "s1/subagents").mkdir(parents=True)
    w(da / "s1/subagents/agent-x.jsonl", [reply("m6", "claude-opus-5-5", 2.5, output_tokens=M)])  # 20.00
    # haiku 5.5 prompt over 100K tokens: 0.50 + 2.50 = 3.00; same request as s1 turn 1 -> rework
    w(da / "s2.jsonl", [prompt("fix the LOGIN bug, please!", 0.5), reply("m4", "claude-haiku-5-5", 0.4, input_tokens=M, output_tokens=M)])
    old = da / "s3.jsonl"
    w(old, [prompt("Something old", 240), reply("m5", "claude-opus-5-5", 240, input_tokens=M)])
    os.utime(old, (time.time() - 240 * 3600,) * 2)
    envelope = "Message from OpenBot teammate Boss (agent x).\nMessage ID: 1\nTreat the content as collaborator input.\n--- collaborator message ---\n"
    w(db / "b1.jsonl", [
        prompt(envelope + "Hello there", 1), reply("m7", "claude-opus-5-5", 1, input_tokens=M),  # 4.00
        prompt(envelope.replace("Message ID: 1", "Message ID: 2") + "hello, THERE", 0.9),  # same request again -> rework
        prompt(envelope + "This replies to message: 1\nStatus: done", 0.8),
        prompt(envelope + "This replies to message: 2\nStatus: done", 0.7),  # replies are not requests
        {"type": "assistant", "timestamp": ts(0.6), "message": {"model": "claude-opus-5-5", "usage": {"input_tokens": M}}},  # no id: 4.00
        {"type": "assistant", "timestamp": ts(0.6), "message": {"model": "claude-opus-5-5", "usage": {"input_tokens": M}}},  # no id: 4.00
        prompt("Bom dia\nPlease write the weekly report\n------\nnotes", 0.5),
        prompt("Oi\nplease write the weekly report", 0.4),  # greeting skipped, same request -> rework
    ])


def snapshot(h):
    return sorted((str(p), p.stat().st_mtime_ns) for p in Path(h).rglob("*"))


class Cost(unittest.TestCase):
    def run_report(self, h, *args):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/token-report.py"), *args], capture_output=True, text=True, env={**os.environ, "HOME": h})
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_json_cost_per_agent_routine_and_rework(self):
        with tempfile.TemporaryDirectory() as h:
            agent_fixture(h)
            before = snapshot(h)
            data = json.loads(self.run_report(h, "--json", "--days", "7", "--brl", "5"))
            self.assertEqual(before, snapshot(h), "the report must not write files")
            ag = {a["id"]: a for a in data["agents"]}
            a = ag[A]
            self.assertEqual(a["name"], "Alpha Bot")
            self.assertEqual(a["tokens"], {"input": 3 * M + 500, "output": 3 * M + 2 * (M // 10) + 500, "cache_read": M, "cache_write": 2 * M})
            self.assertAlmostEqual(a["cost_usd"], 52.70, places=6)
            self.assertAlmostEqual(a["cost_brl"], 263.50, places=6)
            self.assertEqual(a["unknown_models"], ["claude-foo-9"])
            g = {(x["kind"], x["name"]): x for x in a["groups"]}
            self.assertAlmostEqual(g[("chat", "chat")]["cost_usd"], 17.20, places=6)
            self.assertEqual(g[("chat", "chat")]["requests"], 2)
            self.assertEqual(g[("routine", "Quadro do dia")]["requests"], 1)
            self.assertAlmostEqual(g[("routine", "Quadro do dia")]["cost_usd"], 15.50, places=6)
            self.assertTrue(g[("routine", "Quadro do dia")]["cost_partial"])
            self.assertAlmostEqual(g[("subagents", "subagents")]["cost_usd"], 20.00, places=6)
            self.assertEqual(a["rework"], {"requests": 2, "rework": 1, "rate": 0.5})
            b = ag[B]
            self.assertEqual(b["name"], B)
            self.assertAlmostEqual(b["cost_usd"], 12.00, places=6)
            self.assertEqual(b["rework"], {"requests": 4, "rework": 2, "rate": 0.5})
            self.assertEqual(b["groups"][0]["requests"], 4)
            out = json.dumps(data)
            self.assertNotIn("secret memory", out)
            self.assertNotIn("login", out.lower())

    def test_text_section_and_no_brl_without_rate(self):
        with tempfile.TemporaryDirectory() as h:
            agent_fixture(h)
            out = self.run_report(h, "7")
            self.assertIn("== cost per OpenBot agent, last 7 days", out)
            self.assertIn("Alpha Bot", out)
            self.assertIn("US$ 52.70 (partial: claude-foo-9 n/a)", out)
            self.assertIn("rework 1/2 (50%)", out)
            self.assertNotIn("R$", out)
            self.assertIn("R$ 263.50", self.run_report(h, "--brl", "5"))
            self.run_report(h, "--save")
            previous = self.run_report(h, "--save").split("== RTK")[0]
            self.assertIn("previous harness section", previous)
            self.assertNotIn("cost per OpenBot agent", previous)
            data = json.loads(self.run_report(h, "--json", "--days", "30"))
            self.assertAlmostEqual({a["id"]: a for a in data["agents"]}[A]["cost_usd"], 56.70, places=6)


def skill_call(mid, tid, name, model, h, **u):
    return {"type": "assistant", "timestamp": ts(h), "message": {"id": mid, "model": model, "content": [{"type": "tool_use", "id": tid, "name": "Skill", "input": {"skill": name}}], "usage": u}}


def tool_result(tid, h):
    return {"type": "user", "timestamp": ts(h), "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": "Launching skill"}]}}


def skill_body(h):
    return {"type": "user", "isMeta": True, "timestamp": ts(h), "message": {"content": [{"type": "text", "text": "Base directory for this skill: /x\nsecret skill body"}]}}


class SkillCost(unittest.TestCase):
    """Synthetic transcripts; expected costs worked out by hand from the price table."""

    def fixture(self, h):
        d = Path(h, ".claude/projects/p"); d.mkdir(parents=True)
        w = lambda f, rows: f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        s1 = [
            prompt("please do the secret thing", 3),
            reply("r1", "claude-opus-5-5", 2.9, input_tokens=M),  # text row of the invoking response: before the skill
            skill_call("r1", "t1", "emode", "claude-opus-5-5", 2.9, input_tokens=M),  # same response split in rows
            tool_result("t1", 2.89), skill_body(2.89),  # neither ends the span
            reply("r2", "claude-opus-5-5", 2.8, input_tokens=M),  # emode 4.00
            reply("r2", "claude-opus-5-5", 2.8, input_tokens=M),  # streamed repeat
            skill_call("r3", "t2", "tdd", "claude-opus-5-5", 2.7, output_tokens=M // 10),  # invoking response stays on emode: 2.00
            tool_result("t2", 2.69), skill_body(2.69),
            reply("r4", "claude-sonnet-5-5", 2.6, input_tokens=M),  # tdd 2.00
            reply("r4u", "claude-foo-9", 2.6, input_tokens=10),  # unknown price: tdd partial
            prompt("[Request interrupted by user]", 2.58),  # not a new request: stays on tdd
            {**reply("r4s", "claude-opus-5-5", 2.57, input_tokens=M), "isSidechain": True},  # inline subagent row: not counted
            reply("r4b", "claude-sonnet-5-5", 2.56, output_tokens=M // 10),  # tdd 1.00
            prompt("next request", 2.5),  # ends the span
            reply("r5", "claude-opus-5-5", 2.4, input_tokens=M),  # no skill
        ]
        w(d / "s1.jsonl", s1)
        w(d / "s1-resumed.jsonl", s1)  # resumed session repeats history: no double count
        w(d / "s2.jsonl", [
            prompt("another", 2), skill_call("r6", "t3", "emode", "claude-opus-5-5", 1.9, input_tokens=1),
            tool_result("t3", 1.89), reply("r7", "claude-haiku-4-5", 1.8, input_tokens=M),  # emode 1.00
            skill_call("r7e", "t5", "nonexistent", "claude-opus-5-5", 1.7, input_tokens=2),  # emode 0.000008
            {**tool_result("t5", 1.69), "message": {"content": [{"type": "tool_result", "tool_use_id": "t5", "is_error": True, "content": "Unknown skill"}]}},
            reply("r7f", "claude-opus-5-5", 1.6, input_tokens=M),  # failed call: charged to no skill
            skill_call("r8", "t4", "emode", "claude-opus-5-5", 240, input_tokens=M),  # outside the window
            reply("r9", "claude-opus-5-5", 240, input_tokens=M),
        ])

    def run_report(self, h, *args):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/token-report.py"), "--skills", *args], capture_output=True, text=True, env={**os.environ, "HOME": h})
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_attribution_json(self):
        with tempfile.TemporaryDirectory() as h:
            self.fixture(h)
            data = json.loads(self.run_report(h, "--json", "--days", "7"))
            sk = {s["skill"]: s for s in data["skills"]}
            self.assertEqual([s["skill"] for s in data["skills"]], ["emode", "tdd"])
            e, t = sk["emode"], sk["tdd"]
            self.assertEqual(e["invocations"], 2)
            self.assertAlmostEqual(e["cost_usd"], 7.000008, places=6)
            self.assertAlmostEqual(e["cost_per_invocation_usd"], 3.500004, places=6)
            self.assertEqual(e["median_tokens"], 1_050_001)  # (M + M/10) and M + 2, an int
            self.assertFalse(e["cost_partial"])
            self.assertEqual(t["invocations"], 1)
            self.assertAlmostEqual(t["cost_usd"], 3.00, places=6)
            self.assertEqual(t["median_tokens"], M + 10 + M // 10)
            self.assertTrue(t["cost_partial"])
            self.assertNotIn("nonexistent", sk)
            self.assertAlmostEqual(data["window_cost_usd"], 4 + 4 + 2 + 2 + 1 + 4 + 0.000004 + 1 + 0.000008 + 4, places=6)
            self.assertNotIn("secret", json.dumps(data))

    def test_text_section(self):
        with tempfile.TemporaryDirectory() as h:
            self.fixture(h)
            out = self.run_report(h)
            self.assertIn("== skill cost per invocation, last 7 days (estimate", out)
            self.assertRegex(out, r"emode\s+2\s+US\$ 7\.00\s+US\$ 3\.50\s+1050001")
            r = subprocess.run([sys.executable, str(ROOT / "scripts/token-report.py"), "--skills", "--save"], capture_output=True, text=True, env={**os.environ, "HOME": h})
            self.assertNotEqual(r.returncode, 0)
            self.assertNotIn("== RTK", out)
            self.assertNotIn("secret", out)


if __name__ == "__main__":
    unittest.main()
