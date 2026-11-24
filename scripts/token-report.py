#!/usr/bin/env python3
"""Where do tokens go? RTK savings + te-filter ledger + tool-result sizes + harness usage from Claude Code transcripts.

usage: token-report.py [DAYS=7] [--days N] [--brl RATE] [--json] [--save]
--days N   window for the harness and cost sections (default 7; same as the DAYS positional)
--brl RATE USD->BRL rate to also print costs in R$ (no network lookup)
--json     print only the cost section as JSON (per agent, per routine, rework)
--save keeps the output in ~/.claude/state/harness-report-last.txt (mode 600) and prints the previous harness section first.
"""
import argparse
import collections as C
import difflib
import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

H = Path.home()
ap = argparse.ArgumentParser(add_help=True)
ap.add_argument("days_pos", nargs="?", type=int)
ap.add_argument("--days", type=int)
ap.add_argument("--brl", type=float)
ap.add_argument("--json", action="store_true")
ap.add_argument("--save", action="store_true")
OPT = ap.parse_args()
DAYS = next((d for d in (OPT.days, OPT.days_pos) if d is not None), 7)

# USD per million tokens, Claude API first-party list prices, checked 2026-11-24 at
# https://platform.claude.com/docs/en/about-claude/pricing (global inference, standard speed).
# Columns: input, output, cache read (hit), cache write 5m, cache write 1h. Unknown model -> cost "n/a", never guessed.
PRICES_AS_OF = "2026-11-24"
PRICES = {
    "claude-fable-5-2": (8, 40, 0.20, 10, 16),
    "claude-fable-5-1": (10, 50, 0.25, 12.50, 20),
    "claude-opus-5-5": (4, 20, 0.20, 5, 8),
    "claude-opus-5": (5, 25, 0.50, 6.25, 10),
    "claude-opus-4-8": (5, 25, 0.50, 6.25, 10),
    "claude-opus-4-7": (5, 25, 0.50, 6.25, 10),
    "claude-opus-4-6": (5, 25, 0.50, 6.25, 10),
    "claude-sonnet-5-5": (2, 10, 0.10, 2.50, 4),
    "claude-sonnet-5": (2, 10, 0.20, 2.50, 4),
    "claude-sonnet-4-6": (3, 15, 0.30, 3.75, 6),
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125, 0.20),
    "claude-haiku-4-5": (1, 5, 0.10, 1.25, 2),
}
# Same page: Haiku 5.5 requests whose prompt (input + cache read + cache write) is over 100,000 tokens.
PRICES_OVER_100K = {"claude-haiku-5-5": (0.50, 2.50, 0.05, 0.625, 1)}
# Same page: fast mode on Opus 5.5 is $8/$40 and the cache multipliers apply on top (2x every column).
FAST_FACTOR = {"claude-opus-5-5": 2}
US_GEO_FACTOR = 1.1  # inference_geo "us" on 4.6+ models


# --- cost per OpenBot agent, per routine, and rework (reads ~/.claude/projects only, writes nothing)
REWORK_WINDOW_H, REWORK_RATIO = 72, 0.8
SKIP_MODELS = {"<synthetic>"}
# OpenBot envelope lines around the real request (seen in agent transcripts, 2026-11)
BOILERPLATE = re.compile(r"-{3}.*-{3}|\[routine:.*|Message from OpenBot teammate .*|Continue this OpenBot conversation\.?|\[Request interrupted by user.*")


def _enc(path):
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))  # Claude Code project-folder naming


def _ts(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _request(text):
    """(routine name or None, first request line) from a prompt; wrapper blocks and the routine banner are skipped."""
    m = re.search(r"\[routine:\s*([^\]\n]*)\]", text)
    routine = m.group(1).strip()[:60] if m else None
    if "This replies to message:" in text:
        return routine, ""  # a teammate's answer, not a new request
    body = text.lstrip()
    while True:  # leading <tag>...</tag> wrapper blocks (saved memories, turn style, reminders)
        w = re.match(r"<([A-Za-z_][\w-]*)[^>]*>.*?</\1>\s*", body, re.S)
        if not w:
            break
        body = body[w.end():]
    lines = body.splitlines()
    delims = [i for i, x in enumerate(lines) if re.fullmatch(r"-{3}.*-{3}", x.strip())]
    for line in lines[delims[-1] + 1:] if delims else lines:  # OpenBot puts the request after its last --- banner ---
        line = line.strip()
        if line and not BOILERPLATE.fullmatch(line):
            return routine, line
    return routine, ""


def _norm(line):
    return " ".join(re.sub(r"[^\w]+", " ", line.lower()).split())


def _price(model, u):
    """USD for one API response, or None when the model or mode has no verified price."""
    model = re.sub(r"-\d{8}$", "", model or "")
    inp, cr, cw = u.get("input_tokens") or 0, u.get("cache_read_input_tokens") or 0, u.get("cache_creation_input_tokens") or 0
    p = PRICES_OVER_100K.get(model) if inp + cr + cw > 100_000 and model in PRICES_OVER_100K else PRICES.get(model)
    if p is None:
        return None
    factor = 1.0
    if u.get("speed") == "fast":
        if model not in FAST_FACTOR:
            return None
        factor *= FAST_FACTOR[model]
    if u.get("inference_geo") == "us":
        factor *= US_GEO_FACTOR
    split = u.get("cache_creation") or {}
    cw1h = split.get("ephemeral_1h_input_tokens") or 0
    cw5m = cw - cw1h
    usd = inp * p[0] + (u.get("output_tokens") or 0) * p[1] + cr * p[2] + cw5m * p[3] + cw1h * p[4]
    return usd * factor / 1e6


def _bucket():
    return {"tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}, "cost_usd": 0.0, "unknown": set(), "requests": 0}


def _add(b, model, u):
    t = b["tokens"]
    t["input"] += u.get("input_tokens") or 0
    t["output"] += u.get("output_tokens") or 0
    t["cache_read"] += u.get("cache_read_input_tokens") or 0
    t["cache_write"] += u.get("cache_creation_input_tokens") or 0
    usd = _price(model, u)
    if usd is None:
        b["unknown"].add(model or "?")
    else:
        b["cost_usd"] += usd


def _agent_name(aid):
    try:
        for line in (H / f"OpenBot/Agents/agent-{aid}/AGENTS.md").read_text(errors="ignore").splitlines():
            if line.startswith("#"):
                return line.lstrip("#").strip()[:60] or aid
    except OSError:
        pass
    return aid


def cost_report(days, brl=None):
    now = time.time()
    since, lookback = now - days * 86400, now - days * 86400 - REWORK_WINDOW_H * 3600
    prefix = _enc(H / "OpenBot/Agents/agent-")
    agents = {}
    for d in sorted(glob.glob(str(H / ".claude/projects" / (prefix + "*")))):
        m = re.match(re.escape(prefix) + r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", Path(d).name)
        if not m:
            continue
        ag = agents.setdefault(m.group(1), {"total": _bucket(), "groups": {}, "requests": [], "seen": set()})
        files = [(f, False) for f in glob.glob(d + "/*.jsonl")] + [(f, True) for f in glob.glob(d + "/*/subagents/*.jsonl")]
        for f, sub in files:
            if os.path.getmtime(f) < lookback:
                continue
            key = ("subagents", "subagents") if sub else ("chat", "chat")
            for line in open(f, errors="ignore"):
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                msg, t = e.get("message") or {}, _ts(e.get("timestamp"))
                if not sub and e.get("type") == "user" and not e.get("isMeta") and e.get("promptSource") != "system":
                    text = _text(msg.get("content"))
                    if not text.strip():
                        continue  # tool results continue the current request
                    routine, first = _request(text)
                    key = ("routine", routine) if routine else ("chat", "chat")
                    if t is not None and t >= lookback:
                        ag["requests"].append((t, key, _norm(first)))
                    if t is not None and t >= since:
                        ag["groups"].setdefault(key, _bucket())["requests"] += 1
                elif e.get("type") == "assistant" and msg.get("usage") and msg.get("model") not in SKIP_MODELS:
                    if t is None or t < since or msg.get("id") in ag["seen"]:
                        continue  # streamed responses repeat one id with the same usage
                    ag["seen"].add(msg.get("id"))
                    _add(ag["total"], msg.get("model"), msg["usage"])
                    _add(ag["groups"].setdefault(key, _bucket()), msg.get("model"), msg["usage"])
    out = []
    for aid, ag in agents.items():
        reqs = sorted(r for r in ag["requests"] if r[1][0] == "chat" and r[2])  # routines repeat by design
        n = rw = 0
        for i, (t, _, line) in enumerate(reqs):
            if t < since:
                continue
            n += 1
            if any(t - pt <= REWORK_WINDOW_H * 3600 and difflib.SequenceMatcher(None, line, pl).ratio() > REWORK_RATIO for pt, _, pl in reqs[:i]):
                rw += 1
        if not ag["seen"] and not n:
            continue

        def view(b):
            v = {"tokens": b["tokens"], "cost_usd": round(b["cost_usd"], 6), "cost_partial": bool(b["unknown"]), "unknown_models": sorted(b["unknown"])}
            if brl:
                v["cost_brl"] = round(b["cost_usd"] * brl, 6)
            return v

        groups = [{"kind": k[0], "name": k[1], "requests": b["requests"], **view(b)} for k, b in sorted(ag["groups"].items(), key=lambda x: -x[1]["cost_usd"])]
        out.append({"id": aid, "name": _agent_name(aid), **view(ag["total"]), "groups": groups, "rework": {"requests": n, "rework": rw, "rate": round(rw / n, 4) if n else 0.0}})
    out.sort(key=lambda a: -a["cost_usd"])
    return {"days": days, "since": datetime.fromtimestamp(since, timezone.utc).isoformat(), "prices_as_of": PRICES_AS_OF, "usd_brl": brl, "agents": out}


def _money(v):
    s = f"US$ {v['cost_usd']:.2f}"
    if "cost_brl" in v:
        s += f" / R$ {v['cost_brl']:.2f}"
    if v["cost_partial"]:
        s += f" (partial: {', '.join(v['unknown_models'])} n/a)"
    return s


def print_cost(rep):
    print(f"\n== cost per OpenBot agent, last {rep['days']} days (API list prices as of {rep['prices_as_of']}; plan billing may differ)")
    if not rep["agents"]:
        print("  no OpenBot agent sessions in the window")
    for a in rep["agents"]:
        t, r = a["tokens"], a["rework"]
        print(f"  {a['name'][:40]:40s} {_money(a)}  in={t['input']} out={t['output']} cache_r={t['cache_read']} cache_w={t['cache_write']}  rework {r['rework']}/{r['requests']} ({100 * r['rate']:.0f}%)")
        for g in a["groups"]:
            label = g["name"] if g["kind"] == "routine" else g["kind"]
            print(f"    {g['kind'][:8]:8s} {label[:40]:40s} requests={g['requests']:4d} {_money(g)}")


if OPT.json:
    print(json.dumps(cost_report(DAYS, OPT.brl), indent=2))
    sys.exit(0)
if "--save" in sys.argv:
    out = subprocess.run([sys.executable, __file__, *[a for a in sys.argv[1:] if a != "--save"]], capture_output=True, text=True).stdout
    last = H / ".claude/state/harness-report-last.txt"
    if last.exists():
        prev = last.read_text()
        print("== previous harness section (" + time.strftime("%Y-%m-%d", time.localtime(last.stat().st_mtime)) + ")")
        print(prev[prev.find("== harness usage"):].rstrip() if "== harness usage" in prev else "(none)")
        print()
    print(out, end="")
    last.parent.mkdir(parents=True, exist_ok=True)
    last.write_text(out)
    os.chmod(last, 0o600)
    sys.exit(0)
print("== RTK (command rewriting)")
try:
    out = subprocess.run(["rtk", "gain"], capture_output=True, text=True, timeout=20).stdout.splitlines()
    print("\n".join(l for l in out if l.startswith(("Total commands", "Input tokens", "Tokens saved"))))
except Exception:
    print("rtk not available")

print("\n== te-filter hook (ledger; entries before 2026-10-19 never reached the model)")
led = H / ".claude/te-ledger.jsonl"
if led.exists():
    rows = [json.loads(l) for l in led.read_text().splitlines() if l.strip()]
    ap = [r for r in rows if r.get("applied")]
    print(f"decisions: {len(rows)}  applied: {len(ap)}  tokens saved: {sum(r['before'] - r['after'] for r in ap)}")
else:
    print("no ledger yet (hook not fired)")

print("\n== tool-result text tokens in transcripts (top)")
names, size, cnt = {}, C.Counter(), C.Counter()
for f in glob.glob(str(H / ".claude/projects/*/*.jsonl")):
    for line in open(f, errors="ignore"):
        try:
            c = (json.loads(line).get("message") or {}).get("content")
        except ValueError:
            continue
        if not isinstance(c, list):
            continue
        for x in c:
            if not isinstance(x, dict):
                continue
            if x.get("type") == "tool_use":
                names[x["id"]] = x.get("name", "?")
            elif x.get("type") == "tool_result":
                t = names.get(x.get("tool_use_id"), "?")
                b = x.get("content")
                n = len(b) if isinstance(b, str) else sum(len(i.get("text", "")) for i in (b or []) if isinstance(i, dict))
                size[t] += n
                cnt[t] += 1
tot = sum(size.values()) or 1
for t, v in size.most_common(8):
    print(f"  {t[:34]:34s} calls={cnt[t]:5d} ~tok={v // 4:8d} {100 * v / tot:3.0f}%")

# --- harness usage over the last N days (default 7): is the setup being used and are replies short?
import statistics

days = DAYS
skills, slash, words = C.Counter(), C.Counter(), []
for f in glob.glob(str(H / ".claude/projects/*/*.jsonl")):
    if time.time() - os.path.getmtime(f) > days * 86400:
        continue
    for line in open(f, errors="ignore"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        c = (d.get("message") or {}).get("content")
        if d.get("type") == "assistant" and isinstance(c, list):
            txt = "".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
            if txt.strip():
                words.append(len(txt.split()))
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill":
                    skills[b.get("input", {}).get("skill", "?")] += 1
        elif d.get("type") == "user" and isinstance(c, str):
            for s in re.findall(r"<command-name>/?([^<]+)</command-name>", c):
                slash[s] += 1

print(f"\n== harness usage, last {days} days")
print("  skills (model-invoked):", dict(skills.most_common(10)) or "none")
print("  slash commands:", dict(slash.most_common(10)) or "none")
print("  /goal runs:", slash.get("goal", 0))
if words:
    w = sorted(words)
    print(f"  replies: {len(w)}  median {statistics.median(w):.0f} words  p90 {w[int(.9 * len(w))]}  over 150 words: {100 * sum(x > 150 for x in w) // len(w)}%")
else:
    print("  replies: none")

print_cost(cost_report(DAYS, OPT.brl))
