# SQLite schema and loader

Change `015-sqlite-schema-and-loader` · objective **O2**: A data scientist finds every claim credible and reproducible. Signal: one command reproduces every number on the page from a fresh clone; CI is green; every SQL-vs-Cypher round has a test proving both return the same answer; the page makes no claim without a test or a cited method.

## Why
E3 child a (O2). The head-to-head rounds need the same facts in SQLite and Neo4j. This child builds the relational side: a schema that cannot drift from the published data dictionary, and a loader that lands every published and reconciled row exactly once, with keys enforced. It also implements the `load` step of the pipeline contract in AGENTS.md.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `python -m src.features.stores.schema` runs | it writes `src/features/stores/schema.sql`, generated from two data dictionaries in the same Markdown table format:
- the generator's (`src/features/generator/README.md`, 41 published files);
- a new `src/features/stores/reconciled_dictionary.md` for the 6 reconciled files.

There is one table per file, named after it; answer-key files get none. A test asserts that the committed `schema.sql` equals a fresh generation, that every published and reconciled CSV of the seed-42 build has a table, and that no table exists for an answer-key file | `stores.test_sqlite.SqliteTests.test_ac1_schema_is_generated_from_the_dictionaries` | pass | PASS |
| AC-2 | the schema is generated | it follows these rules:
- Columns appear in dictionary order.
- `id` becomes TEXT. `primary key` becomes the table's PRIMARY KEY; a table with no `primary key` column gets a composite PRIMARY KEY over its `id` columns.
- A value that is exactly one `x.csv` becomes a FOREIGN KEY to `x`'s primary key.
- A value naming two files with `by` (for example ``risk_erm.csv` or `risk_ia.csv` by `source``) gets no FOREIGN KEY; AC-3 checks those columns instead.
- `enum` becomes TEXT with a CHECK on the listed values; `int` becomes INTEGER; the new `decimal` type becomes REAL; `date` and `text` become TEXT.
- A column is NOT NULL unless its values mention `blank` or `unmapped`. A blank cell loads as NULL, and so does the literal `unmapped` in a column whose values mention it (only `ia_maps_to_erm.erm_node_id`).

`reconciled_dictionary.md` uses these forms for the reconciled files: `score` is `decimal`; `logit` is `decimal`, blank for unmerged items in the maps-to files; the maps-to item IDs and the review queue's `item_a` and `item_b` are two-file values, and `erm_node_id` is ``taxonomy_node_erm.csv`, or `unmapped` (stored as NULL)``. `ia_maps_to_erm.ia_node_id` is marked `primary key` (one row per IA node), and so is each canonical table's ID. The tables are created and loaded in foreign-key dependency order, with `PRAGMA foreign_keys = ON` throughout. | `stores.test_sqlite.SqliteTests.test_ac2_type_and_key_rules (a hand-written two-table dictionary fixture with an enum, a blank-allowed date, a foreign key and a relationship table)` | pass | PASS |
| AC-3 | the load runs on the seed-42 full build | `<out>/akg.sqlite` holds exactly the CSV rows: per table, the row count equals the CSV's, and the sorted list of row tuples equals the CSV's (a multiset comparison, so dropped duplicates fail), with every CSV value cast by its dictionary type (INTEGER, REAL, TEXT; blanks and `unmapped` as NULL) before comparing. `PRAGMA foreign_key_check` reports no violation.

Every two-file reference exists in the table it names:
- maps-to rows by `source` (ERM or IA);
- review-queue rows by `kind`: `risk` is `risk_erm` then `risk_ia`; `duplicate` is `risk_erm` twice; `control` is `control_erm` then `control_ia`.

The load takes under 5 s (prototype: 7,530 published rows in 0.7 s, with foreign keys off; the build re-measures with them on and with the reconciled tables) | `stores.test_sqlite.SqliteTests.test_ac3_every_row_lands_once_and_keys_hold` | pass | PASS |
| AC-4 | `python -m akg build` or `python -m akg load --out <dir>` runs | build runs generate, reconcile, then load, writing `<out>/akg.sqlite`. `--no-load` stops after reconcile, and `--no-reconcile` stops after generate. Neo4j comes in child b, and rounds in c and d.

**No stale database:** `build --no-load`, `build --no-reconcile` and `akg reconcile` each remove an existing `<out>/akg.sqlite`, so a database never outlives the files it was loaded from.

`akg load --out <dir>` (re)builds `<out>/akg.sqlite` for an existing build. If `reconciled/` is missing, it fails with a nonzero exit naming it. It writes to a temporary file and renames it at the end, so a failed load leaves no partial database. Loading twice gives identical rows. No table or row comes from `answer_key/`: a copy of the build without `answer_key/` loads identically.

**Existing callers** (L-014):
- `train.build_training_bank` passes `--no-load`, so the training bank's files are unchanged. But `train.py`'s source is fingerprinted, so the fingerprint moves, and with it `weights.json`'s `fingerprint` and `scores.json`'s `provenance.weights_fingerprint`. Both files are regenerated (`train`, then `score`). The evidence that nothing else moved: `git diff` of each shows exactly one changed line, the fingerprint, and the reconciled golden is unchanged. 012's currency test and 014's `test_ac3_committed_scores_are_current` must pass afterwards.
- `tests/generator/golden.checksums()` counts only `*.csv` files outside `reconciled/`, so the generator goldens ignore `akg.sqlite` (and later `rounds.json`) and stay unchanged.
- `tests/reconciliation/helpers.full_build` passes `--no-load`.
- The about 10 other plain-build callers (test_determinism, test_issues, test_canonical, test_ai_text, test_batch, test_offline, score.py's regeneration) each gain one load, about 0.7 s each, roughly 7-10 s on the suite. That is stated, not hidden | `stores.test_sqlite.SqliteTests.test_ac4_build_and_load_commands_idempotent_and_answer_key_free` | pass | PASS |
| AC-5 | docs/data-model.md and `src/features/stores/README.md` are read | they describe the SQLite store: `<out>/akg.sqlite`; the generated schema and how to regenerate it; the type and key rules; the cross-source columns without FOREIGN KEY and how they are checked; that the store is derived and not golden; and that the answer key is never loaded. The data model's INV-8 row notes that the Neo4j side arrives in child b | `stores.test_sqlite.SqliteTests.test_ac5_docs_describe_the_sqlite_store` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `src/features/stores/schema.sql`, `docs/data-model.md`
2. **src/features/stores/****: `src/features/stores/__init__.py`, `src/features/stores/reconciled_dictionary.md`, `src/features/stores/schema.py`, `src/features/stores/sqlite_store.py`
3. **akg/****: `akg/__main__.py`
4. **src/features/reconciliation/train.py**: `src/features/reconciliation/train.py`
5. **src/features/reconciliation/weights.json**: `src/features/reconciliation/weights.json`
6. **src/features/reconciliation/scores.json**: `src/features/reconciliation/scores.json`
7. **Tests**: `tests/generator/golden.py`, `tests/reconciliation/helpers.py`, `tests/stores/__init__.py`, `tests/stores/test_sqlite.py`

## Data impact
- **New derived store:** `<out>/akg.sqlite`, with 47 tables (41 published files and 6 reconciled files). Nothing in E1's or E2's outputs changes. The goldens stay unchanged because `golden.checksums()` counts CSV files only. `weights.json` gets a new fingerprint (`train.py` changes) with identical coefficients.
- **New dictionary:** `src/features/stores/reconciled_dictionary.md`, describing the reconciled files in the generator's dictionary format. The columns are the ones docs/data-model.md already lists for 013.
- **Invariants:**
  - INV-6: the store never holds the answer key, tested in AC-4.
  - INV-8: the SQLite half only; parity with Neo4j comes in child b.
  - INV-10 holds by construction: per-source tables stay separate, and ERM-IA links exist only in the reconciled tables.

## Risks
- **The dictionary is wrong or stale for a file.** Then the generated schema fails the load (CHECK or FOREIGN KEY), which is the point. E1's own test (`checks.data_dictionary`) already ties the dictionary to the output.
- **Reconciled columns that point to either source** can't be foreign keys; AC-3 checks them explicitly.
- **Suite time:** about 10 plain-build callers each gain about 0.7 s (roughly 7-10 s in all). Reconciliation helpers and the training bank use `--no-load`, and store tests share one build.
- **Partial or stale databases:** handled by AC-4's atomic write and stale-file removal.

## Deliberately not in this PR
- Neo4j and parity (child b); rounds (c and d); CI (e).
- Indexes for query speed: added in c if a round needs them; no speed claims either way.

Parked for later:
- 2026-11-21 015 review minors: a plain build failing at reconcile or load leaves the previous akg.sqlite beside new CSVs (remove it right after generation); test a mid-load failure so the partial-file cleanup runs; reject malformed CSV rows instead of zip dropping cells; clean errors naming the table for constraint failures and missing CSVs; close the file in test_sqlite line 108 (from 015-sqlite-schema-and-loader)

## Lessons recorded
- L-016 A fingerprint over source code ripples into every artifact that copies it

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `d15489fa6bb969bf`
- Size: 13 code files, +832 / -14 lines
