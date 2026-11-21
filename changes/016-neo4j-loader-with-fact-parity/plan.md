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
      "then": "it follows these rules:\n- *Nodes:* every table with a `primary key` column is a node type. Its label is the table name in CamelCase, except that the per-source tables share one label and carry a `source` property (`risk_erm` and `risk_ia` are `Risk`, the control tables `Control`, the taxonomy tables `TaxonomyNode`). The node has every column as a property, plus `id` (the primary key's value). These are the published entities plus `CanonicalRisk` and `CanonicalControl`.\n- *Edges:* every published relationship table (no primary key column, two single-file foreign keys) is a relationship type. The type is the upper-case middle of the file name `<from>_<label>_<to>[_erm|_ia]` (for example `control_mitigates_risk_ia` gives `MITIGATES`). Edges run from the first foreign-key column's node to the second's. There are 15 published types at seed 42.\n- *The reconciled layer:*\n  - `canonical_risk.erm_l3_node_id` also becomes a `PLACED_AT` edge to the ERM taxonomy node.\n  - Each maps-to row becomes a `MAPS_TO` edge from the source item to its canonical item, with `logit` (absent for unmerged items).\n  - Each mapped `ia_maps_to_erm` row becomes an `IA_MAPS_TO_ERM` edge with `score` and `basis`. Each `unmapped` row becomes properties on the IA node: `mapping = 'unmapped'`, `mapping_score` and `mapping_basis`.\n  - Each review-queue row becomes a `REVIEW_CANDIDATE` edge from `item_a` to `item_b`, with `kind`, `logit`, `reason` and `drivers`.\n- Uniqueness constraints are created on `id` for every label.",
      "test": "stores.test_neo4j.Neo4jTests.test_ac1_graph_model_from_the_schema (pure: label, type and endpoint derivation for all 47 tables, without a server)",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "`load_neo4j(build_dir, driver)` runs on a loaded seed-42 build",
      "then": "it reads the rows from `<out>/akg.sqlite`, so both stores are built from the same typed rows, and replaces the Neo4j contents. In order:\n1. Take the load lock: a single `LoadLock` node with a `started` timestamp. A lock under 10 minutes old makes the load fail with a clear error; an older one is treated as stale and replaced.\n2. Clear the database in an implicit transaction (`CALL (n) { DETACH DELETE n } IN TRANSACTIONS`).\n3. Create the constraints.\n4. Load nodes, then edges, in batched `UNWIND` statements.\n5. Release the lock.\n\nLoading twice gives identical counts. The answer key is never read: the SQLite file holds none. The lock prevents concurrent loads, but a second local test run querying while another reloads is unsupported, and the README says so. The load takes under 30 s on seed 42 (prototype: published and canonical nodes and published edges in 8.3 s)",
      "test": "stores.test_neo4j.Neo4jTests.test_ac2_load_is_idempotent_locked_and_answer_key_free",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "parity is checked after the seed-42 load (INV-8)",
      "then": "every table matches its graph form:\n- an entity table's row count equals its label's node count, filtered by `source` for per-source tables;\n- a relationship table's row count equals the count of edges of its type between its endpoint labels, with endpoint `source` filters. This is needed because types are shared: `OWNED_BY` holds both issue (250) and control (694) owners at seed 42;\n- `PLACED_AT` equals `canonical_risk` rows, and `MAPS_TO` by source and endpoint equals each maps-to table's rows;\n- `IA_MAPS_TO_ERM` edges plus `unmapped` IA nodes equal `ia_maps_to_erm` rows;\n- `REVIEW_CANDIDATE` edges by `kind` equal the review queue's rows.\n\nOne deterministic sample row per table, the lowest key, has equal values in both stores. The `LoadLock` node is excluded from every count. Total nodes at seed 42 is 2,821, matching the entity rows (prototype). The docs' INV-8 row names this test",
      "test": "stores.test_neo4j.Neo4jTests.test_ac3_inv8_sqlite_and_neo4j_hold_the_same_facts",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the pipeline and the tests run, with or without Neo4j",
      "then": "`akg build` and `akg load` load Neo4j after SQLite when `NEO4J_URI` is set, using `NEO4J_USER` and `NEO4J_PASSWORD`; without it they skip Neo4j and say so.\n\n**Credentials and helpers:**\n- A dev helper, `python -m src.features.stores.with_neo4j <python args>`, runs a Python command with those three variables bridged at run time from `~/.claude/secrets.yaml` (`databases.akg_neo4j`). It never prints them, and it is the only module here that imports `yaml`; the build never does.\n- `neo4j==6.4.1` and its one dependency, `pytz==2026.6`, are pinned in `requirements.txt` (`neo4j` is an approved package; `pytz` is its transitive requirement).\n\n**Tests:** a test helper `neo4j_driver()` skips a test when `NEO4J_URI` is unset, and fails it instead when `AKG_REQUIRE_NEO4J=1`. Both paths are tested. A build without `NEO4J_URI` never imports `neo4j`, which extends the offline test's import check",
      "test": "stores.test_neo4j.Neo4jTests.test_ac4_pipeline_env_helper_skip_and_require",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "docs/data-model.md and the stores README are read",
      "then": "they give the graph model:\n- the node labels and the `source` rule;\n- the 15 published relationship types plus `PLACED_AT`, `MAPS_TO`, `IA_MAPS_TO_ERM` and `REVIEW_CANDIDATE`;\n- how `unmapped` is stored.\n\nThey also give the INV-8 parity rule per file, how to run the Neo4j tests locally (start the server per R3, then `with_neo4j -m unittest ...`), `AKG_REQUIRE_NEO4J`, and the unsupported concurrent-run case. The INV-8 row names AC-3's test",
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
