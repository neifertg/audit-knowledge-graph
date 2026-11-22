"""The rounds export, `rounds.json`: the single file E4's page reads (E3 child d, change 018).

    python -m src.features.rounds.export     regenerate the committed src/features/rounds/rounds.json

`akg rounds` (and `akg build`, step 5) writes `<out>/rounds.json` with whatever engines ran. The
committed copy needs Neo4j: this command builds the published bank (seed 42, full, AI text) in a
temporary directory, loads both stores, runs every round and writes it.

Deterministic JSON: sorted keys, no timings (no speed claims, a GOALS non-goal), no filesystem
paths. Scenario outcomes are claims verified by named tests, because only tests read the answer key.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from . import oracle, verdict
from .registry import ALL, REGISTER, STALE_CUTOFF, VIEWS

HERE = Path(__file__).parent
COMMITTED = HERE / "rounds.json"
WEIGHTS = HERE.parent / "reconciliation" / "weights.json"
PUBLISHED_SEED = 42
ROWS_SHOWN = 20
RULE = {
    "score": "clauses + steps + 5 * moving_parts",
    "weight": verdict.WEIGHT,
    "margin": verdict.MARGIN,
    "verdict": "SQL when SQL's score times 1.25 is at most Cypher's; graph the other way round; close otherwise",
    "margin_definition": "max(score) - 1.25 * min(score); zero or more names a winner, negative is close",
    "counting": [
        "clauses: clause keywords; JOIN is not a clause (a join counts once, as a step); OPTIONAL MATCH is a clause",
        "steps: SQL FROM/JOIN targets minus one; Cypher relationship patterns, *n and *m..n counting n hops",
        "moving_parts: extra SELECTs (CTE, subquery, union branch) or Cypher WITH stages, subqueries and "
        "UNION; recursion once per side (RECURSIVE, or an unbounded *); writes and DDL",
        "a round with setup is scored as setup plus query",
    ],
}


def code_lines(text: str, marker: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip() and not line.strip().startswith(marker))


def weights_fingerprint() -> str:
    return json.loads(WEIGHTS.read_text(encoding="utf-8"))["fingerprint"]


def document(results, build_dir: Path, seed: int | None) -> dict:
    from src.features.stores.neo4j_store import reconciled_checksum

    from .runner import comparable

    expected = oracle.answers(build_dir)
    rounds, supporting = [], []
    for res in results:
        r = res.round
        sql, cypher = r.scored("sql"), r.scored("cypher")
        entry = {
            "number": r.number, "question": r.question, "columns": list(r.columns), "note": r.note,
            "sql": sql, "cypher": cypher,
            "lines": {"sql": code_lines(sql, "--"), "cypher": code_lines(cypher, "//")},
            "metrics": {"sql": res.sql_metrics, "cypher": res.cypher_metrics},
            "scores": {"sql": verdict.score(res.sql_metrics), "cypher": verdict.score(res.cypher_metrics)},
            "expected_verdict": r.expected, "measured_verdict": res.measured, "margin": res.margin,
            "engines": ["sqlite"] + (["neo4j"] if res.neo4j is not None else []),
            "row_count": len(res.sqlite), "rows": [list(row) for row in res.sqlite[:ROWS_SHOWN]],
            "checks": {
                "agreement": "not run" if res.agree is None else res.agree,
                "oracle": comparable(r, res.sqlite) == comparable(r, oracle_rows(expected, r.number)),
                "scenario": None if r.scenario is None else
                dict(zip(("planted", "rule", "verified_by"), r.scenario)),
            },
            "supporting": r.supporting,
        }
        if r.number == 7:
            entry["top_riser"] = oracle.top_riser(res.sqlite)
        (supporting if r.supporting else rounds).append(entry)
    views = VIEWS.read_text(encoding="utf-8")
    return {
        "seed": seed,
        "reconciled_checksum": reconciled_checksum(build_dir),
        "weights_fingerprint": weights_fingerprint(),
        "verdict_rule": RULE,
        "views": {"sql": views, "lines": code_lines(views, "--"), "unions": len(re.findall(r"\bUNION ALL\b", views))},
        "parameters": {"round_2_cutoff": STALE_CUTOFF, "round_5_vendor": ALL[4].params["vendor"],
                       "round_5_register": REGISTER},
        "rounds": rounds,
        "supporting": supporting,
    }


def oracle_rows(expected: dict, number) -> list[tuple]:
    from .runner import normalise

    return normalise(expected[number])


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_export(results, build_dir: Path, path: Path, seed: int | None) -> Path:
    path.write_text(render(document(results, build_dir, seed)), encoding="utf-8", newline="\n")
    return path


def main() -> int:
    """Regenerate the committed export from a fresh seed-42 build, with both engines."""
    from src.features.stores.neo4j_store import Neo4jLoadError, configured, connect

    from .runner import RoundsError, run_rounds

    if not configured():
        print("error: the committed rounds.json needs both engines; set NEO4J_URI (for example through "
              "src.features.stores.with_neo4j) and run again", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="akg-export-") as tmp:
        build = subprocess.run([sys.executable, "-m", "akg", "build", "--seed", str(PUBLISHED_SEED), "--size", "full",
                                "--text", "ai", "--out", tmp], env=os.environ.copy())
        if build.returncode != 0:
            print("error: the seed-42 build failed", file=sys.stderr)
            return 1
        try:
            driver = connect()
            try:
                results = run_rounds(Path(tmp), driver)
            finally:
                driver.close()
        except (RoundsError, Neo4jLoadError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        write_export(results, Path(tmp), COMMITTED, PUBLISHED_SEED)
    print(f"wrote {COMMITTED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
