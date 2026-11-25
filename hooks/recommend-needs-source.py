#!/usr/bin/env python3
"""Stop: a reply that recommends something must cite a source or say "não verifiquei".

Uses `last_assistant_message` from the Stop input (the transcript is a fallback; the desktop app stores
reply text outside the assistant entries). If the reply recommends (recomendo, recommend, sugiro,
"o certo é") but has no URL, no file:line and no "não verifiquei"/"not verified", it continues the turn once with
non-error feedback asking for the source (`additionalContext`, the docs' recommended form for guidance). `stop_hook_active` true means it already asked this turn, so it lets the reply through.

Next-step rule: each recommending word is judged on the sentence that follows it (a bullet list right after it
counts as one sentence). The word is a next step, not a claim, and needs no source, only when every part of that
sentence (split at , ; : / "e" "ou" "depois" "and" "or" "then") is one of:
- a study step on study material: a study verb (revisar, ler, fazer, resolver, estudar, praticar, review, read,
  study, practice) plus a material noun (capítulo, lista, exercícios, slides, simulado, chapter, exercises...), its
  numbers, where it comes from ("da lista", "do livro") and a short tail ("antes da prova"), and nothing else. A
  free topic is not material, so "estudar react porque é o mais usado" and "praticar com supabase" still fire;
- a step of the agent's own workflow: run the tests or scripts/verify, open the PR, wait for the review or CI, fix
  the review items, with only a short tail ("de novo", "no PR #16", "antes do merge", "do News Bot").
A price (R$, US$, reais, por mês) or a comparison (em vez de, melhor que, faster) anywhere in the sentence voids the
exemption, and so does a sentence with no end in sight. The reply still fires if any other recommending word in it is
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
_DET = r"(?:(?:o|a|os|as|d[oa]s?|n[oa]s?|esse|essa|este|esta|the|this|these)\s+)?"
_MATERIAL_WORDS = (r"cap(?:ítulo|itulo)?s?\.?|chapters?|se[cç](?:ão|ões)|sections?|listas?|exerc[íi]cios|exercises|"
                   r"quest[õo]es|questions|problems|slides|aulas?|lectures?|notas|notes|resumos?|summary|apostila|"
                   r"matéria|conteúdo|enunciado|simulado|material|flashcards|gabarito|teoria|theory")
_MATERIAL = r"(?:" + _MATERIAL_WORDS + r")\b"
_STUDY_VERB = (r"(?:revis(?:ar|e|em|ão)|rev(?:er|eja)|rel(?:er|eia)|l(?:er|eia)|leitura|(?:re)?(?:fazer|faça|faz)|"
               r"resolv(?:er|a)|review(?:ing)?|re-?read(?:ing)?|read(?:ing)?|(?:re)?do(?:ing)?|solv(?:e|ing))\s+")
_PURE_STUDY = r"(?:estud(?:ar|e)|pratic(?:ar|ando)|pratique|treinar|treine|stud(?:y|ying)|practi[cs](?:e|ing))\b"
_WORKFLOW = (r"(?:(?:rodar|rode|roda|executar|execute|re-?run(?:ning)?|run(?:ning)?)\s+(?:de\s+novo\s+|again\s+)?"
             + _DET + r"(?:testes?|tests?|scripts/verify|verify|lint|build|checks?|CI)|"
             r"(?:abrir|abra|open(?:ing)?)\s+(?:um\s+)?" + _DET + r"(?:PR|pull\s+request)|"
             r"(?:esperar|espere|aguardar|aguarde|wait(?:ing)?\s+for)\s+" + _DET
             + r"(?:reviews?|revis(?:ão|ões)|CI|checks?|aprovação|approval)|"
             r"(?:corrigir|corrija|fix(?:ing)?)\s+" + _DET + r"(?:itens|items|achados|findings|tudo|everything)"
             r"(?:\s+\d+(?:\s*(?:a|to|-)\s*\d+)?)?)")
_TAIL = (r"(?:\s+(?:de\s+novo|again|agora|now|localmente|locally|n[oa]\s+PR(?:\s+#?\d+)?|in\s+the\s+PR|"
         r"(?:antes|depois)\s+d[eoa]\s+\S+|(?:before|after)\s+(?:the\s+)?\S+|d[oa]s?\s+[^\s\d]+(?:\s+[^\s\d]+)?)){0,2}")
_NUMS = r"(?:\s+\d+[a-z]?(?:\.\d+)*(?:\s*(?:a|to|-)\s*\d+)?)"
_SOURCE_NOUN = r"(?:" + _MATERIAL_WORDS + r"|livro|book|unidade|unit|m[óo]dulo|module|semana|week|disciplina)\b"
_STUDY_TAIL = (_NUMS + r"?(?:\s+(?:d[oa]s?|of|from)\s+" + _DET + _SOURCE_NOUN + _NUMS + r"?)?"
               r"(?:\s+(?:de\s+novo|again|agora|now|(?:antes|depois)\s+d[eoa]\s+\S+|(?:before|after)\s+(?:the\s+)?\S+))?$")
_ANY_STUDY_VERB = r"(?:" + _STUDY_VERB + r"|" + _PURE_STUDY + r"\s+(?:(?:com|with|on|em|n[oa]s?)\s+)?)"
STUDY_STEP = re.compile(_LEAD + r"(?:" + _ANY_STUDY_VERB
                        + _DET + _MATERIAL + _STUDY_TAIL + r"|" + _DET + _MATERIAL + _NUMS + _STUDY_TAIL + r")", re.I)
WORKFLOW_STEP = re.compile(_LEAD + _WORKFLOW + _TAIL + r"$", re.I)
CLAIM = re.compile(r"R\$|US\$|\bUSD\b|\$\s?\d|€|\bEUR\b|\breais\b|d[óo]lares|por\s+m[êe]s|/m[êe]s|per\s+month|"
                   r"em\s+vez\s+d|ao\s+inv[ée]s\s+d|no\s+lugar\s+d|instead\s+of|(?:melhor|pior)\s+(?:do\s+)?que|"
                   r"(?:better|worse|faster|cheaper|slower)\b|mais\s+(?:rápid|barat|lent|car)", re.I)
SENTENCE_END = re.compile(r"[.!?](?=\s+[A-ZÀ-Ú]|\s*$)|\n")
BULLET = re.compile(r"\n[ \t\n]*(?:[-*•]|\d+[.)])[ \t]+")
MARKUP = re.compile(r"[*_`]")
NUMBERS = re.compile(r"\d+(?:\s*(?:a|to|-)\s*\d+)?$")
PARTS = re.compile(r"[,;:]|\s(?:e|and|ou|or|depois|then|/)\s", re.I)
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


def _is_step(part: str) -> bool:
    return bool(STUDY_STEP.match(part) or WORKFLOW_STEP.match(part))


def is_next_step(text: str, start: int) -> bool:
    """True when the sentence after a recommending word is only study or own-workflow steps (see the header)."""
    window = text[start:start + 600]
    clause = MARKUP.sub("", BULLET.sub("; ", window)).lstrip(" \t\n:-•;")
    end = SENTENCE_END.search(clause)
    if end:
        clause = clause[:end.start()]
    elif len(window) == 600:
        return False  # no sentence end within the window: judge it as a claim
    if CLAIM.search(clause):
        return False
    parts = [p.strip() for p in PARTS.split(clause)]
    parts = [p for p in parts if p and not NUMBERS.match(p)]  # "capítulos 3 e 4", "itens 1, 3 e 4"
    return bool(parts) and all(_is_step(p) for p in parts)


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
