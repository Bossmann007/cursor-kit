#!/usr/bin/env python3
"""Stop: a reply that recommends something must cite a source or say "não verifiquei".

Uses `last_assistant_message` from the Stop input (the transcript is a fallback; the desktop app stores
reply text outside the assistant entries). If the reply recommends (recomendo, recommend, sugiro,
"o certo é") but has no URL, no file:line and no "não verifiquei"/"not verified", it continues the turn once with
non-error feedback asking for the source (`additionalContext`, the docs' recommended form for guidance). `stop_hook_active` true means it already asked this turn, so it lets the reply through.

Next-step rule: each recommending word is judged on the sentence that follows it. The word is a next step, not a
claim, and needs no source, only when every part of that sentence (split at , ; : "e" "and" "depois" "then") is
either a study step (review, read, study, practice, do the exercises) or a step of the agent's own workflow (run the
tests or scripts/verify, open the PR, wait for the review or CI). Workflow steps need their object ("rodar os
testes", not bare "rodar") and allow only a short tail ("de novo", "antes do merge"), so "fazer deploy na Vercel" and
"rodar o build na Vercel" still fire. A price (R$, US$, reais, por mês) or a comparison (em vez de, melhor que,
faster) anywhere in that sentence voids the exemption. The reply still fires if any other recommending word in it is
not a next step.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RECOMMENDS = re.compile(
    r"(?<!não )(?<!nao )\b(recomendo|recomendaria|recomendad[oa]:|recomendação:|minha recomendação|sugiro|"
    r"sugestão:|o certo é|(I|I'd|I would|we) (recommend|suggest)|my recommendation|the right (call|move) is)", re.I)
SOURCE = re.compile(
    r"https?://|\b[\w./~-]+\.[A-Za-z][A-Za-z0-9]{0,5}:\d+|não verifiquei|nao verifiquei|"
    r"not verified|não testei", re.I)
_LEAD = r"(?:(?:que|that)\s+(?:voc[eê]\s+|vc\s+|you\s+)?|voc[eê]\s+|you\s+|to\s+|a\s+|o\s+)?"
_STUDY = (r"revis(?:ar|e|em|ão)|rev(?:er|eja)|rel(?:er|eia)|l(?:er|eia)|leitura|estud(?:ar|e|o)|pratic(?:ar|ando)|"
          r"pratique|(?:resolv(?:er|a)|(?:re)?(?:fazer|faça|faz))\s+(?:os\s+|as\s+|a\s+|o\s+)?"
          r"(?:exerc[íi]cios|quest[õo]es|lista|simulado)|exerc[íi]cios|review(?:ing)?|stud(?:y|ying)|"
          r"re-?read(?:ing)?|read(?:ing)?|practi[cs](?:e|ing)|(?:solv(?:e|ing)|(?:re)?do(?:ing)?)\s+the\s+"
          r"(?:exercises|problems)")
_WORKFLOW = (r"(?:(?:rodar|rode|roda|executar|execute|re-?run(?:ning)?|run(?:ning)?)\s+(?:de\s+novo\s+|again\s+)?"
             r"(?:os\s+|o\s+|a\s+|the\s+)?(?:testes?|tests?|scripts/verify|verify|lint|build|checks?|CI)|"
             r"(?:abrir|abra|open(?:ing)?)\s+(?:o\s+|um\s+|the\s+|a\s+)?(?:PR|pull\s+request)|"
             r"(?:esperar|espere|aguardar|aguarde|wait(?:ing)?\s+for)\s+(?:o\s+|a\s+|os\s+|the\s+)?"
             r"(?:review|revisão|CI|checks?|aprovação|approval))")
_TAIL = (r"(?:\s+(?:de\s+novo|again|localmente|locally|(?:antes|depois)\s+d[oa]\s+\S+|"
         r"(?:before|after)\s+(?:the\s+)?\S+))?")
STUDY_STEP = re.compile(_LEAD + r"(?:" + _STUDY + r")\b", re.I)
WORKFLOW_STEP = re.compile(_LEAD + _WORKFLOW + _TAIL + r"$", re.I)
CLAIM = re.compile(r"R\$|US\$|\bUSD\b|\$\s?\d|€|\bEUR\b|\breais\b|d[óo]lares|por\s+m[êe]s|/m[êe]s|per\s+month|"
                   r"em\s+vez\s+d|ao\s+inv[ée]s\s+d|instead\s+of|(?:melhor|pior)\s+(?:do\s+)?que|"
                   r"(?:better|worse|faster|cheaper|slower)\b|mais\s+(?:rápid|barat|lent|car)", re.I)
SENTENCE_END = re.compile(r"[.!?](?:\s|$)|\n")
PARTS = re.compile(r"[,;:]|\s(?:e|and|depois|then)\s", re.I)
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


def is_next_step(text: str, start: int) -> bool:
    """True when the sentence after a recommending word is only study or own-workflow steps (see the header)."""
    clause = text[start:start + 300].lstrip(" \t\n:*_-•")
    end = SENTENCE_END.search(clause)
    clause = clause[:end.start()] if end else clause
    if CLAIM.search(clause):
        return False
    parts = [p.strip(" *_`") for p in PARTS.split(clause)]
    parts = [p for p in parts if p]
    return bool(parts) and all(STUDY_STEP.match(p) or WORKFLOW_STEP.match(p) for p in parts)


def verdict(text: str) -> dict:
    text = text[-8000:]  # bound regex cost on huge replies (minified code, long path lists)
    if not SOURCE.search(text) and any(not is_next_step(text, m.end()) for m in RECOMMENDS.finditer(text)):
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
