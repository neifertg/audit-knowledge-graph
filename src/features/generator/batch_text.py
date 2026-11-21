"""Full-size AI text in one Message Batch (E1 child f, 010). Run by hand, never by the build.

    .venv\\Scripts\\python -m src.features.generator.batch_text estimate
    .venv\\Scripts\\python -m src.features.generator.batch_text submit --budget 10
    .venv\\Scripts\\python -m src.features.generator.batch_text collect --batch <id>
    .venv\\Scripts\\python -m src.features.generator.batch_text resubmit --budget 10

The budget is cumulative over research/r2-synthetic-text-realism/cost_log.md and fails closed:
a `submitting` row is written before any API call and counts as spend; a missing log, an
unparseable row or an unknown status refuses the run. Every API call goes through a client
passed in by the caller (a fake in tests); only `main` builds a real one.
"""
import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import text_rules
from .generate import FULL_AI_TEXT_FILE, build, full_text_hash
from .prompts import MODEL, VOICE, system_prompt

ROOT = Path(__file__).resolve().parents[3]
TEXT_DIR = Path(__file__).resolve().parent / "text"
COST_LOG = ROOT / "research" / "r2-synthetic-text-realism" / "cost_log.md"
BATCH_DIR = ROOT / "research" / "r2-synthetic-text-realism" / "batches"

PRICE_IN, PRICE_OUT = 2.0 / 1e6, 10.0 / 1e6   # claude-opus-5-5 per token at batch prices
MEASURED_IN, MEASURED_OUT = 971, 199            # measured per item, 2026-11-20 (R2)
MARGIN = 1.25
MAX_TOKENS, RETRY_MAX_TOKENS = 450, 900         # max_tokens includes thinking, which cannot be turned off
HEADER = "| batch_id | files | items | estimated_usd | actual_usd | status |"
STATUSES = ("submitting", "submitted", "collected", "rejected")
FAILED_RESULT_TYPES = ("errored", "expired", "canceled")
DEFINITE_REJECTION = (400, 401, 403, 404, 413, 422)


class BudgetError(Exception):
    pass


# --- cost log ------------------------------------------------------------------------------

@dataclass
class Row:
    batch_id: str
    files: str
    items: int
    estimated: float
    actual: float | None
    status: str


def parse_log(path: Path = COST_LOG) -> tuple[list[str], list[Row]]:
    """(preface lines, rows). Fails closed on a missing log, a bad row or an unknown status."""
    if not path.exists():
        raise BudgetError(f"cost log missing: {path} (it must exist, even if empty)")
    lines = path.read_text(encoding="utf-8").splitlines()
    if HEADER not in lines:
        raise BudgetError(f"cost log has no table header: {HEADER}")
    head = lines.index(HEADER)
    rows = []
    for line in lines[head + 2:]:
        if not line.strip():
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        try:
            batch_id, files, items, est, actual, status = cells
            row = Row(batch_id, files, int(items), float(est), float(actual) if actual else None, status)
        except ValueError as error:
            raise BudgetError(f"unparseable cost log row: {line!r}") from error
        if row.status not in STATUSES:
            raise BudgetError(f"unknown cost log status {row.status!r} in row {line!r}")
        rows.append(row)
    return lines[:head + 2], rows


def spend(rows: list[Row]) -> float:
    """Actual cost where collected, nothing for rejected batches, the estimate otherwise."""
    total = 0.0
    for row in rows:
        if row.status == "collected":
            total += row.actual or 0.0
        elif row.status != "rejected":
            total += row.estimated
    return total


def write_log(preface: list[str], rows: list[Row], path: Path = COST_LOG) -> None:
    body = [f"| {r.batch_id} | {r.files} | {r.items} | {r.estimated:.4f} | "
            f"{'' if r.actual is None else f'{r.actual:.4f}'} | {r.status} |" for r in rows]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(preface + body) + "\n")


# --- items ----------------------------------------------------------------------------------

@dataclass
class Item:
    key: str
    file: str
    draft: str
    title: str
    voice: str
    opening: str
    expected_hash: str


def full_items(seed: int = 42) -> list[Item]:
    dataset = build(seed, size="full", text="templated")
    rows = {name: {r[0]: dict(zip(t.columns, r)) for r in t.rows} for name, t in dataset.tables.items()}
    items = []
    for ti in dataset.text_items:
        row = rows[ti.file][ti.item_id]
        voice = VOICE[ti.file].format(source=row.get("source", ""))
        opening = text_rules.issue_opening(ti.templated) if ti.file == "issue" else ""
        items.append(Item(ti.key, ti.file, ti.templated, row["title"], voice, opening, full_text_hash(ti.input_hash)))
    return items


def load_text(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {e["key"]: e for e in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if e}


def save_text(path: Path, entries: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for key in sorted(entries):
            f.write(json.dumps(entries[key], ensure_ascii=False, sort_keys=True) + "\n")


def pending(items: list[Item], existing: dict[str, dict]) -> list[Item]:
    return [i for i in items if i.key not in existing or existing[i.key]["input_hash"] != i.expected_hash]


def custom_id(key: str) -> str:
    """Batch custom IDs allow only [a-zA-Z0-9_-]{1,64}; internal keys contain ':' and '#'."""
    return "k" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:40]


def estimate(items: list[Item], max_tokens: int | None = None) -> dict[str, float]:
    """Per-file estimate in USD (with margin); with max_tokens, the worst case at that cap."""
    out_tokens = max_tokens if max_tokens else MEASURED_OUT
    per_item = (MEASURED_IN * PRICE_IN + out_tokens * PRICE_OUT) * (1 if max_tokens else MARGIN)
    by_file: dict[str, float] = {}
    for item in items:
        by_file[item.file] = by_file.get(item.file, 0.0) + per_item
    return by_file


def request(item: Item, max_tokens: int, note: str = "") -> dict:
    content = f"Author: {item.voice}.\nTitle: {item.title}\nDraft: {item.draft}"
    if item.opening:
        content += f"\nOpening: {item.opening}"
    if note:
        content += f"\n{note}"
    return {"custom_id": custom_id(item.key),
            "params": {"model": MODEL, "max_tokens": max_tokens, "output_config": {"effort": "low"},
                       "system": system_prompt(full=True), "messages": [{"role": "user", "content": content}]}}


# --- submit and collect ------------------------------------------------------------------------

def submit(client_factory, items: list[Item], budget: float, attempt: int = 1, notes: dict | None = None,
           log: Path = COST_LOG, batch_dir: Path = BATCH_DIR) -> str:
    """Check the budget, log the estimate, then submit one batch. Returns the batch ID."""
    preface, rows = parse_log(log)
    max_tokens = MAX_TOKENS if attempt == 1 else RETRY_MAX_TOKENS
    by_file = estimate(items, None if attempt == 1 else max_tokens)  # a resubmission is priced at its worst case
    cost = sum(by_file.values())
    already = spend(rows)
    if already + cost > budget:
        raise BudgetError(f"refused: spend so far ${already:.2f} + this run ${cost:.2f} exceeds the ${budget:.2f} budget")
    placeholder = "pending-" + hashlib.sha256("|".join(sorted(i.key for i in items)).encode()).hexdigest()[:12]
    row = Row(placeholder, ",".join(sorted(by_file)), len(items), cost, None, "submitting")
    rows.append(row)
    write_log(preface, rows, log)
    client = client_factory()  # only now: secrets are read and a client created after the budget check
    requests = [request(i, max_tokens, (notes or {}).get(i.key, "")) for i in items]
    try:
        batch = client.messages.batches.create(requests=requests)
    except Exception as error:
        status = getattr(error, "status_code", None)
        if status in DEFINITE_REJECTION:
            row.status = "rejected"  # the API refused the batch outright: nothing was charged
            write_log(preface, rows, log)
        raise
    row.batch_id, row.status = batch.id, "submitted"
    write_log(preface, rows, log)
    batch_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / f"{batch.id}.json").write_text(json.dumps(
        {"attempt": attempt, "requests": {custom_id(i.key): i.key for i in items}}, indent=1, sort_keys=True),
        encoding="utf-8", newline="\n")
    return batch.id


def collect(client_factory, batch_id: str, items: list[Item], text_path: Path, log: Path = COST_LOG,
            batch_dir: Path = BATCH_DIR) -> dict:
    """Store passing results (matched by custom ID), log actual cost, return failures and anomalies."""
    client = client_factory()
    status = client.messages.batches.retrieve(batch_id).processing_status
    if status != "ended":
        return {"status": status}
    meta = json.loads((batch_dir / f"{batch_id}.json").read_text(encoding="utf-8"))
    expected = meta["requests"]
    by_key = {i.key: i for i in items}
    entries = load_text(text_path)
    failures, unknown, seen = {}, [], set()
    tokens_in = tokens_out = 0
    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        if cid not in expected:
            unknown.append(cid)
            continue
        seen.add(cid)
        key = expected[cid]
        item = by_key[key]
        kind = result.result.type
        if kind in FAILED_RESULT_TYPES:
            failures[key] = f"result {kind}"
            continue
        message = result.result.message
        tokens_in += message.usage.input_tokens
        tokens_out += message.usage.output_tokens
        if message.stop_reason in ("refusal", "max_tokens"):
            failures[key] = f"stop_reason {message.stop_reason}"
            continue
        text = " ".join(" ".join(b.text for b in message.content if b.type == "text").split())
        reasons = text_rules.violations(item.file, item.draft, text)
        if reasons:
            failures[key] = "; ".join(reasons)
            continue
        entries[key] = {"key": key, "input_hash": item.expected_hash, "text": text}
    missing = sorted(expected[c] for c in expected if c not in seen)
    for key in missing:
        failures[key] = "no result returned"
    save_text(text_path, entries)
    preface, rows = parse_log(log)
    for row in rows:
        if row.batch_id == batch_id:
            row.actual, row.status = tokens_in * PRICE_IN + tokens_out * PRICE_OUT, "collected"
    write_log(preface, rows, log)
    meta["failures"] = failures
    (batch_dir / f"{batch_id}.json").write_text(json.dumps(meta, indent=1, sort_keys=True), encoding="utf-8",
                                                newline="\n")
    return {"status": "ended", "stored": len(seen) - len(failures) + len(missing), "failures": failures,
            "unknown": unknown, "missing": missing, "tokens": (tokens_in, tokens_out)}


def failures_to_retry(batch_dir: Path = BATCH_DIR) -> tuple[dict, dict]:
    """(first-attempt failures to resubmit, second-attempt failures that block) from collected batches."""
    retry, blocked = {}, {}
    for path in sorted(batch_dir.glob("*.json")):
        meta = json.loads(path.read_text(encoding="utf-8"))
        target = retry if meta.get("attempt") == 1 else blocked
        target.update(meta.get("failures", {}))
    for key in blocked:
        retry.pop(key, None)
    return retry, blocked


# --- command line ---------------------------------------------------------------------------------

def _real_client():
    import anthropic

    from .write_text import api_key

    return anthropic.Anthropic(api_key=api_key())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="batch_text")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("estimate")
    for name in ("submit", "resubmit"):
        sub.add_parser(name).add_argument("--budget", type=float, required=True)
    sub.add_parser("collect").add_argument("--batch", required=True)
    args = parser.parse_args(argv)

    text_path = TEXT_DIR / FULL_AI_TEXT_FILE
    items = full_items()
    todo = pending(items, load_text(text_path))
    if args.command == "estimate":
        by_file = estimate(todo)
        _, rows = parse_log()
        for file, usd in sorted(by_file.items()):
            print(f"{file:12} ${usd:.2f}")
        print(f"{len(todo)} items, estimate ${sum(by_file.values()):.2f}, "
              f"worst case ${sum(estimate(todo, MAX_TOKENS).values()):.2f}, spend so far ${spend(rows):.2f}")
        return 0
    try:
        if args.command == "submit":
            print("submitted batch", submit(_real_client, todo, args.budget))
        elif args.command == "resubmit":
            retry, blocked = failures_to_retry()
            again = [i for i in todo if i.key in retry]
            notes = {k: f"Your previous attempt was rejected because: {reason}. Fix that." for k, reason in retry.items()}
            for key, reason in sorted(blocked.items()):
                print(f"BLOCKED (failed twice): {key}: {reason}")
            if again:
                print("resubmitted batch", submit(_real_client, again, args.budget, attempt=2, notes=notes))
        else:
            outcome = collect(_real_client, args.batch, items, text_path)
            print(json.dumps({k: v for k, v in outcome.items() if k != "failures"}, indent=1))
            for key, reason in sorted(outcome.get("failures", {}).items()):
                print(f"failed: {key}: {reason}")
    except BudgetError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
