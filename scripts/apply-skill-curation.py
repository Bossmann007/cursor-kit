#!/usr/bin/env python3
"""Merge claude/skill-overrides.json into ~/.claude/settings.json skillOverrides. Backup first, mode 600.

'off' and 'name-only' set that override; 'on' deletes the override (skill back to default, i.e. on).
Overrides for names not in the file are never touched.
"""
import json, os, shutil, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply(settings: Path, cfg: dict) -> tuple[int, int, int]:
    """Return (set, removed, already) counts."""
    both = set(cfg.get("on", [])) & (set(cfg["off"]) | set(cfg.get("name-only", [])))
    if both:
        raise SystemExit(f"skill curation: in 'on' and in 'off'/'name-only': {sorted(both)}")
    want = {n: "off" for n in cfg["off"]} | {n: "name-only" for n in cfg.get("name-only", [])}
    d = json.loads(settings.read_text())
    o = d.setdefault("skillOverrides", {})
    changed = [n for n, v in want.items() if o.get(n) != v]
    removed = [n for n in cfg.get("on", []) if n in o]
    if changed or removed:
        b = settings.with_name(settings.name + f".bak.{time.strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(settings, b); os.chmod(b, 0o600)
        for n in changed:
            o[n] = want[n]
        for n in removed:
            del o[n]
        settings.write_text(json.dumps(d, indent=2) + "\n"); os.chmod(settings, 0o600)
    return len(changed), len(removed), len(want) - len(changed)


if __name__ == "__main__":
    cfg = json.loads((ROOT / "claude/skill-overrides.json").read_text())
    set_, removed, already = apply(Path.home() / ".claude/settings.json", cfg)
    print(f"skill curation: {set_} set, {removed} removed, {already} already set")
