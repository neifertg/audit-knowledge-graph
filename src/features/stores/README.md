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
