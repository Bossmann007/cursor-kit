#!/usr/bin/env python3
"""Stop: a reply that recommends something must cite a source or say "não verifiquei".

Uses `last_assistant_message` from the Stop input (the transcript is a fallback; the desktop app stores
reply text outside the assistant entries). If the reply recommends (recomendo, recommend, sugiro,
"o certo é") but has no URL, no file:line and no "não verifiquei"/"not verified", it continues the turn once with
non-error feedback asking for the source (`additionalContext`, the docs' recommended form for guidance). `stop_hook_active` true means it already asked this turn, so it lets the reply through.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RECOMMENDS = re.compile(r"\b(recomend|recommend|sugiro|suggest|o certo é|the right (call|move) is)", re.I)
SOURCE = re.compile(
    r"https?://|\b[\w./~-]+\.[A-Za-z0-9]{1,6}:\d+|não verifiquei|nao verifiquei|not verified|não testei", re.I)
REASON = ("This reply recommends something without a source. Before stopping: cite the primary source you read in "
          "this session (URL or file:line) for each fact the recommendation rests on, name the one fact that would "
          "make it wrong and how you checked it, and say whether it is reversible. If you did not check, say "
          "\"não verifiquei\" instead of recommending.")


def last_assistant_text(transcript: Path) -> str:
    texts: list[str] = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = entry.get("type")
        if kind == "user" and not _is_tool_result(entry):
            texts = []  # a new user turn starts
        elif kind == "assistant":
            for block in (entry.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text") or "")
    return "\n".join(texts)


def _is_tool_result(entry: dict) -> bool:
    content = (entry.get("message") or {}).get("content")
    return isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def verdict(text: str) -> dict:
    if RECOMMENDS.search(text) and not SOURCE.search(text):
        return {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": REASON}}
    return {}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if payload.get("stop_hook_active"):
            print("{}")
            return
        text = payload.get("last_assistant_message")
        if text is None:
            path = Path(payload.get("transcript_path") or "")
            text = last_assistant_text(path) if path.is_file() else ""
        out = verdict(text)
    except Exception:  # never wedge a session on a hook error
        out = {}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
