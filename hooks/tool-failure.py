#!/usr/bin/env python3
"""postToolUseFailure: append to failures.jsonl."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS))

from cursor_state import append_failure, load_session, save_session, workspace_root  # noqa: E402


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return

    if not isinstance(payload, dict):
        print("{}")
        return

    root = workspace_root(payload)
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    entry = {
        "tool": payload.get("tool_name") or payload.get("toolName"),
        "error": payload.get("error") or payload.get("message") or payload.get("stderr"),
        "command": tool_input.get("command") or payload.get("command"),
    }
    append_failure(entry, root)
    session = load_session(root)
    session["tool_failures"] = int(session.get("tool_failures") or 0) + 1
    save_session(session, root)
    print("{}")


if __name__ == "__main__":
    main()
