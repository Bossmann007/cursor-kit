#!/usr/bin/env python3
"""Add-only merge of kit MCP servers into a client JSON config. Never overwrites or prints existing entries."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

HOME = Path.home()
TE = HOME / ".cursor/repos/token-engine"
SECRET_KEY = re.compile(r"(pass|secret|token|apikey|api_key|auth|cookie|credential)", re.I)


def servers(client: str) -> dict:
    http = "httpUrl" if client == "gemini" else "url"
    return {
        "token-engine": {"command": str(TE / ".venv/bin/python"), "args": ["-m", "token_engine.mcp.server"],
                         "env": {"PYTHONPATH": str(TE / "src")}},
        "codebase-memory": {"command": str(HOME / ".local/bin/codebase-memory-mcp"), "args": []},
        "context7": {http: "https://mcp.context7.com/mcp"},
        "ai-memory": {http: "http://127.0.0.1:49374/mcp"},
    }


def check_no_secrets(entries: dict) -> None:
    for name, e in entries.items():
        for k in (e.get("env") or {}):
            if SECRET_KEY.search(k) and k != "PYTHONPATH":
                sys.exit(f"refusing: secret-like env key in kit entry {name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", choices=["cursor", "gemini"], required=True)
    ap.add_argument("--file", required=True)
    a = ap.parse_args()
    os.umask(0o077)
    path = Path(a.file).expanduser()
    want = servers(a.client)
    check_no_secrets(want)
    data = json.loads(path.read_text()) if path.exists() else {}
    cur = data.setdefault("mcpServers", {})
    added = [k for k in want if k not in cur]
    if not added:
        print(f"{a.client}: mcp up to date")
        return
    if path.exists():
        bak = path.with_name(path.name + f".bak.{time.strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(path, bak)
        os.chmod(bak, 0o600)
    for k in added:
        cur[k] = want[k]
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    print(f"{a.client}: added {', '.join(added)}")


if __name__ == "__main__":
    main()
