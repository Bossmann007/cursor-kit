#!/usr/bin/env python3
"""Stop: a reply that recommends something must cite a source or say "não verifiquei".

Uses `last_assistant_message` from the Stop input (the transcript is a fallback; the desktop app stores
reply text outside the assistant entries). If the reply recommends (recomendo, recommend, sugiro,
"o certo é") but has no URL, no file:line and no "não verifiquei"/"not verified", it continues the turn once with
non-error feedback asking for the source (`additionalContext`, the docs' recommended form for guidance). `stop_hook_active` true means it already asked this turn, so it lets the reply through.

Next-step rule: each recommending word is judged on the action that directly follows it, in the same sentence.
If that action is a study step (review, read, study, practice, solve, do the exercises) or a step of the agent's own
workflow (run the tests or scripts/verify, open the PR, wait for the review or CI), the word is a next step, not a
claim, and needs no source. Workflow verbs only count with their object ("rodar os testes", not bare "rodar"), so
"fazer deploy na Vercel" or "abrir conta na AWS" still fire. A price in that sentence (R$, US$, $, EUR) voids the
exemption. The reply still fires if any other recommending word in it is not a next step. Only the first action
after the word is judged: "sugiro revisar X e usar Supabase" passes.
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
_LEAD = r"[\s:*_-]*(?:(?:que|that)\s+(?:voc[eê]\s+|vc\s+|you\s+)?|voc[eê]\s+|you\s+|to\s+|a\s+|o\s+)?"
_STUDY = (r"revis(?:ar|e|em|ão)|rev(?:er|eja)|rel(?:er|eia)|l(?:er|eia)\b|leitura|estud(?:ar|e|o)|pratic(?:ar|ando)|pratique|"
          r"(?:resolv(?:er|a)|(?:re)?(?:fazer|faça|faz))\s+(?:os\s+|as\s+|a\s+|o\s+)?(?:exerc[íi]cios|quest[õo]es|lista|simulado)|"
          r"exerc[íi]cios|review(?:ing)?|stud(?:y|ying)|re-?read(?:ing)?|read(?:ing)?|practi[cs](?:e|ing)|"
          r"(?:solv(?:e|ing)|(?:re)?do(?:ing)?)\s+the\s+(?:exercises|problems)")
_WORKFLOW = (r"(?:rodar|rode|roda|executar|execute|re-?run(?:ning)?|run(?:ning)?)\s+(?:de\s+novo\s+|again\s+)?"
             r"(?:os\s+|o\s+|a\s+|the\s+)?(?:testes?|tests?|scripts/verify|verify|lint|build|checks?|CI)\b|"
             r"(?:abrir|abra|open(?:ing)?)\s+(?:o\s+|um\s+|the\s+|a\s+)?(?:PR|pull\s+request)\b|"
             r"(?:esperar|espere|aguardar|aguarde|wait(?:ing)?\s+for)\s+(?:o\s+|a\s+|os\s+|the\s+)?"
             r"(?:review|revisão|CI|checks?|aprovação|approval)\b")
NEXT_STEP = re.compile(_LEAD + r"(?:(?:" + _STUDY + r")\b|" + _WORKFLOW + r")", re.I)
PRICE = re.compile(r"R\$|US\$|\$\s?\d|€|\bEUR\b", re.I)
SENTENCE_END = re.compile(r"[.!?](?:\s|$)|\n")
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
    """True when the action right after a recommending word is a study or own-workflow step (see the header)."""
    clause = text[start:start + 300]
    end = SENTENCE_END.search(clause)
    clause = clause[:end.start()] if end else clause
    return bool(NEXT_STEP.match(clause)) and not PRICE.search(clause)


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
