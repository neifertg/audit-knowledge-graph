"""The site-data export, `site.json`: what the page needs beyond rounds.json and scores.json (021).

    python -m src.features.site.export --out <loaded build>     rewrites src/features/site/data/site.json

Read-only on <build>/akg.sqlite (017's read-only connection and views) and the committed rounds.json;
never the answer key. Deterministic JSON: sorted keys, no paths, no timings.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from src.features.rounds import symmetry
from src.features.rounds.export import COMMITTED as ROUNDS_JSON
from src.features.rounds.runner import sqlite_connection

HERE = Path(__file__).parent
SITE_JSON = HERE / "data" / "site.json"


def top_system(rounds: dict) -> str:
    """Round 3's first row: the system whose dependent controls reach the most entities."""
    round3 = next(r for r in rounds["rounds"] if r["number"] == 3)
    return round3["rows"][0][0]


def subgraph(con, system_id: str) -> dict:
    q = lambda sql, *a: con.execute(sql, a).fetchall()
    system_name = q("SELECT name FROM system WHERE system_id = ?", system_id)[0][0]
    controls = {c for (c,) in q("SELECT control_id FROM depends_on WHERE system_id = ?", system_id)}
    mitigates = [(c, r) for c, r in q("SELECT control_id, risk_id FROM mitigates") if c in controls]
    risks = {r for _, r in mitigates}
    exposed = [(r, e) for r, e in q("SELECT risk_id, auditable_entity_id FROM exposed_to") if r in risks]
    entities = {e for _, e in exposed}
    owns = [(e, u) for u, e in q("SELECT business_unit_id, auditable_entity_id FROM business_unit_owns_auditable_entity")
            if e in entities]
    units = {u for _, u in owns}
    title = dict(q("SELECT control_id, title FROM control_erm UNION ALL SELECT control_id, title FROM control_ia"))
    title.update(q("SELECT risk_id, title FROM risk_erm UNION ALL SELECT risk_id, title FROM risk_ia"))
    title.update(q("SELECT auditable_entity_id, name FROM auditable_entity"))
    title.update(q("SELECT business_unit_id, name FROM business_unit"))
    nodes = ([{"id": system_id, "kind": "system", "label": system_name}]
             + [{"id": i, "kind": kind, "label": title[i]} for kind, ids in
                (("control", controls), ("risk", risks), ("entity", entities), ("unit", units)) for i in sorted(ids)])
    edges = sorted([{"source": system_id, "target": c, "kind": "depends_on"} for c in controls]
                   + [{"source": c, "target": r, "kind": "mitigates"} for c, r in set(mitigates)]
                   + [{"source": r, "target": e, "kind": "exposes"} for r, e in set(exposed)]
                   + [{"source": e, "target": u, "kind": "owned_by"} for e, u in set(owns)],
                   key=lambda e: (e["kind"], e["source"], e["target"]))
    per_unit = defaultdict(set)
    for e, u in owns:
        per_unit[u].add(e)
    by_unit = sorted(({"unit_id": u, "unit_name": title[u], "entities": len(es)} for u, es in per_unit.items()),
                     key=lambda x: (-x["entities"], x["unit_name"]))
    story = {"system_id": system_id, "system_name": system_name, "controls": len(controls),
             "controls_with_risks": len({c for c, _ in mitigates}), "risks": len(risks), "entities": len(entities),
             "units": len(units), "by_unit": by_unit}
    return {"nodes": nodes, "edges": edges}, story


def stories(con, rounds: dict) -> dict:
    by_number = {r["number"]: r for r in rounds["rounds"] + rounds["supporting"]}
    round6 = by_number[6]
    owners = by_number["owners"]["rows"]
    top = [row for row in owners if (row[1], row[2]) == (owners[0][1], owners[0][2])]
    names = dict(con.execute("SELECT person_id, name FROM person").fetchall())
    return {
        "repeat_finding": {"controls": len({row[0] for row in round6["rows"]}), "issues": round6["row_count"]},
        "owners": {"top": [{"person_id": row[0], "name": names[row[0]]} for row in top],
                   "key_controls": owners[0][1], "units": owners[0][2]},
    }


def document(build_dir: Path, rounds: dict | None = None) -> dict:
    rounds = rounds or json.loads(ROUNDS_JSON.read_text(encoding="utf-8"))
    con = sqlite_connection(build_dir)
    try:
        graph, blast = subgraph(con, top_system(rounds))
        doc = {"subgraph": graph, "blast_radius": blast, "symmetry": symmetry.table(), **stories(con, rounds)}
    finally:
        con.close()
    return doc


def render(doc: dict) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.features.site.export")
    parser.add_argument("--out", type=Path, required=True, help="a loaded build (seed 42 for the committed copy)")
    args = parser.parse_args(argv)
    SITE_JSON.parent.mkdir(parents=True, exist_ok=True)
    SITE_JSON.write_text(render(document(args.out)), encoding="utf-8", newline="\n")
    print(f"wrote {SITE_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
