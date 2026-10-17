#!/usr/bin/env python3
"""Fail if README.md, docs/EVIDENCE.md or any skills/*/SKILL.md links to a local file that does not exist."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = [ROOT / "README.md", ROOT / "docs/EVIDENCE.md", *sorted((ROOT / "skills").glob("*/SKILL.md"))]
bad = []
for f in files:
    if not f.exists():
        continue
    text = re.sub(r"```.*?```", "", f.read_text(), flags=re.S)
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = target.split("#")[0]
        if path and not (f.parent / path).exists():
            bad.append(f"{f.relative_to(ROOT)}: {target}")
print("\n".join(bad) or f"docs ok ({len(files)} files)")
sys.exit(1 if bad else 0)
