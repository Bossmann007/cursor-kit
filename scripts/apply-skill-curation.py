#!/usr/bin/env python3
"""Merge claude/skill-overrides.json ('off' list) into ~/.claude/settings.json skillOverrides. Backup first, mode 600."""
import json, os, shutil, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = Path.home() / ".claude/settings.json"
want = json.loads((ROOT / "claude/skill-overrides.json").read_text())["off"]
d = json.loads(S.read_text())
o = d.setdefault("skillOverrides", {})
changed = [n for n in want if o.get(n) != "off"]
if changed:
    b = S.with_name(S.name + f".bak.{time.strftime('%Y%m%d%H%M%S')}")
    shutil.copy2(S, b); os.chmod(b, 0o600)
    for n in changed:
        o[n] = "off"
    S.write_text(json.dumps(d, indent=2) + "\n"); os.chmod(S, 0o600)
print(f"skill curation: {len(changed)} set to off, {len(want) - len(changed)} already")
