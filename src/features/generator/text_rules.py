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


CAPITALIZED = re.compile(r"[A-Za-z][\w/&'-]*")
# Ordinary capitalized words the check allows but the prompt does not list (adding them to
# allow_terms.txt would change the full prompt version and make all stored full-size text stale).
RULE_ONLY_WORDS = ("ID", "IDs", "January", "February", "March", "April", "May", "June", "July", "August",
                   "September", "October", "November", "December")


@cache
def _allowed_words() -> frozenset:
    """Name lists, the domain allow-list, and the bank's own published names (segments, business
    units, auditable entities, processes, taxonomy nodes): the AI may use these, nothing invented."""
    from . import library as lib

    terms = set()
    for list_name in ("systems", "vendors", "institution", "regulations", "titles", "allow_terms",
                      "first_names", "last_names"):
        terms |= set(load(list_name))
    terms |= set(lib.SEGMENTS) | set(lib.FULL_BUSINESS_UNITS) | set(lib.FULL_AUDITABLE_ENTITIES)
    terms |= set(lib.FULL_PROCESSES)
    terms |= {name for path in lib.FULL_ERM_TAXONOMY + lib.FULL_IA_TAXONOMY for name in path}
    terms |= set(RULE_ONLY_WORDS)
    return frozenset(w for term in terms for w in CAPITALIZED.findall(term))


def added_systems(text: str, draft: str) -> list[str]:
    return [s for s in load("systems") if s in text and s not in draft]


def denied(text: str) -> list[str]:
    words = tokens(text)
    return [" ".join(e) for e in _deny() if any(tuple(words[i:i + len(e)]) == e for i in range(len(words)))]


def stray_capitals(text: str, draft: str = "") -> list[str]:
    """Capitalized words (not sentence-initial) that are neither allowed nor in the item's own draft."""
    words = []
    for sentence in re.split(r"(?<=[.!?])\s+|;\s+|:\s+", text):
        found = CAPITALIZED.findall(sentence)
        words += [t.removesuffix("'s") for t in found[1:] if t[0].isupper()]
    allowed = _allowed_words() | set(CAPITALIZED.findall(draft))
    # a hyphenated word ('Board-approved') passes when each capitalized part is allowed
    return sorted(w for w in set(words)
                  if w not in allowed and not all(p in allowed for p in w.split("-") if p[:1].isupper()))


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
    caps = stray_capitals(text, draft)
    if caps:
        reasons.append(f"capitalized words not on any list: {', '.join(caps)}")
    return reasons
