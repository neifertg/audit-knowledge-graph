# stores

Purpose: loads the built bank (E1's published files plus E2's reconciled layer) into the stores the head-to-head rounds query: SQLite now (child a), Neo4j next (child b), with the same facts in both (INV-8).
Entry point: `sqlite_store.py` (`load()`), run by `python -m akg build` (after reconcile) or `python -m akg load --out <dir>`.
Owns: the derived store `<out>/akg.sqlite` and its schema, `schema.sql`. Neither is golden: both are rebuilt from the CSVs.
Depends on: the generator's data dictionary (`src/features/generator/README.md`) and E2's reconciled output; the standard library's `sqlite3`.

Notes for people and agents working here:
- **`schema.sql` is generated, never edited.** It comes from two data dictionaries in one Markdown format: the generator's (41 published files) and `reconciled_dictionary.md` (6 reconciled files). After changing either, regenerate it:

  ```
  .venv\Scripts\python -m src.features.stores.schema
  ```

  A test fails while the committed file is stale.
- **Type and key rules:**
  - `id` becomes TEXT. `primary key` becomes the primary key; a relationship file gets a composite key over its id columns.
  - A value naming exactly one `x.csv` becomes a FOREIGN KEY.
  - `enum` becomes TEXT with a CHECK; `int` becomes INTEGER; `decimal` becomes REAL; dates and text become TEXT.
  - A column is NOT NULL unless its values mention `blank` or `unmapped`. A blank cell, and the literal `unmapped` in `ia_maps_to_erm.erm_node_id`, load as NULL.
- **Two-file columns:** a column naming two files `by` another column (the maps-to item IDs, and the review queue's `item_a` and `item_b`) has no FOREIGN KEY, because SQLite cannot reference two tables. Tests check those references against the right table.
- **The answer key is never loaded** (INV-6). The stores hold what a bank would hold.
- **Safe loading:** the load runs with foreign keys on, in dependency order. It writes `akg.sqlite.partial` and renames it at the end, so a failed load leaves no partial database. `akg reconcile`, `build --no-load` and `build --no-reconcile` remove a stale `akg.sqlite`.

## Neo4j (E3 child b, change 016)

- **The graph model** (`graph_model.py`) is derived from the same schema metadata as SQLite:
  - One label per entity table (CamelCase). Per-source tables share a label and carry `source`: `Risk`, `Control` and `TaxonomyNode`.
  - One relationship type per relationship file, from the middle of its name: `control_mitigates_risk_ia` gives `MITIGATES`.
  - The reconciled layer adds `PLACED_AT`, `MAPS_TO`, `IA_MAPS_TO_ERM` and `REVIEW_CANDIDATE`.
- **The loader** (`neo4j_store.py`) loads from `akg.sqlite`, so both stores hold the same typed rows. `python -m akg build` and `akg load` run it after SQLite whenever `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD` are set.
- **A load replaces the whole Neo4j database** (every node except its `LoadLock`). Point `NEO4J_URI` only at a database dedicated to this project.
- **Locking:** a load takes a lock first, atomically and stamped with the server's clock. A lock older than 10 minutes counts as stale. The lock is released in `finally`. A failed load writes no `LoadComplete` node, so a half-loaded graph is detectable.
- **Concurrent test runs are unsupported locally** (no concurrent local runs): the lock stops two loads at once, but not one run reloading the graph while another queries it.
- **Running the Neo4j tests locally:**
  1. Start the server (research R3):

     ```
     $env:JAVA_HOME="$env:LOCALAPPDATA\akg-neo4j\jdk-21.0.13.1+2"; & "$env:LOCALAPPDATA\akg-neo4j\neo4j-community-5.26.33\bin\neo4j.bat" console
     ```

  2. Run the tests through the dev helper:

     ```
     .venv\Scripts\python -m src.features.stores.with_neo4j -m unittest discover -s tests
     ```

  The helper bridges `NEO4J_*` from `~/.claude/secrets.yaml` (`databases.akg_neo4j`) into the child process only, and never prints them. It is the one module here that imports `yaml`, a dev-only exception: the build never does.
- **Skip and require:** without `NEO4J_URI` the Neo4j tests skip. With `AKG_REQUIRE_NEO4J=1` (CI) they fail instead, so CI cannot go green with them skipped.
- **Test isolation:** every test subprocess runs with `tests/generator/helpers.akg_env()`, which strips `NEO4J_*`. Only `tests/stores/test_neo4j.py` touches the graph.
