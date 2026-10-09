---
name: digest-files
description: >
  Convert documents and binary files to Markdown with Microsoft MarkItDown
  (PDF, DOCX, PPTX, XLSX, HTML, images, audio, epub, zip, YouTube URLs). Use
  whenever the user asks to digir / digest / converter arquivo para md,
  markitdown, extrair texto de PDF/slides/Word/Excel, or needs LLM-ready
  Markdown from office/binary files — even if they do not say "digest-files".
  Prefer this over ad-hoc pdftotext or manual copy-paste.
disable-model-invocation: false
---

# Digest files (MarkItDown)

Turn files into Markdown for agents and RAG using **[MarkItDown](https://github.com/microsoft/markitdown)** (`pip install 'markitdown[all]'`).

Portuguese OK in chat. Paths, commands, and output filenames stay in English unless the project is PT-first.

## Process

### 0. Confirm inputs

1. Collect source path(s) or URL(s). Refuse untrusted remote URLs without user OK (MarkItDown can fetch network resources).
2. Ask output location if unclear. Defaults:
   - Single file: same dir as source, name `basename.md` (e.g. `aula01.pdf` → `aula01.md`)
   - Batch / folder: `./digest/` next to the sources (create if missing)
3. If the target `.md` already exists and is non-empty, ask before overwrite (idempotent: skip if content identical).

### 1. Ensure MarkItDown is available

Resolve the CLI in this order (do not use the ancient system `python3` on macOS CLT — it may pull a broken `0.0.1a1`):

1. `$MARKITDOWN` if set
2. `command -v markitdown`
3. `~/token-engine/.venv/bin/markitdown` (common on this stack)
4. Else install into a real 3.10+ venv:

```bash
# Prefer Homebrew or an existing project/token-engine venv
python3.12 -m pip install -U 'markitdown[all]'   # or: uv pip install ...
# Verify:
markitdown --version   # expect 0.1.x+, not 0.0.1a1
```

Need only a subset of formats: `pip install 'markitdown[pdf,docx,pptx,xlsx]'`.

Python **3.10+** required.

### 2. Convert

**CLI (preferred):**

```bash
markitdown "/ABS/OR/REL/path-to-file.pdf" -o "/path/to/output.md"
```

Stdout redirect also works:

```bash
markitdown "/path/to/file.pdf" > "/path/to/output.md"
```

**Batch:** use the kit script when present:

```bash
bash "$(dirname "$0")/scripts/digest.sh" /path/to/file_or_dir [--out DIR]
# or from cursor-kit:
# bash ~/cursor-kit/skills/digest-files/scripts/digest.sh ./Modulos --out ./digest
```

**Python API** (when you need programmatic control):

```python
from markitdown import MarkItDown
md = MarkItDown(enable_plugins=False)
result = md.convert("report.pdf")
Path("report.md").write_text(result.markdown, encoding="utf-8")
```

Prefer `convert_local()` for local-only paths when using the API in untrusted contexts.

### 3. After convert

1. Confirm the `.md` exists and size > 0.
2. Do **not** dump huge Markdown into the chat. Summarize: path, bytes/lines, first heading if any.
3. If the agent must reason over the content and the file is large, use token-engine `caveman_compress` on excerpts, or read only the sections needed (CBM / targeted Read).
4. Optional: add a one-line note in `PROJECT.md` or course notes only if the user asked to record digests.

### 4. Report

```markdown
## Digest complete
- Source: …
- Output: …
- Tool: markitdown …
- Notes: (OCR skipped / empty extract / overwrite skipped / …)
```

## Formats (built-in)

PDF, PowerPoint, Word, Excel, images (EXIF + OCR deps), audio (transcription extras), HTML, CSV/JSON/XML, ZIP (walks contents), EPub, YouTube URLs (extra), and more.

Azure Document Intelligence / Content Understanding flags exist (`-d`, `--use-cu`) but are **out of default scope** unless the user provides endpoints and asks.

## Guardrails

- Do not invent content when conversion fails. Report the error and suggest installing the right extra (`[pdf]`, etc.).
- Do not commit secrets from converted files into git without asking.
- Do not replace MarkItDown with a weaker one-off scraper when this skill was requested.
- Machine-specific absolute paths only in local commands, never in shared docs.

## Examples

**User:** "digere o Modulo03.pdf pra md"  
→ `markitdown Modulos/Modulo03.pdf -o Modulos/Modulo03.md` (or `digest/Modulo03.md` if they prefer a digest folder)

**User:** "converte todos os pptx da pasta Slides"  
→ batch into `./digest/` via `scripts/digest.sh`

**User:** "/digest-files" with an attachment path  
→ same pipeline; ask only if output path is ambiguous
