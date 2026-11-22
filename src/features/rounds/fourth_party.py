"""Round 5's fourth-party register: which vendors rely on which (E3 child d, change 018).

    python -m src.features.rounds.fourth_party      (re)writes fourth_party.csv

Deterministic: for each vendor of the generator's fictional vendor list (INV-9) in name order,
random.Random('fourth-party-v1') draws k from (0, 0, 1) and then k other vendors, sorted.
The vendor round 5 asks about is the one most vendors rely on, directly or through others,
ties by name.
"""
import csv
import io
import random
from pathlib import Path

HERE = Path(__file__).parent
REGISTER = HERE / "fourth_party.csv"
VENDORS = HERE.parents[1] / "features" / "generator" / "names" / "vendors.txt"
TAG = "fourth-party-v1"
COLUMNS = ("vendor", "relies_on")


def vendor_names() -> list[str]:
    lines = VENDORS.read_text(encoding="utf-8").splitlines()
    return sorted(line.strip() for line in lines if line.strip() and not line.strip().startswith("#"))


def generate() -> list[dict]:
    vendors, rng, rows = vendor_names(), random.Random(TAG), []
    for vendor in vendors:
        k = rng.choice((0, 0, 1))
        for other in sorted(rng.sample([v for v in vendors if v != vendor], k)):
            rows.append({"vendor": vendor, "relies_on": other})
    return rows


def render(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def read_register(path: Path = REGISTER) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return [{"vendor": r["vendor"], "relies_on": r["relies_on"]} for r in csv.DictReader(f)]


def upstream(vendor: str, rows: list[dict]) -> set[str]:
    """Every other vendor that relies on `vendor`, directly or through others."""
    relies_on = {}
    for r in rows:
        relies_on.setdefault(r["vendor"], set()).add(r["relies_on"])
    seen, todo = set(), [vendor]
    while todo:
        target = todo.pop()
        for v, others in relies_on.items():
            if target in others and v not in seen and v != vendor:
                seen.add(v)
                todo.append(v)
    return seen


def most_relied_on(rows: list[dict]) -> str:
    return sorted(vendor_names(), key=lambda v: (-len(upstream(v, rows)), v))[0]


if __name__ == "__main__":
    REGISTER.write_text(render(generate()), encoding="utf-8", newline="")
    print(f"wrote {REGISTER} ({len(generate())} rows)")
