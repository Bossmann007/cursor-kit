#!/usr/bin/env python3
"""stop: merge session files into checkpoint; minimal observability."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS))

from cursor_state import append_obs, merge_session_into_checkpoint, workspace_root  # noqa: E402


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    root = workspace_root(payload if isinstance(payload, dict) else None)
    status = "idle"
    if isinstance(payload, dict):
        status = str(payload.get("status") or payload.get("reason") or "idle")
    merge_session_into_checkpoint(root, status=status)
    append_obs({"event": "stop", "status": status}, root)
    print("{}")


if __name__ == "__main__":
    main()
