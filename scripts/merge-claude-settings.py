#!/usr/bin/env python3
"""Merge kit Claude hooks into ~/.claude/settings.json without dropping other hooks.

Kit-owned entries = commands whose path ends in one of the kit hook basenames.
usage: merge-claude-settings.py --kit KIT.json --existing SETTINGS.json --out OUT.json
"""
import argparse, json, pathlib

KIT = ("token-engine-session.py", "compress-tool-output.py", "track-edits.py",
       "tool-failure.py", "checkpoint-stop.py")

def is_kit(group):
    return any(h.get("command", "").strip().endswith(KIT) or any(k in h.get("command", "") for k in KIT)
               for h in group.get("hooks", []))

ap = argparse.ArgumentParser()
ap.add_argument("--kit", required=True); ap.add_argument("--existing", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
kit = json.loads(pathlib.Path(a.kit).read_text())
ex_path = pathlib.Path(a.existing)
cur = json.loads(ex_path.read_text()) if ex_path.is_file() and ex_path.read_text().strip() else {}
hooks = cur.setdefault("hooks", {})
for event, groups in kit["hooks"].items():
    keep = [g for g in hooks.get(event, []) if not is_kit(g)]
    hooks[event] = keep + groups
pathlib.Path(a.out).write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n")
