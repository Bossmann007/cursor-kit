#!/usr/bin/env python3
"""sessionStart: inject checkpoint summary + compression hint."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS))

from cursor_state import (  # noqa: E402
    checkpoint_summary,
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
    ensure_checkpoint_exists(root)
    checkpoint = load_checkpoint(root)
    summary = checkpoint_summary(checkpoint)

    extra = (
        f"{summary}\n"
        "Token hint: compress Shell/Read outputs >~500 tokens via token-engine "
        "`caveman_compress` / `token_engine_compress_session`. "
        "Explore code via codebase-memory before full-file Read. "
        "Non-trivial work: /poteto-mode."
    )
    print(json.dumps({"additional_context": extra}))


if __name__ == "__main__":
    main()
