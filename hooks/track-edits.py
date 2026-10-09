#!/usr/bin/env python3
"""afterFileEdit: track edited paths in session.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS))

from cursor_state import track_file, workspace_root  # noqa: E402


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
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    path = (
        tool_input.get("file_path")
        or tool_input.get("notebook_path")
        or payload.get("file_path")
        or payload.get("path")
        or payload.get("file")
        or ""
    )
    if isinstance(path, str) and path.strip():
        track_file(path.strip(), root)
    print("{}")


if __name__ == "__main__":
    main()
