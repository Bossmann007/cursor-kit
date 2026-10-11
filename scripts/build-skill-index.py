#!/usr/bin/env python3
"""Build a compact index of the skills actually enabled for Claude Code -> ~/.claude/skill-index.md.
find-skills reads this one small file instead of loading every skill description. Re-run after changing plugins/skills."""
import json, re, time
from pathlib import Path

H = Path.home()
C = H / ".claude"
settings = json.loads((C / "settings.json").read_text())
enabled = settings.get("enabledPlugins", {})
over = settings.get("skillOverrides", {})
MAX = 78


def meta(path):
    t = path.read_text(errors="ignore")
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    fm = m.group(1) if m else ""
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    d = re.search(r"^description:\s*(.*?)(?=\n[a-zA-Z_-]+:|\Z)", fm, re.M | re.S)
    desc = re.sub(r"^[>|][+-]?\s*", "", d.group(1).strip()) if d else ""
    desc = re.sub(r"\s+", " ", desc.strip("\"' "))
    s = re.split(r"(?<=[.!?])\s", desc)[0]
    return (name.group(1).strip().strip("\"'") if name else path.parent.name), s[:MAX]


rows = []


def add(prefix, skill_md):
    n, d = meta(skill_md)
    full = f"{prefix}:{n}" if prefix else n
    if over.get(full) == "off" or over.get(f"{prefix}:{skill_md.parent.name}") == "off":
        return
    if full.startswith("pstack:principle-"):
        return
    rows.append((full, "" if over.get(full) == "name-only" else d))


for p in sorted((C / "skills").glob("*/SKILL.md")):
    add("", p)
inst = json.loads((C / "plugins/installed_plugins.json").read_text())
inst = inst.get("plugins", inst)
for key, v in inst.items():
    if enabled.get(key) is False:
        continue
    for p in sorted((Path(v[0]["installPath"]) / "skills").glob("*/SKILL.md")):
        add(key.split("@")[0], p)
for p in sorted((C / "plugins/synced").glob("*/*/skills/*/SKILL.md")):
    plugin = p.parents[2].name
    if enabled.get(f"{plugin}@synced") is False:
        continue
    add(plugin, p)

out = ["# Installed skills (auto-generated, do not edit)", f"# built {time.strftime('%Y-%m-%d %H:%M')} | pstack principle-* omitted (name-only)", ""]
out += [f"{n} — {d}" if d else n for n, d in rows]
out += ["", "anthropic-skills (built-in): docx pptx xlsx pdf docs google-workspace schedule skill-creator consolidate-memory explain-usage"]
(C / "skill-index.md").write_text("\n".join(out) + "\n")
txt = "\n".join(out)
print(f"skill index: {len(rows)} skills, ~{len(txt)//4} tokens -> {C / 'skill-index.md'}")
