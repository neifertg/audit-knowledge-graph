# Neo4j loader with fact parity

Change `016-neo4j-loader-with-fact-parity` · objective **O2**: A data scientist finds every claim credible and reproducible. Signal: one command reproduces every number on the page from a fresh clone; CI is green; every SQL-vs-Cypher round has a test proving both return the same answer; the page makes no claim without a test or a cited method.

## Why
E3 child b (O2). This is where the knowledge graph is built. It loads the same facts as the SQLite store into Neo4j, and proves they are the same facts (INV-8), so every later round compares engines rather than data.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | the graph model is derived from the schema metadata (`stores.schema.load_tables`) | it follows these rules:
- *Nodes:* every table with a `primary key` column is a node type, except the four reconciled tables mapped specially below (`ia_maps_to_erm`, the two maps-to tables and `review_queue`). Its label is the table name in CamelCase, except that the per-source tables share one label and carry a `source` property (`risk_erm` and `risk_ia` are `Risk`, the control tables `Control`, the taxonomy tables `TaxonomyNode`). The node has every column as a property, plus `id` (the primary key's value). These are the published entities plus `CanonicalRisk` and `CanonicalControl`.
- *Edges:* every published relationship table (no primary key column, two single-file foreign keys) is a relationship type. The type is the upper-case middle of the file name: strip a trailing `_erm` or `_ia`, then the first foreign key's target table name (without its source suffix) and `_` from the front, and `_` plus the second target's name from the end (for example `control_mitigates_risk_ia` gives `MITIGATES`). Edges run from the first foreign-key column's node to the second's. There are 15 published types at seed 42.
- *The reconciled layer:*
  - `canonical_risk.erm_l3_node_id` also becomes a `PLACED_AT` edge to the ERM taxonomy node.
  - Each maps-to row becomes a `MAPS_TO` edge from the source item to its canonical item, with `logit` (absent for unmerged items).
  - Each mapped `ia_maps_to_erm` row becomes an `IA_MAPS_TO_ERM` edge with `score` and `basis`. Each `unmapped` row becomes properties on the IA node: `mapping = 'unmapped'`, `mapping_score` and `mapping_basis`.
  - Each review-queue row becomes a `REVIEW_CANDIDATE` edge from `item_a` to `item_b`, with `kind`, `logit`, `reason` and `drivers`. The endpoints by kind: `risk` runs from Risk ERM to Risk IA, `duplicate` from Risk ERM to Risk ERM, and `control` from Control ERM to Control IA.
- Uniqueness constraints are created on `id` for every label.
- *Absent values:* a NULL in SQLite is an absent property in Neo4j (`SET n = r` drops nulls). Comparisons treat NULL and absent as equal.
- *Unique IDs across sources:* per-source tables share a label and a unique `id`, which relies on ERM and IA IDs never colliding (`ERM-R`, `IAR-`, `ERMT-`, `IAT-` and so on). AC-3 asserts the per-source ID sets are disjoint.
- *Counts:* the schema gives 17 node tables (14 labels), 26 relationship tables and 4 special tables, 47 in all, and the pure test asserts these counts. | `stores.test_neo4j.Neo4jTests.test_ac1_graph_model_from_the_schema (pure: label, type and endpoint derivation for all 47 tables, without a server)` | pass | PASS |
| AC-2 | `load_neo4j(build_dir, driver)` runs on a loaded seed-42 build | it reads the rows from `<out>/akg.sqlite`, so both stores come from the same typed rows, and replaces the Neo4j contents. In order:
1. Create the `LoadLock.name` uniqueness constraint first (idempotent), then take the load lock **atomically**, with `started` set from the server clock (`datetime()`). One `MERGE (l:LoadLock {name: 'load'})` sets a fresh token on create, or replaces the token when the existing lock's `started` is over 10 minutes old (stale). The load proceeds only if the lock holds its own token; otherwise it fails naming the lock's age.
2. Clear every node **except** `LoadLock`, in an implicit transaction (`MATCH (n) WHERE NOT n:LoadLock CALL (n) { DETACH DELETE n } IN TRANSACTIONS`).
3. Create the constraints.
4. Load nodes, then edges, in batched `UNWIND` statements.
5. Write a `LoadComplete` node holding the build's reconciled-golden checksum.
6. Release the lock in a `finally`, deleting it only if it holds the load's own token.

**A failed load** releases the lock and leaves no `LoadComplete` node, so a half-loaded graph is detectable. The parity check and the rounds (c and d) require `LoadComplete`.

**An unreachable server** fails the load with a clear error and a nonzero exit, naming `NEO4J_URI`.

Loading twice gives identical results. The answer key is never read: the SQLite file holds none, and a copy of the build without `answer_key/` gives an identical graph.

The load takes under 30 s on seed 42 (prototype: 8.3 s for the published and canonical nodes and the published edges).

Tests:
- a fresh foreign lock blocks the load;
- a stale lock is replaced;
- a load forced to fail midway releases its lock and leaves no `LoadComplete`. The failure is real, not mocked: a copy of the build whose `akg.sqlite` has one edge table dropped. The loader reads each table's rows while loading it, after the clear, so the failure lands after the nodes; the test asserts the outcome that matters: no `LoadComplete`, the lock released, and the next good load restoring parity.

These lock tests reload Neo4j, so the shared fixture checks `LoadComplete` and its checksum before each Neo4j test, and reloads when either is missing or differs. "Once per run" means at most once per test that leaves the graph changed. | `stores.test_neo4j.Neo4jTests.test_ac2_load_is_idempotent_locked_and_answer_key_free` | pass | PASS |
| AC-3 | parity is checked after the seed-42 load (INV-8) | every table matches its graph form exactly, as **multisets**: the comparisons below are made on sorted lists, not sets, so a duplicated node or edge fails. Each label (with `source`) has exactly as many nodes as its table has rows, and each edge type (with its endpoint labels and `source`s) exactly as many edges as its table has rows, as INV-8 states:
- *Entity tables:* the set of IDs equals the set of `id` values on its label, filtered by `source` for per-source tables.
- *Relationship tables:* the set of (from ID, to ID) pairs equals the set of (start `id`, end `id`) pairs of edges of its type between its endpoint labels, with endpoint `source` filters. A reversed or misdirected edge therefore fails; types are shared across files (`OWNED_BY` holds both issue and control owners).
- `PLACED_AT` pairs equal (`canonical_risk_id`, `erm_l3_node_id`).
- `MAPS_TO` pairs by source equal each maps-to table's (item, canonical ID).
- `IA_MAPS_TO_ERM` pairs equal the mapped rows, and the IA nodes flagged `unmapped` equal the unmapped rows.
- `REVIEW_CANDIDATE` (`item_a`, `item_b`, `kind`) triples equal the review queue's.
- *Properties:* every column's values match for the lowest-key row of each table, plus, for every nullable column, the lowest-key row where it is NULL, so the NULL rule is exercised (for example an open issue's `closed_date` and an unmerged item's `logit`). NULL equals absent. Edge properties (`logit`, `score`, `basis`, `kind`, `reason`, `drivers`) are compared the same way on their tables.
- The per-source ID sets of the same label are disjoint.

`LoadLock` and `LoadComplete` are excluded from every comparison. At seed 42 there are 2,821 entity nodes (prototype). The docs' INV-8 row names this test | `stores.test_neo4j.Neo4jTests.test_ac3_inv8_sqlite_and_neo4j_hold_the_same_facts` | pass | PASS |
| AC-4 | the pipeline and the tests run, with or without Neo4j | `akg build` and `akg load` load Neo4j after SQLite when `NEO4J_URI` is set, using `NEO4J_USER` and `NEO4J_PASSWORD`. Without it they skip Neo4j and say so. `--no-load` and `--no-reconcile` also skip Neo4j.

**Test isolation.** Tests that spawn `akg` subprocesses must not touch the shared Neo4j fixture, so one shared function, `tests/generator/helpers.akg_env(neo4j=False)`, builds every test subprocess's environment and strips `NEO4J_*` unless the test opts in. `run_akg` and the subprocess builds in `test_batch` and `test_offline` all use it. **A test proves the isolation:** with `NEO4J_URI` pointed at an unreachable address in the test process, a `run_akg('build', '--size', 'sample', ...)` still succeeds, because stripped subprocesses never try to connect. The same test asserts that `test_batch` and `test_offline` build their subprocess environments with `akg_env` (shared, not re-implemented), so no extra full-size build is added (L-014). Only `tests/stores/test_neo4j.py` loads Neo4j, once per run. **The full suite passes both without Neo4j and under `with_neo4j`** (Neo4j tests running), and the criteria are marked from the `with_neo4j` run.

**The `with_neo4j` helper:** `python -m src.features.stores.with_neo4j <python args>` runs a Python command with the three variables bridged at run time from `~/.claude/secrets.yaml` (`databases.akg_neo4j`). It never prints them, and it is a dev-only exception to the rule that nothing imports `yaml`: the build and every runtime module never import it. Its test is hermetic:
- the parent's `NEO4J_*` are removed first, so a pass cannot come from inherited values;
- a dummy secrets file under a fake home supplies the values, with both `HOME` and `USERPROFILE` pointed at it (on Windows `Path.home()` reads `USERPROFILE`), so the real secrets file is never read;
- a child process reports only whether each variable is set and equals the dummy value;
- the dummy password never appears in the output;
- a missing secrets file or a missing `databases.akg_neo4j` entry fails with a clear message.

**Dependencies:** `neo4j==6.4.1` and its one dependency, `pytz==2026.6`, are pinned in `requirements.txt` (`neo4j` is an approved package; `pytz` is its transitive requirement).

**Skip and require:** a test helper `neo4j_driver()` skips when `NEO4J_URI` is unset and fails instead when `AKG_REQUIRE_NEO4J=1`; both paths are tested. A build without `NEO4J_URI` never imports `neo4j`, which extends the offline test's import check. | `stores.test_neo4j.Neo4jTests.test_ac4_pipeline_env_helper_skip_and_require` | pass | PASS |
| AC-5 | docs/data-model.md and the stores README are read | they give the graph model:
- the node labels and the `source` rule;
- the 15 published relationship types plus `PLACED_AT`, `MAPS_TO`, `IA_MAPS_TO_ERM` and `REVIEW_CANDIDATE`;
- how `unmapped` is stored.

They also give the INV-8 parity rule per file, how to run the Neo4j tests locally (start the server per R3, then `with_neo4j -m unittest ...`), `AKG_REQUIRE_NEO4J`, and the unsupported concurrent-run case. The INV-8 row names AC-3's test. The README warns that a load **replaces the whole Neo4j database** (every node except the lock), so point `NEO4J_URI` only at a database dedicated to this project, and it records the `yaml` dev-helper exception. | `stores.test_neo4j.Neo4jTests.test_ac5_docs_describe_the_graph_model (runs without Neo4j)` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/stores/****: `src/features/stores/graph_model.py`, `src/features/stores/neo4j_store.py`, `src/features/stores/with_neo4j.py`
3. **akg/****: `akg/__main__.py`
4. **requirements.txt**: `requirements.txt`
5. **Tests**: `tests/generator/golden.py`, `tests/generator/helpers.py`, `tests/generator/test_batch.py`, `tests/generator/test_offline.py`, `tests/reconciliation/golden.py`, `tests/stores/test_neo4j.py`

## Data impact
- **New derived store:** the Neo4j database (local per research R3; a CI service container in child e). It holds 2,821 nodes for the published entities and canonical items at seed 42, the published relationships, and the reconciled layer's edges as AC-1 maps them. It is not golden.
- **No published or reconciled file changes;** the SQLite store is unchanged.
- **INV-8 becomes enforced** (AC-3). **INV-6:** the graph is loaded from `akg.sqlite`, which holds no answer key.
- **`requirements.txt`** gains `neo4j==6.4.1` and `pytz==2026.6`.

## Risks
- **Neo4j not running locally:** the tests skip, and a skipped test is not a pass. The done-check is therefore run with `with_neo4j`, and the plan's criteria are marked from that run. CI (child e) enforces it with `AKG_REQUIRE_NEO4J=1`.
- **Test subprocesses touching Neo4j:** the first critique's blocker. AC-4 strips `NEO4J_*` from test subprocesses, and the done-check runs the full suite under `with_neo4j` to prove it.
- **Locks:** atomic `MERGE`, released in `finally`, excluded from the clear; tested fresh, stale and failed.
- **Load time on a slow machine:** the prototype took 8.3 s, and the bar is 30 s.
- **Two stores drifting:** the graph is loaded from the SQLite rows, so it cannot read the CSVs differently; parity checks every table.

## Deliberately not in this PR
- The rounds and their queries (c and d); CI and the GitHub repo (e).
- Indexes beyond the `id` constraints, and Graph Data Science (epic non-goal).

Parked for later:
- 2026-11-21 016 review minors: AC-3 maps-to property check should match the edge by both ends (item and canonical); neo4j_store counts SQLite rows not created edges; AuthError gives a traceback, not a clear message; test the CLI's nonzero exit when Neo4j is unreachable; the two golden.py scripts should reuse akg_env (from 016-neo4j-loader-with-fact-parity)

## Lessons recorded
- L-017 On a low-memory machine, reviewers must not wait on long test runs

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `f08fdc3bd4a13078`
- Size: 11 code files, +627 / -11 lines
