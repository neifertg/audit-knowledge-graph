"""Rules every AI-written description must pass before it is stored (L-002, 010 AC-3)."""
import re
from functools import cache

from .names import load

ISSUE_OPENING = re.compile(r"^(.*?\bthat)\b")


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[&'./-][a-z0-9]+)*", text.lower())


@cache
def _deny() -> tuple:
    return tuple(tuple(tokens(e)) for e in load("deny_list"))


@cache
def _allowed_words() -> frozenset:
    terms = set()
    for list_name in ("systems", "vendors", "institution", "regulations", "titles", "allow_terms",
                      "first_names", "last_names"):
        terms |= set(load(list_name))
    return frozenset(w for term in terms for w in re.findall(r"[A-Za-z][\w/&'-]*", term))


def added_systems(text: str, draft: str) -> list[str]:
    return [s for s in load("systems") if s in text and s not in draft]


def denied(text: str) -> list[str]:
    words = tokens(text)
    return [" ".join(e) for e in _deny() if any(tuple(words[i:i + len(e)]) == e for i in range(len(words)))]


def stray_capitals(text: str) -> list[str]:
    words = []
    for sentence in re.split(r"(?<=[.!?])\s+|;\s+|:\s+", text):
        found = re.findall(r"[A-Za-z][\w/&'-]*", sentence)
        words += [t.removesuffix("'s") for t in found[1:] if t[0].isupper()]
    return sorted(set(words) - _allowed_words())


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def issue_opening(draft: str) -> str:
    """The opening words of a full-size issue draft ('Testing found that', ...)."""
    match = ISSUE_OPENING.match(draft)
    return match.group(1) if match else ""


def violations(file: str, draft: str, text: str) -> list[str]:
    """Reasons a rewrite may not be stored; empty when it passes."""
    reasons = []
    if not text.strip():
        reasons.append("empty text")
    extra = added_systems(text, draft)
    if extra:
        reasons.append(f"names systems its draft lacks: {', '.join(extra)}")
    if file == "control_erm":
        parts = sentences(text)
        if len(parts) != 1 or len(text.split()) > 30:
            reasons.append(f"ERM control must be one sentence of at most 30 words ({len(parts)} sentences, "
                           f"{len(text.split())} words)")
    if file == "issue":
        opening = issue_opening(draft)
        if opening and not text.startswith(opening):
            reasons.append(f"issue must begin with '{opening}'")
    names = denied(text)
    if names:
        reasons.append(f"real institution name: {', '.join(names)}")
    caps = stray_capitals(text)
    if caps:
        reasons.append(f"capitalized words not on any list: {', '.join(caps)}")
    return reasons
