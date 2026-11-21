# SQLite schema and loader

```json plan
{
  "id": "015-sqlite-schema-and-loader",
  "tier": "standard",
  "status": "done",
  "created": "2026-11-21",
  "objective": "O2",
  "areas": [
    "src/features/stores/**",
    "tests/**",
    "docs/data-model.md",
    "akg/**",
    "src/features/reconciliation/train.py",
    "src/features/reconciliation/weights.json",
    "src/features/reconciliation/scores.json"
  ],
  "timebox": "1 day. Past this, stop and re-plan or split.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m src.features.stores.schema` runs",
      "then": "it writes `src/features/stores/schema.sql`, generated from two data dictionaries in the same Markdown table format:\n- the generator's (`src/features/generator/README.md`, 41 published files);\n- a new `src/features/stores/reconciled_dictionary.md` for the 6 reconciled files.\n\nThere is one table per file, named after it; answer-key files get none. A test asserts that the committed `schema.sql` equals a fresh generation, that every published and reconciled CSV of the seed-42 build has a table, and that no table exists for an answer-key file",
      "test": "stores.test_sqlite.SqliteTests.test_ac1_schema_is_generated_from_the_dictionaries",
      "status": "pass"
    },
    {
      "id": "AC-2",
      "when": "the schema is generated",
      "then": "it follows these rules:\n- Columns appear in dictionary order.\n- `id` becomes TEXT. `primary key` becomes the table's PRIMARY KEY; a table with no `primary key` column gets a composite PRIMARY KEY over its `id` columns.\n- A value that is exactly one `x.csv` becomes a FOREIGN KEY to `x`'s primary key.\n- A value naming two files with `by` (for example ``risk_erm.csv` or `risk_ia.csv` by `source``) gets no FOREIGN KEY; AC-3 checks those columns instead.\n- `enum` becomes TEXT with a CHECK on the listed values; `int` becomes INTEGER; the new `decimal` type becomes REAL; `date` and `text` become TEXT.\n- A column is NOT NULL unless its values mention `blank` or `unmapped`. A blank cell loads as NULL, and so does the literal `unmapped` in a column whose values mention it (only `ia_maps_to_erm.erm_node_id`).\n\n`reconciled_dictionary.md` uses these forms for the reconciled files: `score` is `decimal`; `logit` is `decimal`, blank for unmerged items in the maps-to files; the maps-to item IDs and the review queue's `item_a` and `item_b` are two-file values, and `erm_node_id` is ``taxonomy_node_erm.csv`, or `unmapped` (stored as NULL)``. `ia_maps_to_erm.ia_node_id` is marked `primary key` (one row per IA node), and so is each canonical table's ID. The tables are created and loaded in foreign-key dependency order, with `PRAGMA foreign_keys = ON` throughout.",
      "test": "stores.test_sqlite.SqliteTests.test_ac2_type_and_key_rules (a hand-written two-table dictionary fixture with an enum, a blank-allowed date, a foreign key and a relationship table)",
      "status": "pass"
    },
    {
      "id": "AC-3",
      "when": "the load runs on the seed-42 full build",
      "then": "`<out>/akg.sqlite` holds exactly the CSV rows: per table, the row count equals the CSV's, and the sorted list of row tuples equals the CSV's (a multiset comparison, so dropped duplicates fail), with every CSV value cast by its dictionary type (INTEGER, REAL, TEXT; blanks and `unmapped` as NULL) before comparing. `PRAGMA foreign_key_check` reports no violation.\n\nEvery two-file reference exists in the table it names:\n- maps-to rows by `source` (ERM or IA);\n- review-queue rows by `kind`: `risk` is `risk_erm` then `risk_ia`; `duplicate` is `risk_erm` twice; `control` is `control_erm` then `control_ia`.\n\nThe load takes under 5 s (prototype: 7,530 published rows in 0.7 s, with foreign keys off; the build re-measures with them on and with the reconciled tables)",
      "test": "stores.test_sqlite.SqliteTests.test_ac3_every_row_lands_once_and_keys_hold",
      "status": "pass"
    },
    {
      "id": "AC-4",
      "when": "`python -m akg build` or `python -m akg load --out <dir>` runs",
      "then": "build runs generate, reconcile, then load, writing `<out>/akg.sqlite`. `--no-load` stops after reconcile, and `--no-reconcile` stops after generate. Neo4j comes in child b, and rounds in c and d.\n\n**No stale database:** `build --no-load`, `build --no-reconcile` and `akg reconcile` each remove an existing `<out>/akg.sqlite`, so a database never outlives the files it was loaded from.\n\n`akg load --out <dir>` (re)builds `<out>/akg.sqlite` for an existing build. If `reconciled/` is missing, it fails with a nonzero exit naming it. It writes to a temporary file and renames it at the end, so a failed load leaves no partial database. Loading twice gives identical rows. No table or row comes from `answer_key/`: a copy of the build without `answer_key/` loads identically.\n\n**Existing callers** (L-014):\n- `train.build_training_bank` passes `--no-load`, so the training bank's files are unchanged. But `train.py`'s source is fingerprinted, so the fingerprint moves, and with it `weights.json`'s `fingerprint` and `scores.json`'s `provenance.weights_fingerprint`. Both files are regenerated (`train`, then `score`). The evidence that nothing else moved: `git diff` of each shows exactly one changed line, the fingerprint, and the reconciled golden is unchanged. 012's currency test and 014's `test_ac3_committed_scores_are_current` must pass afterwards.\n- `tests/generator/golden.checksums()` counts only `*.csv` files outside `reconciled/`, so the generator goldens ignore `akg.sqlite` (and later `rounds.json`) and stay unchanged.\n- `tests/reconciliation/helpers.full_build` passes `--no-load`.\n- The about 10 other plain-build callers (test_determinism, test_issues, test_canonical, test_ai_text, test_batch, test_offline, score.py's regeneration) each gain one load, about 0.7 s each, roughly 7-10 s on the suite. That is stated, not hidden",
      "test": "stores.test_sqlite.SqliteTests.test_ac4_build_and_load_commands_idempotent_and_answer_key_free",
      "status": "pass"
    },
    {
      "id": "AC-5",
      "when": "docs/data-model.md and `src/features/stores/README.md` are read",
      "then": "they describe the SQLite store: `<out>/akg.sqlite`; the generated schema and how to regenerate it; the type and key rules; the cross-source columns without FOREIGN KEY and how they are checked; that the store is derived and not golden; and that the answer key is never loaded. The data model's INV-8 row notes that the Neo4j side arrives in child b",
      "test": "stores.test_sqlite.SqliteTests.test_ac5_docs_describe_the_sqlite_store",
      "status": "pass"
    }
  ],
  "epic": "003-e3-dual-stores-and-head-to-head-rounds",
  "child": "a",
  "approved": "2026-11-21",
  "approved_hash": "4cf8d88f9e753a16",
  "in_progress": "2026-11-21",
  "done": "2026-11-21"
}
```

## Why
E3 child a (O2). The head-to-head rounds need the same facts in SQLite and Neo4j. This child builds the relational side: a schema that cannot drift from the published data dictionary, and a loader that lands every published and reconciled row exactly once, with keys enforced. It also implements the `load` step of the pipeline contract in AGENTS.md.

## Data impact
- **New derived store:** `<out>/akg.sqlite`, with 47 tables (41 published files and 6 reconciled files). Nothing in E1's or E2's outputs changes. The goldens stay unchanged because `golden.checksums()` counts CSV files only. `weights.json` gets a new fingerprint (`train.py` changes) with identical coefficients.
- **New dictionary:** `src/features/stores/reconciled_dictionary.md`, describing the reconciled files in the generator's dictionary format. The columns are the ones docs/data-model.md already lists for 013.
- **Invariants:**
  - INV-6: the store never holds the answer key, tested in AC-4.
  - INV-8: the SQLite half only; parity with Neo4j comes in child b.
  - INV-10 holds by construction: per-source tables stay separate, and ERM-IA links exist only in the reconciled tables.

## Test plan
Tests go in `tests/stores/test_sqlite.py`, using one cached seed-42 full build (built with `--no-load` and loaded once by the test fixture) and a small dictionary fixture for AC-2. The whole suite stays the done-check.

**Evidence** (pre-plan prototype on 2026-11-21; a critique reproduced it): the generator's dictionary parses into 41 tables (a 311-line schema). The seed-42 build loads 7,530 rows in 0.6-0.7 s with zero violations from `foreign_key_check`, and every enum CHECK is satisfied. The sample build loads 585 rows. Every published CSV has a dictionary entry. The prototype ran with foreign keys off and without the reconciled tables; the build measures both.

**Not tested here:** Neo4j (child b) and the rounds (c and d).

## Risks
- **The dictionary is wrong or stale for a file.** Then the generated schema fails the load (CHECK or FOREIGN KEY), which is the point. E1's own test (`checks.data_dictionary`) already ties the dictionary to the output.
- **Reconciled columns that point to either source** can't be foreign keys; AC-3 checks them explicitly.
- **Suite time:** about 10 plain-build callers each gain about 0.7 s (roughly 7-10 s in all). Reconciliation helpers and the training bank use `--no-load`, and store tests share one build.
- **Partial or stale databases:** handled by AC-4's atomic write and stale-file removal.

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
