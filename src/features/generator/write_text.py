"""Generate the AI-written descriptions once and commit them (R2). Run by hand, never by the build.

    .venv\\Scripts\\python -m src.features.generator.write_text            # missing or stale items only
    .venv\\Scripts\\python -m src.features.generator.write_text --only risk_ia:wire_fraud

Reads the Anthropic key at runtime from ~/.claude/secrets.yaml (anthropic.api_key) and never
prints it. Output: text/ai_text.jsonl, one {key, input_hash, text} per line, sorted by key.
Each entry's input_hash ties it to the templated inputs, so the build refuses stale text.
"""
import argparse
import json
import sys
from pathlib import Path

from .generate import AI_TEXT_FILE, build
from .names import load

TEXT_DIR = Path(__file__).resolve().parent / "text"
MODEL = "claude-opus-5-5"

VOICE = {
    "risk_erm": "an ERM risk register (RCSA) risk statement: one or two sentences in cause, event, impact form",
    "risk_ia": "an Internal Audit universe entry: one or two sentences naming the risk area and what the audit "
               "of it covers",
    "control_erm": "an ERM RCSA control description: one short, high-level sentence written by the business, "
                   "with no step-by-step detail",
    "control_ia": "an Internal Audit risk and control matrix (RCM) control description: two to four sentences "
                  "saying who performs it, what they do, when, and what evidence is kept",
    "issue": "an issue description recorded by {source}: one to three sentences stating the condition found",
}


def system_prompt() -> str:
    proper = ", ".join(load("systems") + load("allow_terms"))
    return (
        "You write record text for a fictional US regional bank's risk and audit data. Rewrite the draft "
        "you are given so it reads like a real record written by the stated author.\n"
        "Rules:\n"
        "- Keep every fact in the draft: numbers, thresholds, systems, roles and timeframes. You may reword, "
        "reorder and add plausible operational detail.\n"
        "- Add no new names of people, companies, vendors, products, systems, laws or places. Mention a "
        "system only if the draft names it.\n"
        f"- The only capitalized terms you may use, other than the first word of a sentence, are: {proper}.\n"
        "- Do not reuse any full sentence from the draft.\n"
        "- Plain prose only: no headings, lists, quotation marks or preamble. Reply with the rewritten text "
        "and nothing else."
    )


def api_key() -> str:
    import yaml

    path = Path.home() / ".claude" / "secrets.yaml"
    secrets = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    key = (secrets.get("anthropic") or {}).get("api_key")
    if not key:
        raise SystemExit(f"no anthropic.api_key in {path}")
    return key


def added_systems(text: str, draft: str) -> list[str]:
    """Systems the rewrite names that its draft does not (not allowed)."""
    return [s for s in load("systems") if s in text and s not in draft]


def rewrite(client, voice: str, title: str, draft: str, attempts: int = 3) -> str:
    note = ""
    for _ in range(attempts):
        text = _rewrite_once(client, voice, title, draft, note)
        extra = added_systems(text, draft)
        if not extra:
            return text
        note = f"\nYour last attempt named {', '.join(extra)}, which the draft does not mention. Do not name it."
    raise RuntimeError(f"rewrite kept naming systems absent from the draft: {extra}")


def _rewrite_once(client, voice: str, title: str, draft: str, note: str) -> str:
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=system_prompt(),
        messages=[{"role": "user", "content": f"Author: {voice}.\nTitle: {title}\nDraft: {draft}{note}"}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"refused: {response.stop_details}")
    text = " ".join(b.text for b in response.content if b.type == "text").strip()
    return " ".join(text.split())  # one line, single spaces


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="write_text")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--only", action="append", default=[], help="regenerate this key (repeatable)")
    parser.add_argument("--file", action="append", default=[], help="regenerate every item of this file")
    args = parser.parse_args(argv)

    import anthropic

    dataset = build(args.seed)
    path = TEXT_DIR / AI_TEXT_FILE
    existing = {}
    if path.exists():
        existing = {e["key"]: e for e in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if e}
    rows = {name: {r[0]: dict(zip(t.columns, r)) for r in t.rows} for name, t in dataset.tables.items()}

    todo = [i for i in dataset.text_items
            if i.key in args.only or i.file in args.file or i.key not in existing or existing[i.key]["input_hash"] != i.input_hash]
    print(f"{len(todo)} of {len(dataset.text_items)} items to write")
    client = anthropic.Anthropic(api_key=api_key())
    entries = {i.key: existing[i.key] for i in dataset.text_items if i.key in existing}
    for n, item in enumerate(todo, 1):
        row = rows[item.file][item.item_id]
        voice = VOICE[item.file].format(source=row.get("source", ""))
        try:
            text = rewrite(client, voice, row["title"], item.templated)
        except anthropic.APIError as error:
            print(f"{item.key}: API error {type(error).__name__}; stopping, progress saved", file=sys.stderr)
            break
        except RuntimeError as error:
            print(f"{item.key}: {error}; skipped", file=sys.stderr)
            continue
        entries[item.key] = {"key": item.key, "input_hash": item.input_hash, "text": text}
        print(f"[{n}/{len(todo)}] {item.key}")
        _save(path, entries)
    _save(path, entries)
    return 0


def _save(path: Path, entries: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for key in sorted(entries):
            f.write(json.dumps(entries[key], ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    sys.exit(main())
