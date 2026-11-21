# SQLite schema and loader

```json plan
{
  "id": "015-sqlite-schema-and-loader",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-21",
  "objective": "O2",
  "areas": [
    "src/features/stores/**",
    "tests/**",
    "docs/data-model.md",
    "akg/**"
  ],
  "timebox": "1 day. Past this, stop and re-plan or split.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m src.features.stores.schema` runs",
      "then": "it writes `src/features/stores/schema.sql`, generated from two data dictionaries in the same Markdown table format:\n- the generator's (`src/features/generator/README.md`, 41 published files);\n- a new `src/features/stores/reconciled_dictionary.md` for the 6 reconciled files.\n\nThere is one table per file, named after it; answer-key files get none. A test asserts that the committed `schema.sql` equals a fresh generation, that every published and reconciled CSV of the seed-42 build has a table, and that no table exists for an answer-key file",
      "test": "stores.test_sqlite.SqliteTests.test_ac1_schema_is_generated_from_the_dictionaries",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the schema is generated",
      "then": "it follows these rules:\n- Columns appear in dictionary order.\n- `id` becomes TEXT. `primary key` becomes the table's PRIMARY KEY; a table with no `primary key` column (a relationship file) gets a composite PRIMARY KEY over its `id` columns.\n- A value naming `x.csv` becomes a FOREIGN KEY to `x`'s primary key.\n- `enum` becomes TEXT with a CHECK on the listed values; `int` becomes INTEGER; `date` and `text` become TEXT.\n- A column is NOT NULL unless its values mention `blank`. A blank CSV cell loads as NULL.\n\nReconciled columns that point to either source (`source` plus item ID in the maps-to files; `item_a` and `item_b` in the review queue) carry no FOREIGN KEY, because SQLite cannot reference two tables. AC-3's test checks them against the right table instead. `ia_maps_to_erm.erm_node_id` is a nullable FOREIGN KEY, holding NULL for `unmapped` (as the epic's INV-8 plan states)",
      "test": "stores.test_sqlite.SqliteTests.test_ac2_type_and_key_rules (a hand-written two-table dictionary fixture with an enum, a blank-allowed date, a foreign key and a relationship table)",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the load runs on the seed-42 full build",
      "then": "`<out>/akg.sqlite` holds exactly the CSV rows: per table, the set of row tuples equals the CSV's, with blanks as NULL and `unmapped` as NULL. The load runs with `PRAGMA foreign_keys = ON`, and `PRAGMA foreign_key_check` reports no violation. Every cross-source reference in the reconciled tables exists in the table its `source` names. The load takes under 5 s (prototype: 7,530 rows in 0.7 s)",
      "test": "stores.test_sqlite.SqliteTests.test_ac3_every_row_lands_once_and_keys_hold",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "`python -m akg build` or `python -m akg load --out <dir>` runs",
      "then": "build runs generate, reconcile, then load, writing `<out>/akg.sqlite`. `--no-load` stops after reconcile, and `--no-reconcile` still stops after generate. Neo4j loading comes in child b, and rounds in c and d.\n\n`akg load` (re)builds `<out>/akg.sqlite` from scratch for an existing reconciled build. Loading twice gives identical row sets, so the load is idempotent. No table, row or file in the database comes from `answer_key/`: a build whose `answer_key/` is deleted loads identically.\n\nThe reconciliation test helper (`tests/reconciliation/helpers.full_build`) passes `--no-load`, and new store tests reuse one cached seed-42 build, so the suite gains one load (under a second) rather than one per test (L-014)",
      "test": "stores.test_sqlite.SqliteTests.test_ac4_build_and_load_commands_idempotent_and_answer_key_free",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "docs/data-model.md and `src/features/stores/README.md` are read",
      "then": "they describe the SQLite store: `<out>/akg.sqlite`; the generated schema and how to regenerate it; the type and key rules; the cross-source columns without FOREIGN KEY and how they are checked; that the store is derived and not golden; and that the answer key is never loaded. The data model's INV-8 row notes that the Neo4j side arrives in child b",
      "test": "stores.test_sqlite.SqliteTests.test_ac5_docs_describe_the_sqlite_store",
      "status": "pending"
    }
  ],
  "epic": "003-e3-dual-stores-and-head-to-head-rounds",
  "child": "a"
}
```

## Why
E3 child a (O2). The head-to-head rounds need the same facts in SQLite and Neo4j. This child builds the relational side: a schema that cannot drift from the published data dictionary, and a loader that lands every published and reconciled row exactly once, with keys enforced. It also implements the `load` step of the pipeline contract in AGENTS.md.

## Data impact
- **New derived store:** `<out>/akg.sqlite`, with 47 tables (41 published files and 6 reconciled files). Nothing in E1's or E2's outputs changes, and no golden changes.
- **New dictionary:** `src/features/stores/reconciled_dictionary.md`, describing the reconciled files in the generator's dictionary format. The columns are the ones docs/data-model.md already lists for 013.
- **Invariants:**
  - INV-6: the store never holds the answer key, tested in AC-4.
  - INV-8: the SQLite half only; parity with Neo4j comes in child b.
  - INV-10 holds by construction: per-source tables stay separate, and ERM-IA links exist only in the reconciled tables.

## Test plan
Tests go in `tests/stores/test_sqlite.py`, using one cached seed-42 full build (built with `--no-load` and loaded once by the test fixture) and a small dictionary fixture for AC-2. The whole suite stays the done-check.

**Evidence** (pre-plan prototype on 2026-11-21): the generator's dictionary parses into 41 tables (a 311-line schema). The seed-42 build loads 7,530 rows in 0.7 s with zero foreign-key violations and every enum CHECK satisfied. Every published CSV has a dictionary entry.

**Not tested here:** Neo4j (child b) and the rounds (c and d).

## Risks
- **The dictionary is wrong or stale for a file.** Then the generated schema fails the load (CHECK or FOREIGN KEY), which is the point. E1's own test (`checks.data_dictionary`) already ties the dictionary to the output.
- **Reconciled columns that point to either source** can't be foreign keys; AC-3 checks them explicitly.
- **Suite time:** the pipeline gains a load step at about 0.7 s per full build. Reconciliation helpers use `--no-load`, and store tests share one build.

## Out of scope
- Neo4j and parity (child b); rounds (c and d); CI (e).
- Indexes for query speed: added in c if a round needs them; no speed claims either way.

## Relevant lessons
- **L-014** (count the builds a step adds): the reconciliation helpers pass `--no-load`; store tests share one build.
- **L-006** (frozen goldens): the store is derived, and nothing golden changes.
- **L-012** (quote the built module): the figures come from the prototype and are re-measured by the build.

## Slices
1. `reconciled_dictionary.md` and the schema generator (AC-1, AC-2).
2. The loader and the `akg` wiring (AC-3, AC-4).
3. Docs (AC-5).
