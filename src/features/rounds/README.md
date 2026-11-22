# rounds

Purpose: the head-to-head planning rounds, each one question asked in SQL and in Cypher over the same facts, proved by agreement, an oracle and the planted scenario.
Entry point: `runner.py` (`run_rounds()`, `main()`), run by `python -m akg rounds --out <dir>` and as step 4 of `python -m akg build`.
Owns: no data entities; the rounds' queries (`roundN.sql`, `roundN.cypher`), the registry (`registry.py`) and the measured-verdict rule (`verdict.py`). The export (`rounds.json`) arrives with child d.
Depends on: `src/features/stores/` (`akg.sqlite`, the Neo4j graph and its `LoadComplete` checksum).

Notes for people and agents working here:
- **Both sources, both engines.** Neo4j's shared labels merge ERM and IA. SQL gets the same merging from `views.sql`, temporary views made on each connection (never in the store schema). A round's SQL must not name a per-source table except `audit_tested_control_ia`. `views.sql` is shared setup and never scored.
- **Three checks** in `tests/rounds/test_rounds.py`: agreement (SQL rows equal Cypher rows), an oracle (an independent Python computation from the CSVs) and the scenario (answer key read in the test only).
- **Round 2's cutoff** is the parameter `:cutoff` / `$cutoff`, default 2023-12-31 in `registry.py`. A control counts as tested when an audit testing it ended on or after it (inclusive). `has_ia_member` marks canonical risks with an IA member; the rest are stale by construction.
- **The Neo4j guard** refuses a graph with no `LoadComplete` node or a checksum other than `reconciled_checksum(<dir>)`. It does not detect a changed `akg.sqlite`.
- **The measured verdict** (`verdict.py`): each side scores `clauses + steps + 5 * moving_parts`; the side whose score times 1.25 is at most the other's wins, else `close`. It counts clauses, not lines, so layout cannot move it. It knows nothing about any round, so child d reuses it unchanged; do not tune it to move a verdict.
- **Query style** (checked by a test): each clause keyword starts its own line, no line over 100 characters, comments on their own line, no comma joins.
- **A new round:** add `roundN.sql` and `roundN.cypher`, a `Round` entry in `registry.py`, its oracle in the test, and its entry in docs/data-model.md.
