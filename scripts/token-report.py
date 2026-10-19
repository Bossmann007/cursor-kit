#!/usr/bin/env python3
"""Where do tokens go? RTK savings + te-filter ledger + tool-result sizes + harness usage from Claude Code transcripts.

usage: token-report.py [DAYS=7] [--save]
--save keeps the output in ~/.claude/state/harness-report-last.txt (mode 600) and prints the previous harness section first.
"""
import collections as C
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

H = Path.home()
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
import re
import statistics
import sys
import time

args = [a for a in sys.argv[1:] if not a.startswith("--")]
days = int(args[0]) if args else 7
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
