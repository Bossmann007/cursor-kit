"""Copy of ~/.cursor/hooks/cursor_state.py — source of truth in cursor-kit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHECKPOINT_NAME = "checkpoint.json"
SESSION_NAME = "session.json"
FAILURES_NAME = "failures.jsonl"
OBS_NAME = "observability.jsonl"

DEFAULT_CHECKPOINT: dict[str, Any] = {
    "task": "",
    "status": "idle",
    "completed": [],
    "pending": [],
    "blockers": [],
    "files": [],
    "tests": "",
    "next_action": "",
    "updated_at": "",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def workspace_root(payload: dict[str, Any] | None = None) -> Path:
    if payload:
        for key in ("workspace_roots", "workspace_root", "project_path", "cwd", "root"):
            val = payload.get(key)
            if isinstance(val, list) and val:
                return Path(str(val[0])).resolve()
            if isinstance(val, str) and val.strip():
                return Path(val).resolve()
    return Path.cwd().resolve()


def state_dir(root: Path | None = None) -> Path:
    base = root or Path.cwd()
    directory = base / ".cursor" / "state"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return dict(default)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def checkpoint_path(root: Path | None = None) -> Path:
    return state_dir(root) / CHECKPOINT_NAME


def session_path(root: Path | None = None) -> Path:
    return state_dir(root) / SESSION_NAME


def load_checkpoint(root: Path | None = None) -> dict[str, Any]:
    return _read_json(checkpoint_path(root), DEFAULT_CHECKPOINT)


def save_checkpoint(data: dict[str, Any], root: Path | None = None) -> None:
    data = dict(data)
    data["updated_at"] = _now_iso()
    _write_json(checkpoint_path(root), data)


def load_session(root: Path | None = None) -> dict[str, Any]:
    return _read_json(
        session_path(root),
        {"files": [], "tool_failures": 0, "started_at": _now_iso()},
    )


def save_session(data: dict[str, Any], root: Path | None = None) -> None:
    _write_json(session_path(root), data)


def track_file(path: str, root: Path | None = None) -> None:
    session = load_session(root)
    files: list[str] = list(session.get("files") or [])
    normalized = path.replace("\\", "/")
    if normalized not in files:
        files.append(normalized)
    session["files"] = files[-50:]
    save_session(session, root)


def merge_session_into_checkpoint(
    root: Path | None = None,
    *,
    status: str = "idle",
) -> dict[str, Any]:
    checkpoint = load_checkpoint(root)
    session = load_session(root)
    session_files = list(session.get("files") or [])
    if session_files:
        existing = list(checkpoint.get("files") or [])
        merged = existing + [f for f in session_files if f not in existing]
        checkpoint["files"] = merged[-50:]
    if status in ("completed", "error", "aborted"):
        checkpoint["status"] = status if status != "completed" else checkpoint.get("status") or "idle"
    save_checkpoint(checkpoint, root)
    session["files"] = []
    save_session(session, root)
    return checkpoint


def append_failure(entry: dict[str, Any], root: Path | None = None) -> None:
    path = state_dir(root) / FAILURES_NAME
    line = dict(entry)
    line.setdefault("at", _now_iso())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")


def append_obs(entry: dict[str, Any], root: Path | None = None) -> None:
    path = state_dir(root) / OBS_NAME
    line = dict(entry)
    line.setdefault("at", _now_iso())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")


def checkpoint_summary(checkpoint: dict[str, Any]) -> str:
    task = checkpoint.get("task") or "(no task set)"
    status = checkpoint.get("status") or "idle"
    pending = checkpoint.get("pending") or []
    next_action = checkpoint.get("next_action") or ""
    parts = [f"Checkpoint: task={task!r} status={status}"]
    if pending:
        parts.append(f"pending={pending[:5]}")
    if next_action:
        parts.append(f"next={next_action!r}")
    return " | ".join(parts)


def ensure_checkpoint_exists(root: Path | None = None) -> None:
    path = checkpoint_path(root)
    if not path.is_file():
        example = root / ".cursor" / "state" / "checkpoint.json.example" if root else None
        if example and example.is_file():
            path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            save_checkpoint(dict(DEFAULT_CHECKPOINT), root)
