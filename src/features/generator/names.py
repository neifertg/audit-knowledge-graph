"""Fictional name lists (INV-9). Every institution, person, vendor and system name comes from here."""
from functools import cache
from pathlib import Path

NAMES_DIR = Path(__file__).resolve().parent / "names"


@cache
def load(list_name: str) -> tuple[str, ...]:
    path = NAMES_DIR / f"{list_name}.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    return tuple(line.strip() for line in lines if line.strip() and not line.startswith("#"))
