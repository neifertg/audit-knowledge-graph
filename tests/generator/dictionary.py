"""Parse the data dictionary in src/features/generator/README.md."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "src" / "features" / "generator" / "README.md"
NAMES = ROOT / "src" / "features" / "generator" / "names"
TYPES = {"id", "text", "enum", "int", "date"}


def parse() -> dict[str, list[tuple[str, str, str]]]:
    """{'risk_erm.csv': [(column, type, values), ...], 'answer_key/...csv': [...]}"""
    spec: dict[str, list] = {}
    current = None
    for line in README.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^### `([^`]+\.csv)`\s*$", line)
        if heading:
            current = heading.group(1)
            spec[current] = []
            continue
        row = re.match(r"^\| `([^`]+)` \| (\w+) \| (.*) \|\s*$", line)
        if row and current:
            spec[current].append(row.groups())
    return spec


def name_list(list_name: str) -> set[str]:
    if list_name == "people":
        first, last = name_list("first_names"), name_list("last_names")
        return {f"{f} {l}" for f in first for l in last}
    lines = (NAMES / f"{list_name}.txt").read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[&'./-][a-z0-9]+)*", text.lower())


def denied_in(text: str, deny: list[list[str]]) -> list[str]:
    """Deny-list entries that occur in `text` as a whole-token sequence."""
    words = tokens(text)
    hits = []
    for entry in deny:
        n = len(entry)
        if any(words[i:i + n] == entry for i in range(len(words) - n + 1)):
            hits.append(" ".join(entry))
    return hits


def deny_entries() -> list[list[str]]:
    return [tokens(e) for e in name_list("deny_list")]
