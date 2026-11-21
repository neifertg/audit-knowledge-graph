# Neo4j loader with fact parity

```json plan
{
  "id": "016-neo4j-loader-with-fact-parity",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-21",
  "objective": "O2",
  "areas": [
    "src/features/stores/**",
    "tests/**",
    "docs/data-model.md",
    "akg/**",
    "requirements.txt"
  ],
  "timebox": "1 day. Past this, stop and re-plan or split.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "the graph model is derived from the schema metadata (`stores.schema.load_tables`)",
      "then": "it follows these rules:\n- *Nodes:* every table with a `primary key` column is a node type, except the four reconciled tables mapped specially below (`ia_maps_to_erm`, the two maps-to tables and `review_queue`). Its label is the table name in CamelCase, except that the per-source tables share one label and carry a `source` property (`risk_erm` and `risk_ia` are `Risk`, the control tables `Control`, the taxonomy tables `TaxonomyNode`). The node has every column as a property, plus `id` (the primary key's value). These are the published entities plus `CanonicalRisk` and `CanonicalControl`.\n- *Edges:* every published relationship table (no primary key column, two single-file foreign keys) is a relationship type. The type is the upper-case middle of the file name: strip a trailing `_erm` or `_ia`, then the first foreign key's target table name (without its source suffix) and `_` from the front, and `_` plus the second target's name from the end (for example `control_mitigates_risk_ia` gives `MITIGATES`). Edges run from the first foreign-key column's node to the second's. There are 15 published types at seed 42.\n- *The reconciled layer:*\n  - `canonical_risk.erm_l3_node_id` also becomes a `PLACED_AT` edge to the ERM taxonomy node.\n  - Each maps-to row becomes a `MAPS_TO` edge from the source item to its canonical item, with `logit` (absent for unmerged items).\n  - Each mapped `ia_maps_to_erm` row becomes an `IA_MAPS_TO_ERM` edge with `score` and `basis`. Each `unmapped` row becomes properties on the IA node: `mapping = 'unmapped'`, `mapping_score` and `mapping_basis`.\n  - Each review-queue row becomes a `REVIEW_CANDIDATE` edge from `item_a` to `item_b`, with `kind`, `logit`, `reason` and `drivers`. The endpoints by kind: `risk` runs from Risk ERM to Risk IA, `duplicate` from Risk ERM to Risk ERM, and `control` from Control ERM to Control IA.\n- Uniqueness constraints are created on `id` for every label.\n- *Absent values:* a NULL in SQLite is an absent property in Neo4j (`SET n = r` drops nulls). Comparisons treat NULL and absent as equal.\n- *Unique IDs across sources:* per-source tables share a label and a unique `id`, which relies on ERM and IA IDs never colliding (`ERM-R`, `IAR-`, `ERMT-`, `IAT-` and so on). AC-3 asserts the per-source ID sets are disjoint.\n- *Counts:* the schema gives 17 node tables (14 labels), 26 relationship tables and 4 special tables, 47 in all, and the pure test asserts these counts.",
      "test": "stores.test_neo4j.Neo4jTests.test_ac1_graph_model_from_the_schema (pure: label, type and endpoint derivation for all 47 tables, without a server)",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "`load_neo4j(build_dir, driver)` runs on a loaded seed-42 build",
      "then": "it reads the rows from `<out>/akg.sqlite`, so both stores come from the same typed rows, and replaces the Neo4j contents. In order:\n1. Create the `LoadLock.name` uniqueness constraint first (idempotent), then take the load lock **atomically**, with `started` set from the server clock (`datetime()`). One `MERGE (l:LoadLock {name: 'load'})` sets a fresh token on create, or replaces the token when the existing lock's `started` is over 10 minutes old (stale). The load proceeds only if the lock holds its own token; otherwise it fails naming the lock's age.\n2. Clear every node **except** `LoadLock`, in an implicit transaction (`MATCH (n) WHERE NOT n:LoadLock CALL (n) { DETACH DELETE n } IN TRANSACTIONS`).\n3. Create the constraints.\n4. Load nodes, then edges, in batched `UNWIND` statements.\n5. Write a `LoadComplete` node holding the build's reconciled-golden checksum.\n6. Release the lock in a `finally`, deleting it only if it holds the load's own token.\n\n**A failed load** releases the lock and leaves no `LoadComplete` node, so a half-loaded graph is detectable. The parity check and the rounds (c and d) require `LoadComplete`.\n\n**An unreachable server** fails the load with a clear error and a nonzero exit, naming `NEO4J_URI`.\n\nLoading twice gives identical results. The answer key is never read: the SQLite file holds none, and a copy of the build without `answer_key/` gives an identical graph.\n\nThe load takes under 30 s on seed 42 (prototype: 8.3 s for the published and canonical nodes and the published edges).\n\nTests:\n- a fresh foreign lock blocks the load;\n- a stale lock is replaced;\n- a load forced to fail midway releases its lock and leaves no `LoadComplete`. The failure is real, not mocked: a copy of the build whose `akg.sqlite` has one edge table dropped. The loader reads each table's rows while loading it, after the clear, so the failure lands after the nodes; the test asserts the outcome that matters: no `LoadComplete`, the lock released, and the next good load restoring parity.\n\nThese lock tests reload Neo4j, so the shared fixture checks `LoadComplete` and its checksum before each Neo4j test, and reloads when either is missing or differs. \"Once per run\" means at most once per test that leaves the graph changed.",
      "test": "stores.test_neo4j.Neo4jTests.test_ac2_load_is_idempotent_locked_and_answer_key_free",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "parity is checked after the seed-42 load (INV-8)",
      "then": "every table matches its graph form exactly, as **multisets**: the comparisons below are made on sorted lists, not sets, so a duplicated node or edge fails. Each label (with `source`) has exactly as many nodes as its table has rows, and each edge type (with its endpoint labels and `source`s) exactly as many edges as its table has rows, as INV-8 states:\n- *Entity tables:* the set of IDs equals the set of `id` values on its label, filtered by `source` for per-source tables.\n- *Relationship tables:* the set of (from ID, to ID) pairs equals the set of (start `id`, end `id`) pairs of edges of its type between its endpoint labels, with endpoint `source` filters. A reversed or misdirected edge therefore fails; types are shared across files (`OWNED_BY` holds both issue and control owners).\n- `PLACED_AT` pairs equal (`canonical_risk_id`, `erm_l3_node_id`).\n- `MAPS_TO` pairs by source equal each maps-to table's (item, canonical ID).\n- `IA_MAPS_TO_ERM` pairs equal the mapped rows, and the IA nodes flagged `unmapped` equal the unmapped rows.\n- `REVIEW_CANDIDATE` (`item_a`, `item_b`, `kind`) triples equal the review queue's.\n- *Properties:* every column's values match for the lowest-key row of each table, plus, for every nullable column, the lowest-key row where it is NULL, so the NULL rule is exercised (for example an open issue's `closed_date` and an unmerged item's `logit`). NULL equals absent. Edge properties (`logit`, `score`, `basis`, `kind`, `reason`, `drivers`) are compared the same way on their tables.\n- The per-source ID sets of the same label are disjoint.\n\n`LoadLock` and `LoadComplete` are excluded from every comparison. At seed 42 there are 2,821 entity nodes (prototype). The docs' INV-8 row names this test",
      "test": "stores.test_neo4j.Neo4jTests.test_ac3_inv8_sqlite_and_neo4j_hold_the_same_facts",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the pipeline and the tests run, with or without Neo4j",
      "then": "`akg build` and `akg load` load Neo4j after SQLite when `NEO4J_URI` is set, using `NEO4J_USER` and `NEO4J_PASSWORD`. Without it they skip Neo4j and say so. `--no-load` and `--no-reconcile` also skip Neo4j.\n\n**Test isolation.** Tests that spawn `akg` subprocesses must not touch the shared Neo4j fixture, so one shared function, `tests/generator/helpers.akg_env(neo4j=False)`, builds every test subprocess's environment and strips `NEO4J_*` unless the test opts in. `run_akg` and the subprocess builds in `test_batch` and `test_offline` all use it. **A test proves the isolation:** with `NEO4J_URI` pointed at an unreachable address in the test process, a `run_akg('build', '--size', 'sample', ...)` still succeeds, because stripped subprocesses never try to connect. The same test asserts that `test_batch` and `test_offline` build their subprocess environments with `akg_env` (shared, not re-implemented), so no extra full-size build is added (L-014). Only `tests/stores/test_neo4j.py` loads Neo4j, once per run. **The full suite passes both without Neo4j and under `with_neo4j`** (Neo4j tests running), and the criteria are marked from the `with_neo4j` run.\n\n**The `with_neo4j` helper:** `python -m src.features.stores.with_neo4j <python args>` runs a Python command with the three variables bridged at run time from `~/.claude/secrets.yaml` (`databases.akg_neo4j`). It never prints them, and it is a dev-only exception to the rule that nothing imports `yaml`: the build and every runtime module never import it. Its test is hermetic:\n- the parent's `NEO4J_*` are removed first, so a pass cannot come from inherited values;\n- a dummy secrets file under a fake home supplies the values, with both `HOME` and `USERPROFILE` pointed at it (on Windows `Path.home()` reads `USERPROFILE`), so the real secrets file is never read;\n- a child process reports only whether each variable is set and equals the dummy value;\n- the dummy password never appears in the output;\n- a missing secrets file or a missing `databases.akg_neo4j` entry fails with a clear message.\n\n**Dependencies:** `neo4j==6.4.1` and its one dependency, `pytz==2026.6`, are pinned in `requirements.txt` (`neo4j` is an approved package; `pytz` is its transitive requirement).\n\n**Skip and require:** a test helper `neo4j_driver()` skips when `NEO4J_URI` is unset and fails instead when `AKG_REQUIRE_NEO4J=1`; both paths are tested. A build without `NEO4J_URI` never imports `neo4j`, which extends the offline test's import check.",
      "test": "stores.test_neo4j.Neo4jTests.test_ac4_pipeline_env_helper_skip_and_require",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "docs/data-model.md and the stores README are read",
      "then": "they give the graph model:\n- the node labels and the `source` rule;\n- the 15 published relationship types plus `PLACED_AT`, `MAPS_TO`, `IA_MAPS_TO_ERM` and `REVIEW_CANDIDATE`;\n- how `unmapped` is stored.\n\nThey also give the INV-8 parity rule per file, how to run the Neo4j tests locally (start the server per R3, then `with_neo4j -m unittest ...`), `AKG_REQUIRE_NEO4J`, and the unsupported concurrent-run case. The INV-8 row names AC-3's test. The README warns that a load **replaces the whole Neo4j database** (every node except the lock), so point `NEO4J_URI` only at a database dedicated to this project, and it records the `yaml` dev-helper exception.",
      "test": "stores.test_neo4j.Neo4jTests.test_ac5_docs_describe_the_graph_model (runs without Neo4j)",
      "status": "pending"
    }
  ],
  "epic": "003-e3-dual-stores-and-head-to-head-rounds",
  "child": "b"
}
```

## Why
E3 child b (O2). This is where the knowledge graph is built. It loads the same facts as the SQLite store into Neo4j, and proves they are the same facts (INV-8), so every later round compares engines rather than data.

## Data impact
- **New derived store:** the Neo4j database (local per research R3; a CI service container in child e). It holds 2,821 nodes for the published entities and canonical items at seed 42, the published relationships, and the reconciled layer's edges as AC-1 maps them. It is not golden.
- **No published or reconciled file changes;** the SQLite store is unchanged.
- **INV-8 becomes enforced** (AC-3). **INV-6:** the graph is loaded from `akg.sqlite`, which holds no answer key.
- **`requirements.txt`** gains `neo4j==6.4.1` and `pytz==2026.6`.

## Test plan
Tests go in `tests/stores/test_neo4j.py`, against the cached seed-42 build from 015's fixture, loaded into Neo4j once per test run. AC-1 and AC-5 run without a server; AC-2 to AC-4's Neo4j parts skip without `NEO4J_URI` (fail with `AKG_REQUIRE_NEO4J=1`). Locally they run through `with_neo4j` against the R3 server; child e makes them run in CI. The whole suite stays the done-check, run once with and once without Neo4j.

**Evidence** (pre-plan prototype on 2026-11-21, local Neo4j 5.26.33):
- Deriving labels and types from the schema metadata loaded 2,821 nodes, equal to the entity rows, with 15 published relationship types, in 8.3 s.
- It also found two pitfalls this plan pins. Types are shared across files (`OWNED_BY` holds 944 edges = 250 issue + 694 control owners), so parity counts by type *and* endpoint labels. And a batched delete must run in an implicit transaction, in the `CALL (n) {...}` form; the old form is deprecated.

**Not tested here:** rounds (c and d) and CI (e).

## Risks
- **Neo4j not running locally:** the tests skip, and a skipped test is not a pass. The done-check is therefore run with `with_neo4j`, and the plan's criteria are marked from that run. CI (child e) enforces it with `AKG_REQUIRE_NEO4J=1`.
- **Test subprocesses touching Neo4j:** the first critique's blocker. AC-4 strips `NEO4J_*` from test subprocesses, and the done-check runs the full suite under `with_neo4j` to prove it.
- **Locks:** atomic `MERGE`, released in `finally`, excluded from the clear; tested fresh, stale and failed.
- **Load time on a slow machine:** the prototype took 8.3 s, and the bar is 30 s.
- **Two stores drifting:** the graph is loaded from the SQLite rows, so it cannot read the CSVs differently; parity checks every table.

## Out of scope
- The rounds and their queries (c and d); CI and the GitHub repo (e).
- Indexes beyond the `id` constraints, and Graph Data Science (epic non-goal).

## Relevant lessons
- **L-012** (quote the built module): the prototype's figures are re-measured by the build.
- **L-014** (count the builds a step adds): the Neo4j load happens only when `NEO4J_URI` is set, so the default local suite is unchanged; the Neo4j tests load once per run.
- **L-016** (fingerprints ripple): this change touches no fingerprinted file (`train.py`, the reconciliation features), so `weights.json` and `scores.json` stay unchanged.

## Slices
1. The graph model derivation (AC-1, pure).
2. `neo4j_store.py` loader, lock and clear (AC-2), and parity (AC-3).
3. The env helper, pipeline wiring, skip/require and requirements (AC-4).
4. Docs (AC-5).
