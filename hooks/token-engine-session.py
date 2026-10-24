#!/usr/bin/env python3
"""sessionStart: inject checkpoint summary + compression hint."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS))

from cursor_state import (  # noqa: E402
    should_run,
    checkpoint_summary,
    emit_context,
    ensure_checkpoint_exists,
    load_checkpoint,
    workspace_root,
)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    root = workspace_root(payload if isinstance(payload, dict) else None)
    if not should_run("token-engine-session", root):
        print("{}")
        return
    ensure_checkpoint_exists(root)
    checkpoint = load_checkpoint(root)
    if not checkpoint.get("task"):
        print("{}")
        return
    emit_context("SessionStart", checkpoint_summary(checkpoint))


if __name__ == "__main__":
    main()
