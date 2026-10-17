#!/usr/bin/env python3
"""Offline search of the Claude Code plugin catalog (~300 official plugins) -> compact ranked lines.
usage: find-plugins.py <keyword> [keyword...] [-n 8]
Shows installs, always-on token cost (what the plugin adds to EVERY turn), components and the install command."""
import json
import re
import sys
from pathlib import Path

cat = json.loads((Path.home() / ".claude/plugins/plugin-catalog-cache.json").read_text())["catalog"]["plugins"]
args = sys.argv[1:]
n = 8
if "-n" in args:
    i = args.index("-n"); n = int(args[i + 1]); del args[i:i + 2]
words = [w.lower() for w in args]
if not words:
    sys.exit(__doc__)
rows = []
for key, p in cat.items():
    e = p.get("marketplace_entry", {})
    comp = p.get("components", {})
    hay = " ".join([key, e.get("description", ""), " ".join(e.get("tags", []) or []), e.get("category", "") or "",
                    " ".join(s["name"] for s in comp.get("skills", [])), " ".join(comp.get("mcpServers", []))]).lower()
    score = sum(hay.count(w) * (3 if w in key.lower() else 1) for w in words)
    if score:
        rows.append((score, p.get("unique_installs", 0), key, p, e, comp))
rows.sort(key=lambda r: (-r[0], -r[1]))
for score, inst, key, p, e, comp in rows[:n]:
    tok = (p.get("tokens", {}).get("claude-sonnet-4-6") or {}).get("always_on", "?")
    parts = [f"{len(comp.get(k, []))} {k}" for k in ("skills", "agents", "hooks", "mcpServers") if comp.get(k)]
    print(f"{key}  installs={inst}  always-on~{tok}tok  [{', '.join(parts) or 'no components'}]")
    desc = re.sub(r"\s+", " ", e.get("description", ""))[:150]
    print(f"   {desc}")
    print(f"   claude plugin install {key}")
if not rows:
    print("no match in local catalog; try GitHub / MCP registry")
