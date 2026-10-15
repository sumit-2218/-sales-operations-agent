"""Guards against unsupported claims in model output. Pure standard library.

The model is only allowed to restate facts present in the context it was given.
Numbers, e-mail addresses and URLs that do not appear in that context are rejected,
as are phrases that claim prior contact or research the sender never did.
"""
from __future__ import annotations

import json
import re

FORBIDDEN_OUTREACH_PHRASES = [
    "as we discussed", "as discussed", "our previous conversation", "our last conversation",
    "last time we spoke", "we spoke", "we met", "we connected", "great to meet",
    "i noticed", "i saw that", "i came across", "i've been following", "i have been following",
    "i researched", "i did some research", "after researching", "my research", "our research",
    "congratulations on", "our clients include", "our customers include", "trusted by",
    "guaranteed", "guarantee", "proven results", "case study",
]
NUM_RE = re.compile(r"\d[\d,\.]*\d|\d")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s)\]\"']+", re.I)
DURATION_RE = re.compile(r"^\s*-?\s*(minutes?|mins?|min)\b", re.I)


def _digits(tok: str) -> str:
    return re.sub(r"[,\.]", "", tok)


def _numbers_with_context(text: str):
    text = re.sub(r"(?m)^\s*\d+[\.\)]\s", "", text)  # list enumerators
    for m in NUM_RE.finditer(text):
        yield m.group(0), text[m.end():m.end() + 12]


def find_unsupported(text: str, context: str) -> list[str]:
    """Return tokens (numbers/emails/urls) in `text` that do not occur in `context`."""
    ctx_low = context.lower()
    ctx_nums = {_digits(t) for t, _ in _numbers_with_context(context)}
    ctx_trim = {n.rstrip("0") or "0" for n in ctx_nums}
    problems: list[str] = []
    for tok, after in _numbers_with_context(text):
        if DURATION_RE.match(after):  # "15 minutes" describes the meeting, not the company
            continue
        d = _digits(tok)
        if d in ctx_nums or (d.rstrip("0") or "0") in ctx_trim:
            continue
        problems.append(tok)
    for m in EMAIL_RE.findall(text):
        if m.lower() not in ctx_low:
            problems.append(m)
    for m in URL_RE.findall(text):
        if m.lower().rstrip(".,;") not in ctx_low:
            problems.append(m)
    return sorted(set(problems))


def find_forbidden_phrases(text: str, phrases: list[str] | None = None) -> list[str]:
    low = text.lower().replace("\u2019", "'")
    return [p for p in (phrases or FORBIDDEN_OUTREACH_PHRASES) if p in low]


def extract_json(text: str):
    """Parse a JSON object from model output, tolerating code fences / surrounding prose."""
    if text is None:
        raise ValueError("empty response")
    s = text.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    s2 = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.I)
    try:
        return json.loads(s2)
    except json.JSONDecodeError:
        pass
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b > a:
        return json.loads(s[a:b + 1])
    raise ValueError("response did not contain a JSON object")
