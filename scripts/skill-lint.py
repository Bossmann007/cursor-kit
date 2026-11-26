#!/usr/bin/env python3
"""Pass-or-fail quality checks for skills/*/SKILL.md (documented in docs/WORKFLOWS.md, "Writing a skill").

Reports every skill. Exit 1 only when a skill added or changed against the base ref (default origin/master) fails,
so existing skills are reported without breaking scripts/verify. Structural checks only; no intent guessing.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

DESC_WARN_CHARS = 600  # about 100-150 tokens
MAX_BODY_LINES = 500
CHECK_WORDS = re.compile(
    r"\b(check|checks|checked|verify|verifies|verified|confirm|confirms|expect|expects|assert|asserts|"
    r"done when|exit code|exit status|exit 0|until|succeeds|passes|verifique|confirme|confira)\b",
    re.I,
)
RECOVERY_HEADING = re.compile(
    r"^#{1,6}\s+(?:\d+[.)]\s+)?(?:common\s+)?(errors?|failures?|recovery|troubleshooting|(?:if|when) .* fails|erros?|falhas?)\b",
    re.I,
)
VAGUE_FIX = re.compile(
    r"^\W*(just\s+)?(try( it)? again|retry|re-?run( it)?|run( it)? again|tente novamente|tentar novamente|"
    r"de novo)\W*$",
    re.I,
)
STEP = re.compile(r"^(?:#{1,6}\s+)?\d+[.)]\s")
HEADING = re.compile(r"^(#{1,6})\s")


def split_frontmatter(text):
    """Return (fields, body_lines). fields is None when the file has no closed --- frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, lines
    fields, key = {}, None
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            fields[key] = "" if re.fullmatch(r"[>|][+-]?", value) else value.strip("\"'")
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, lines[end + 1 :]


def strip_fences(lines):
    """Replace fenced code lines with a marker so headings/lists inside code are ignored."""
    out, fenced = [], False
    for line in lines:
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            out.append("\0fence")
        else:
            out.append("\0fence" if fenced else line)
    return out


def check_frontmatter(fields):
    if fields is None:
        return ["no --- frontmatter block"], []
    errors = [f"frontmatter has no {k}" for k in ("name", "description") if not fields.get(k)]
    desc = fields.get("description", "")
    warns = [f"description is {len(desc)} chars (> {DESC_WARN_CHARS})"] if len(desc) > DESC_WARN_CHARS else []
    return errors, warns


def check_length(body):
    return [f"body is {len(body)} lines (max {MAX_BODY_LINES - 1})"] if len(body) >= MAX_BODY_LINES else []


def section_end(lines, i):
    """Index of the first heading after line i at the same or a higher level than the heading on line i."""
    level = len(HEADING.match(lines[i]).group(1))
    for j in range(i + 1, len(lines)):
        h = HEADING.match(lines[j])
        if h and len(h.group(1)) <= level:
            return j
    return len(lines)


def recovery_sections(lines):
    """(start, end) line ranges of each error-recovery section, heading included."""
    return [(i, section_end(lines, i)) for i, line in enumerate(lines) if RECOVERY_HEADING.match(line)]


def steps(lines):
    """Yield (label, block_lines) for each numbered step: a top-level `1.` list item or a `### 1.` heading.
    Numbered items inside an error-recovery section are recovery rows, not steps."""
    skip = recovery_sections(lines)
    starts = [i for i, l in enumerate(lines) if STEP.match(l) and not any(a <= i < b for a, b in skip)]
    for i in starts:
        if lines[i].startswith("#"):
            block = lines[i : section_end(lines, i)]
        else:
            block = [lines[i]]
            for line in lines[i + 1 :]:
                if STEP.match(line) or HEADING.match(line):
                    break
                if line and not line[0].isspace() and line != "\0fence":
                    break  # a list item ends at the next unindented line
                block.append(line)
        yield re.sub(r"^#+\s+", "", lines[i]).split()[0].rstrip(".)"), block


def check_steps(lines):
    found = list(steps(lines))
    if not found:
        return ["no numbered steps"]
    texts = ["\n".join(block) for _, block in found]
    no_cmd = sum("`" not in t and "\0fence" not in t for t in texts)
    no_check = sum(not CHECK_WORDS.search(t) for t in texts)
    errors = []
    if no_cmd:
        errors.append(f"{no_cmd}/{len(found)} without a `command`")
    if no_check:
        errors.append(f"{no_check}/{len(found)} without a check")
    return errors


def recovery_rows(section):
    """Concrete failure -> fix rows in a table or list; rows whose fix is only 'try again' do not count."""
    rows, table_seen = [], False
    for line in section:
        s = line.strip()
        if not s.startswith("|"):
            table_seen = False  # the next table has its own header row
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            if not table_seen:  # header row
                table_seen = True
                continue
            if len([c for c in cells if c]) >= 2:
                rows.append(cells[-1])
            continue
        m = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$", line)
        if m:
            parts = re.split(r"\s*(?:→|->|=>|:\s| — | – )\s*", m.group(1), maxsplit=1)
            if len(parts) == 2 and parts[0] and parts[1]:
                rows.append(parts[1])
    return [r for r in rows if not VAGUE_FIX.match(re.sub(r"[*_`]", "", r))]


def check_recovery(lines):
    if any(recovery_rows(lines[a + 1 : b]) for a, b in recovery_sections(lines)):
        return []
    return ["no failure -> fix section"]


def lint(path):
    """Return (errors_by_check, warnings) for one SKILL.md."""
    fields, body = split_frontmatter(path.read_text(encoding="utf-8-sig"))
    clean = strip_fences(body)
    fm_errors, warns = check_frontmatter(fields)
    errors = {
        "frontmatter": fm_errors,
        "length": check_length(body),
        "steps": check_steps(clean),
        "recovery": check_recovery(clean),
    }
    return {k: v for k, v in errors.items() if v}, warns


def git(root, *args):
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def changed_skills(root, base):
    """Skill names whose SKILL.md was added or changed since merge-base(base, HEAD), incl. uncommitted; None if no git base."""
    top = git(root, "rev-parse", "--show-toplevel")
    if not top or Path(top.strip()).resolve() != root.resolve():
        return None  # not a checkout of this root (e.g. a tarball unpacked inside another repo)
    mb = git(root, "merge-base", base, "HEAD")
    if not mb:
        return None
    paths = (git(root, "diff", "-z", "--name-only", "--diff-filter=d", mb.strip(), "--", "skills") or "").split("\0")
    paths += (git(root, "ls-files", "-z", "--others", "--exclude-standard", "--", "skills") or "").split("\0")
    return {p.split("/")[1] for p in paths if re.fullmatch(r"skills/[^/]+/SKILL\.md", p)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=Path(__file__).resolve().parents[1], type=Path)
    ap.add_argument("--base", default="origin/master", help="git ref; skills changed since its merge-base must pass")
    ap.add_argument("--changed", help="comma-separated skill names to gate instead of asking git")
    args = ap.parse_args(argv)

    results = {}
    for f in sorted((args.root / "skills").glob("*/SKILL.md")):
        results[f.parent.name] = lint(f)
    width = max((len(n) for n in results), default=0)
    for name, (errors, warns) in results.items():
        detail = "; ".join(f"{k}: {', '.join(v)}" for k, v in errors.items())
        print(f"{'FAIL' if errors else 'PASS'}  {name:<{width}}  {detail}".rstrip())
        for w in warns:
            print(f"WARN  {name:<{width}}  {w}")

    failing = [n for n, (e, _) in results.items() if e]
    by_check = {k: sum(k in e for e, _ in results.values()) for k in ("frontmatter", "length", "steps", "recovery")}
    print(
        f"skill-lint: {len(results)} skills, {len(results) - len(failing)} pass, {len(failing)} fail "
        f"({', '.join(f'{k} {v}' for k, v in by_check.items())}), "
        f"{sum(1 for _, w in results.values() if w)} warn"
    )

    if args.changed is not None:
        changed = {n for n in args.changed.split(",") if n}
    else:
        changed = changed_skills(args.root, args.base)
        if changed is None:
            print(f"skill-lint gate SKIPPED: no git merge-base with {args.base} (report only)")
            return 0
    gated = sorted(n for n in changed if n in failing)
    if gated:
        print(f"skill-lint gate FAIL: changed skills failing: {', '.join(gated)} "
              f"(changed since merge-base with {args.base}; if you did not touch them, run `git fetch origin`)")
        return 1
    print(f"skill-lint gate ok: {len(changed & results.keys())} changed skill(s), none failing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
