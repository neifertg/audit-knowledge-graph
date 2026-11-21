"""Render the realism-review sample pack (`python -m akg sample-pack`).

One Markdown file for the owner: a review table to fill in, the full name lists, every entity's
rows (risks, controls and issues with templated and AI-written descriptions side by side),
relationships with names instead of IDs, and the answer key's reconciliation pairs.
"""
from pathlib import Path

from .generate import Dataset, build
from .names import load

ENTITY_ORDER = [
    "segment", "business_unit", "auditable_entity", "process", "system", "person", "regulation",
    "taxonomy_node_erm", "taxonomy_node_ia", "risk_erm", "risk_ia", "control_erm", "control_ia",
    "audit", "issue",
]
WITH_TEXT = {"risk_erm", "risk_ia", "control_erm", "control_ia", "issue"}
NAME_LISTS = ["institution", "first_names", "last_names", "titles", "systems", "vendors", "regulations"]


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(columns: list[str], rows: list) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(_cell(v) for v in row) + " |" for row in rows]
    return lines + [""]


def _labels(dataset: Dataset) -> dict[str, str]:
    labels = {}
    for table in dataset.tables.values():
        for col in ("name", "title"):
            if col in table.columns:
                i = table.columns.index(col)
                labels.update({row[0]: f"{row[i]} ({row[0]})" for row in table.rows})
                break
    return labels


def render_text(templated: Dataset, ai: Dataset | None, full: bool = False) -> str:
    institution = load("institution")[0]
    if full:
        # full size (007 AC-7, 010 AC-5): both descriptions side by side; the text choice is made
        counts = ", ".join(f"{len(templated.tables[n].rows)} {n}" for n in
                           ("auditable_entity", "risk_erm", "risk_ia", "control_erm", "control_ia"))
        out = [
            f"# Full-size pack: {institution} (synthetic)",
            "",
            f"The full-size bank ({counts}) for a realism skim: do the organization, taxonomies and risk "
            "registers read like a real US regional bank? Risks, controls and issues show the templated "
            "description beside the AI-written one the build uses by default (E1 child f).",
            "",
            "## Your review",
            "",
            "Mark each entity type realistic (yes / no) and add notes.",
            "",
        ]
        out += _table(["entity type", "realistic?", "notes"], [(name, "", "") for name in ENTITY_ORDER])
    else:
        out = [
            f"# Sample pack: {institution} (synthetic)",
            "",
            "This is a small slice of the generated bank (about 15 rows per entity) for one question: "
            "**do these records read like a real US regional bank's ERM and Internal Audit data?** "
            "Judge the wording and attributes of the rows. Population sizes, ratios and taxonomy breadth are "
            "set later (children b-e), so they are not under review here.",
            "",
            "Risks, controls and issues show two versions of each description: **templated** (built from "
            "hand-written phrases) and **AI-written** (generated once with Claude and committed). Pick one.",
            "",
            "## Your review",
            "",
            "Mark each entity type realistic (yes / no) and add notes. Record the verdict and text choice "
            "in `research/r2-synthetic-text-realism/decision.md`.",
            "",
        ]
        out += _table(["entity type", "realistic?", "notes"], [(name, "", "") for name in ENTITY_ORDER])
        out += ["**Text choice (templated / AI):** ____", ""]

    out += ["## Name lists", "", "Every institution, person, vendor and system name comes from these lists "
            "(INV-9). Check that none resembles a real institution or product.", ""]
    for list_name in NAME_LISTS:
        out += [f"**{list_name}:** " + "; ".join(load(list_name)), ""]

    out += ["## Entities", ""]
    ai_rows = {}
    if ai is not None:
        for name in WITH_TEXT:
            table = ai.tables[name]
            i = table.columns.index("description")
            ai_rows[name] = {row[0]: row[i] for row in table.rows}
    for name in ENTITY_ORDER:
        table = templated.tables[name]
        out += [f"### {name}", ""]
        if name in WITH_TEXT and ai is not None:
            i = table.columns.index("description")
            columns = table.columns[:i] + ["description (templated)", "description (AI)"] + table.columns[i + 1:]
            rows = [row[:i] + (row[i], ai_rows.get(name, {}).get(row[0], "(not generated)")) + row[i + 1:]
                    for row in table.rows]
            out += _table(columns, rows)
        else:
            out += _table(table.columns, table.rows)

    labels = _labels(templated)
    out += ["## How things connect", "", "Each relationship file, with names in place of IDs.", ""]
    for name, table in sorted(templated.tables.items()):
        if name in ENTITY_ORDER:
            continue
        rows = [tuple(labels.get(v, v) for v in row) for row in table.rows]
        out += [f"<details><summary>{name} ({len(rows)} rows)</summary>", ""]
        out += _table(table.columns, rows)
        out += ["</details>", ""]

    out += ["## Reconciliation pairs (answer key)", "",
            "Items the answer key says are the same underlying risk or control. Matching these is E2's job; "
            "here, check that the pairs look like the same thing described by two different teams.", ""]
    for kind in ("risk", "control"):
        clusters: dict[str, list] = {}
        for row in templated.answer_key[f"{kind}_clusters"].rows:
            if row[2] != "none":
                clusters.setdefault(row[2], []).append(f"{row[0]}: {labels.get(row[1], row[1])}")
        out += [f"### {kind}s", ""]
        out += _table(["cluster", "members"], [(c, "<br>".join(m)) for c, m in sorted(clusters.items())])
    return "\n".join(out)


def render(args) -> None:
    templated = build(args.seed, dict(args.count), "templated", size=args.size)
    ai = build(args.seed, dict(args.count), "ai", args.text_dir, args.size)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_text(templated, ai, full=args.size == "full"))
    print(f"wrote {path}")
