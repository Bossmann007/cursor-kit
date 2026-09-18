#!/usr/bin/env python3
"""Merge kit hooks.json into an existing Cursor hooks.json without dropping companions.

Kit-owned entries are identified by known script basenames (token-engine, checkpoint, …).
Non-kit commands (ai-memory, rtk, user hooks) are preserved per event.
Events that exist only in the existing file are kept intact.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

KIT_MARKERS = (
    "token-engine-session.py",
    "compress-tool-output.py",
    "tool-failure.py",
    "track-edits.py",
    "checkpoint-stop.py",
)


def is_kit_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    cmd = str(entry.get("command", ""))
    return any(marker in cmd for marker in KIT_MARKERS)


def merge_hooks(existing: dict[str, Any] | None, kit: dict[str, Any]) -> dict[str, Any]:
    if not existing:
        return kit

    out: dict[str, Any] = {
        "version": kit.get("version", existing.get("version", 1)),
        "hooks": {},
    }
    existing_hooks = existing.get("hooks") or {}
    kit_hooks = kit.get("hooks") or {}

    # Preserve unknown top-level keys from existing (forward-compat)
    for key, value in existing.items():
        if key not in ("version", "hooks"):
            out[key] = value

    all_events = list(dict.fromkeys([*kit_hooks.keys(), *existing_hooks.keys()]))
    for event in all_events:
        kit_entries = list(kit_hooks.get(event) or [])
        existing_entries = list(existing_hooks.get(event) or [])
        preserved = [e for e in existing_entries if not is_kit_entry(e)]
        if event in kit_hooks:
            out["hooks"][event] = kit_entries + preserved
        else:
            out["hooks"][event] = existing_entries

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", required=True, help="Resolved kit hooks.json (from template)")
    parser.add_argument("--existing", help="Current ~/.cursor/hooks.json (optional)")
    parser.add_argument("--out", required=True, help="Output path")
    args = parser.parse_args()

    kit = json.loads(Path(args.kit).read_text(encoding="utf-8"))
    existing = None
    if args.existing and Path(args.existing).is_file():
        existing = json.loads(Path(args.existing).read_text(encoding="utf-8"))

    merged = merge_hooks(existing, kit)
    Path(args.out).write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
