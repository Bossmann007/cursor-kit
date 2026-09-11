#!/usr/bin/env python3
"""postToolUse: note large Shell/Read outputs that should be compressed."""
from __future__ import annotations

import json
import sys


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return

    if not isinstance(payload, dict):
        print("{}")
        return

    tool = str(payload.get("tool_name") or payload.get("toolName") or "")
    output = (
        payload.get("tool_output")
        or payload.get("output")
        or payload.get("result")
        or ""
    )
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False) if output else ""

    tokens = _approx_tokens(output)
    if tokens < 500:
        print("{}")
        return

    msg = (
        f"Large {tool or 'tool'} output (~{tokens} tok). "
        "Call token-engine `caveman_compress` (or compress_session) before keeping raw text."
    )
    print(json.dumps({"additional_context": msg}))


if __name__ == "__main__":
    main()
