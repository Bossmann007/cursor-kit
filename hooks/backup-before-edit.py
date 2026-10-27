#!/usr/bin/env python3
"""PreToolUse(Edit|Write|MultiEdit): copy a config or persona file before it changes, so every edit is reversible.

Covers files outside git that steer agents: any settings*.json, AGENTS.md, CLAUDE.md, and files under ~/.claude
(except transcripts and caches). Git-tracked files are skipped: git already holds their last version.
Never blocks; prints {} and exits 0 on any error.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
BACKUPS = HOME / "Backups" / "edits"
NAMES = {"AGENTS.md", "CLAUDE.md"}
SKIP_UNDER = ("projects", "transcripts", "te-cache", "paste-cache", "file-history", "sessions", "shell-snapshots")


def protected(path: Path) -> bool:
    if path.name in NAMES or (path.name.startswith("settings") and path.suffix == ".json"):
        return True
    try:
        rel = path.relative_to(HOME / ".claude")
    except ValueError:
        return False
    return bool(rel.parts) and rel.parts[0] not in SKIP_UNDER


def tracked(path: Path) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(path.parent), "ls-files", "--error-unmatch", path.name],
                           capture_output=True, timeout=3)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def backup(path: Path) -> Path:
    day = time.strftime("%Y%m%d")
    stamp = time.strftime("%H%M%S")
    flat = str(path.resolve()).lstrip("/").replace("/", "__")
    dest = BACKUPS / day / f"{flat}.{stamp}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        raw = (payload.get("tool_input") or {}).get("file_path") or ""
        path = Path(raw).expanduser()
        if raw and path.is_file() and protected(path) and not tracked(path):
            backup(path)
    except Exception:  # a backup hook must never stop the edit
        pass
    print("{}")


if __name__ == "__main__":
    main()
