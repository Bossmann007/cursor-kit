#!/usr/bin/env python3
"""PostToolUse (Bash): replace large, compressible tool output with a token-engine-filtered version BEFORE it reaches the model.

Fail-open and fidelity-guarded:
- only outputs >= TE_MIN_TOKENS (default 1500) and >= TE_MIN_RATIO (default 0.25) saved
- every error-looking line of the original must survive, else the output is left untouched
- the full original is kept in ~/.claude/te-cache and referenced in a footer
- every decision is logged to ~/.claude/te-ledger.jsonl (see scripts/token-report.py)
Needs Claude Code to honor hookSpecificOutput.updatedToolOutput; if it does not, output is simply unchanged.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path.home()
CACHE = HOME / ".claude" / "te-cache"
LEDGER = HOME / ".claude" / "te-ledger.jsonl"
MIN_TOKENS = int(os.environ.get("TE_MIN_TOKENS", "1500"))
MIN_RATIO = float(os.environ.get("TE_MIN_RATIO", "0.25"))
ERR = re.compile(r"error|fail|traceback|exception|assert|fatal|panic|denied", re.I)


def _log(rec: dict) -> None:
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a") as f:
            f.write(json.dumps({"ts": int(time.time()), **rec}) + "\n")
        os.chmod(LEDGER, 0o600)
    except OSError:
        pass


def _prune() -> None:
    try:
        files = sorted(CACHE.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files[200:]:
            p.unlink()
        for p in files:
            if time.time() - p.stat().st_mtime > 7 * 86400:
                p.unlink()
    except OSError:
        pass


def filter_text(text: str, engine) -> tuple[str, int, int] | None:
    before = engine.count_tokens(text)
    if before < MIN_TOKENS:
        return None
    out = engine.optimize(text, content_type="").content
    after = engine.count_tokens(out)
    if after >= before or (before - after) / before < MIN_RATIO:
        return None
    kept = set(out.splitlines())
    for line in text.splitlines():
        if ERR.search(line) and line not in kept and line.strip() not in out:
            return None
    return out, before, after


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        resp = payload.get("tool_response")
        if isinstance(resp, dict):
            stdout, stderr = str(resp.get("stdout", "")), str(resp.get("stderr", ""))
        else:
            stdout, stderr = str(resp or ""), ""
        if not stdout or len(stdout) < MIN_TOKENS * 3:
            print("{}")
            return
        from token_engine import QualityLevel, TokenEngine
        from token_engine.core.config import EngineConfig

        cfg = EngineConfig.default()
        cfg.quality_level = QualityLevel("balanced")
        cfg.enable_ccr = False
        res = filter_text(stdout, TokenEngine(cfg))
        if res is None:
            _log({"tool": payload.get("tool_name"), "applied": False, "reason": "no-gain-or-guard"})
            print("{}")
            return
        out, before, after = res
        CACHE.mkdir(parents=True, exist_ok=True)
        os.chmod(CACHE, 0o700)
        path = CACHE / f"{int(time.time())}-{hashlib.sha1(stdout.encode()).hexdigest()[:10]}.txt"
        path.write_text(stdout)
        os.chmod(path, 0o600)
        _prune()
        footer = f"\n[token-engine: {before}->{after} tok; full output: {path}]"
        text = out + (f"\n{stderr}" if stderr else "") + footer
        _log({"tool": payload.get("tool_name"), "applied": True, "before": before, "after": after})
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": text}}))
    except Exception as exc:  # fail open
        _log({"applied": False, "reason": f"error:{type(exc).__name__}"})
        print("{}")


if __name__ == "__main__":
    main()
