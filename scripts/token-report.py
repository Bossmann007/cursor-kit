#!/usr/bin/env python3
"""Where do tokens go? RTK savings + te-filter ledger + tool-result sizes from Claude Code transcripts."""
import collections as C
import glob
import json
import os
import subprocess
from pathlib import Path

H = Path.home()
print("== RTK (command rewriting)")
try:
    out = subprocess.run(["rtk", "gain"], capture_output=True, text=True, timeout=20).stdout.splitlines()
    print("\n".join(l for l in out if l.startswith(("Total commands", "Input tokens", "Tokens saved"))))
except Exception:
    print("rtk not available")

print("\n== te-filter hook (ledger)")
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
