# Sample pack for realism review

Change `005-sample-pack-for-realism-review` · objective **O3**: It shows, and measures, the realistic hard part: reconciling ERM's and IA's separate risk taxonomies, risks and controls into one framework (ERM's Basel-style taxonomy). Signal: precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue rather than being merged silently.

## Why
The milestone's riskiest assumption is that the synthetic bank reads as real to audit professionals (O3's numbers mean nothing otherwise). This change builds a thin, working slice of the real generator and renders its output as a sample pack the owner reviews before b-e scale it up, and it settles R2 (templated vs AI-written text).

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `python -m akg build --size sample --seed 42 --out <dir>` runs on a fresh checkout | it writes the file layout in Data impact: one CSV per shared entity type, one per source (erm, ia) for TAXONOMY_NODE, RISK and CONTROL, and one per (from, label, to) relationship, split by source wherever one end is a sourced entity; CANONICAL_*, maps_to and ia_maps_to_erm appear only in answer_key/; `tested` has only `audit_tested_control_ia.csv` (audits test IA controls only, per the epic); every relationship CSV has at least one row; every entity CSV has 1-20 rows except the taxonomy files (up to 30 each: all L1 nodes plus a thin L2-L3 branch under each) | `generator.test_sample_build.SampleBuildTests.test_ac1_sample_build_writes_every_entity_and_edge` | pass | PASS |
| AC-2 | the sample build has run | answer_key/ holds taxonomy_map.csv, risk_clusters.csv, control_clusters.csv and scenarios.csv (header only), passing the epic's consistency rules, and contains at least 5 cross-source risk matches, 5 cross-source control matches, 1 within-ERM duplicate, 1 unmapped IA node and 1 misfiled IA risk; and, computed in the test with scikit-learn TF-IDF on the published descriptions, separately for risks and for controls and for both `--text templated` and `--text ai`, at least one cross-source non-matching pair whose cosine is at or above the median cosine of true matching pairs (a hard negative) | `generator.test_answer_key.AnswerKeyTests.test_ac2_answer_key_consistent_and_covers_each_case` | pass | PASS |
| AC-3 | the build runs twice with seed 42 at default settings (sample size, templated text) | every output file is UTF-8 without BOM with LF line endings, and its SHA-256 matches tests/golden/checksums.sha256 (INV-7) | `generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums` | pass | PASS |
| AC-4 | the sample build has run, the AI text is committed, and the test has generated a sample pack to a temp path | every text column in the data dictionary is marked either `name_list: <list>` or `free_text` (the test fails on an unmarked text column); every `name_list` column takes its values only from that list in src/features/generator/names/; no list entry, and no token sequence in any text cell of any output CSV, the committed AI text or the generated pack, matches (case-insensitive, whole-token sequence) the committed deny-list of real US bank, vendor and core-system names (INV-9). Deny-list entries are distinctive forms (e.g. 'KeyBank', 'Regions Bank', 'Citizens Financial'), never a single common word, so 'key control' does not match. Also, every capitalized word or run of capitalized words in the AI text (ignoring the sentence-initial word) is on a name list or on a committed allow-list of domain terms (e.g. 'General Ledger', 'ACH', 'SOX'), so the AI cannot invent unlisted one-word or multi-word names | `generator.test_names.NameTests.test_ac4_inv9_names_from_lists_and_no_denied_name_anywhere` | pass | PASS |
| AC-5 | the build runs in a subprocess whose socket connections raise, once with `--text templated` and once with `--text ai` | both complete, and neither `anthropic` nor `yaml` is in sys.modules afterwards | `generator.test_offline.OfflineTests.test_ac5_build_is_offline_and_never_imports_anthropic` | pass | PASS |
| AC-6 | the build runs with `--text ai --text-dir <tmp copy of the committed AI text>` where the copy has one entry removed, one input hash altered, or one extra key that matches no item | the build fails naming the key (removed, altered), or `python -m akg check-text --text-dir <dir>` (the orphan check) fails naming the key (extra); with an unaltered copy both succeed | `generator.test_ai_text.AiTextTests.test_ac6_missing_stale_or_orphan_ai_text_fails` | pass | PASS |
| AC-7 | two items share a true cluster in the answer key, in a build with `--text templated` and in one with `--text ai` | their published IDs share no numeric part; their descriptions share no full template sentence; their TF-IDF cosine is below 0.90 and the median cosine of matched pairs is below 0.70 (so AI paraphrases are not near-copies); owner/frequency/type are not all equal (controls); and the Spearman rank correlation between matched clusters' row positions in risk_erm.csv / control_erm.csv and in risk_ia.csv / control_ia.csv has absolute value below 0.8 | `generator.test_leakage.LeakageTests.test_ac7_matched_items_share_no_id_sentence_attributes_or_order` | pass | PASS |
| AC-8 | `python -m akg sample-pack --out <path>` runs (default path research/r2-synthetic-text-realism/sample_pack.md) | it writes a markdown pack with every entity type's rows, templated and AI descriptions side by side for risks, controls and issues, every name list in full (for the owner's one-time INV-9 review), and a review table (entity type | realistic? | notes) plus a text-choice line for the owner; the test writes to a temp path, never the committed file | `generator.test_sample_pack.SamplePackTests.test_ac8_sample_pack_shows_every_entity_and_both_text_variants` | pass | PASS |
| AC-9 | the sample build has run | every CSV and column in the output, including the answer_key/ files, is listed in src/features/generator/README.md (the data dictionary) with type and allowed values, and the README lists nothing the output lacks | `generator.test_data_dictionary.DataDictionaryTests.test_ac9_data_dictionary_matches_output` | pass | PASS |
| AC-10 | requirements.txt is read | every line is an exact pin (`name==x.y.z`); every pinned package is on the approved list (anthropic, scikit-learn, pandas, neo4j, networkx, pyyaml) or in the transitive dependency closure of one (resolved via importlib.metadata in the installed venv), so numpy, six, h11, pydantic-core and the like are pinned too | `test_requirements.RequirementsTests.test_ac10_requirements_exactly_pinned_and_approved` | pass | PASS |
| AC-11 | the build runs with seed 42 and `--count REGULATION=5` (sample default 8; an early type with few dependents), and separately with `--count ISSUE=5` (sample default 15; the last type) | the test first asserts each override differs from the default, then that in the first run every CSV whose file name does not contain `regulation`, and in the second every CSV whose name contains no `issue`, is byte-identical to the default run, proving per-type and per-relationship random streams are independent | `generator.test_determinism.DeterminismTests.test_ac11_changing_one_type_count_leaves_other_types_unchanged` | pass | PASS |
| AC-12 | the sample build has run | every ID in every relationship CSV exists in the entity file its column names, and in that source's file when the relationship file has a source suffix; no relationship row links an ERM item to an IA item (the new no-cross-source rule) | `generator.test_referential.ReferentialTests.test_ac12_relationship_ids_exist_and_never_cross_sources` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/generator/****: `src/features/generator/__init__.py`, `src/features/generator/cli.py`, `src/features/generator/generate.py`, `src/features/generator/library.py`, `src/features/generator/names.py`, `src/features/generator/names/allow_terms.txt`, `src/features/generator/names/deny_list.txt`, `src/features/generator/names/first_names.txt`, `src/features/generator/names/institution.txt`, `src/features/generator/names/last_names.txt`, `src/features/generator/names/regulations.txt`, `src/features/generator/names/systems.txt`, `src/features/generator/names/titles.txt`, `src/features/generator/names/vendors.txt`, `src/features/generator/rng.py`, `src/features/generator/sample_pack.py`, `src/features/generator/text/ai_text.jsonl`, `src/features/generator/write_text.py`, `src/features/generator/writer.py`
3. **akg/****: `akg/__init__.py`, `akg/__main__.py`
4. **requirements.txt**: `requirements.txt`
5. **.gitattributes**: `.gitattributes`
6. **Tests**: `tests/__init__.py`, `tests/generator/__init__.py`, `tests/generator/dictionary.py`, `tests/generator/golden.py`, `tests/generator/helpers.py`, `tests/generator/test_ai_text.py`, `tests/generator/test_answer_key.py`, `tests/generator/test_data_dictionary.py`, `tests/generator/test_determinism.py`, `tests/generator/test_leakage.py`, `tests/generator/test_names.py`, `tests/generator/test_offline.py`, `tests/generator/test_referential.py`, `tests/generator/test_sample_build.py`, `tests/generator/test_sample_pack.py`, `tests/golden/checksums.sha256`, `tests/test_requirements.py`

## Data impact
- **File layout (one choice, used by every criterion, the checksums, the data dictionary, b-e and E3a).** ERM and IA are separate systems, so their data is published separately:
  - Shared entities, one file each: `segment`, `business_unit`, `auditable_entity`, `process`, `system`, `person`, `regulation`, `audit`, `issue`.
  - Sourced entities, one file per source: `taxonomy_node_erm` / `_ia`, `risk_erm` / `_ia`, `control_erm` / `_ia`. IDs and row order are shuffled independently per file.
  - Relationships, named `<from>_<label>_<to>.csv`, with a source suffix when either end is sourced (e.g. `control_mitigates_risk_erm.csv`, `issue_against_control_ia.csv`, `control_owned_by_person_erm.csv`).
  - **New rule: no relationship crosses sources.** ERM controls mitigate ERM risks, IA controls IA risks; ERM-IA links exist only in the answer key. Added to `docs/data-model.md` in this change as an invariant enforced by AC-12.
- **Random streams:** each entity type and each relationship file draws from its own stream, sub-seeded from the master seed and the type or file name. Sample default counts per type are fixed in the generator's config and listed in the data dictionary.
- Columns are provisional; b-e may add columns and update the data dictionary.
- **Committed AI text:** `src/features/generator/text/ai_text.jsonl`, one JSON object per line (`key`, `input_hash`, `text`), sorted by key, UTF-8, LF. That folder is the `--text-dir` default.
- **Published description:** the build writes templated text by default (`--text templated`). `--text ai` swaps in the committed AI text. All criteria and golden checksums use the default until R2 is GO; if R2 picks AI text, child b switches the default and regenerates the checksums.
- First answer-key files, in the epic's schema.
- Invariants enforced here: INV-7 (golden checksums), INV-9 (names + deny-list over all text). Replaces their `TBD (E1)` in `docs/data-model.md` with the AC-3 and AC-4 test names. INV-1, 2, 4, 5 are left to b-e.
- The generator itself uses only the standard library (`random`, `csv`, `hashlib`), so output bytes never depend on numpy or pandas versions; scikit-learn is used only in tests.
- `akg/` sits at the repo root; `python -m akg` run from the root imports the generator as `src.features.generator` (namespace package, no packaging files needed).

## Risks
- Sample size too small to judge realism of ratios: the review asks about text and attributes, not distributions (stated in the pack header).
- Windows/Linux byte differences: AC-3 written first, with explicit `newline="\n"` and encoding in the writer.
- AI text keys drift as code changes: generate AI text last (slice 6), after the internal keys are stable.
- AI text mentioning real names or paraphrasing its match too closely: AC-4 and AC-7 run on the AI variant; the generation prompt gives the model only the project's names and the item's own facts.
- Deny-list completeness: it is a floor, backed by the owner's one-time review of the name lists in the pack.
- Thin slice grows into the full generator: rules beyond what the criteria need are out of scope (below).

## Deliberately not in this PR
- Full sizes, quotas, F1 baseline bands, hard-negative rates: c and d.
- Taxonomy breadth and organization realism rules: b.
- Planted scenarios and INV-4/INV-5 date and link rules: e.
- Loading into SQLite or Neo4j, CI workflow: E3.

Parked for later:
- 2026-11-20 E1 children c-e: AI-text keys for issues are positional (issue:{j}); --count ISSUE/AUDIT with --text ai breaks them. Key issues by a stable natural key before full-size AI text (review of 005) (from 005-sample-pack-for-realism-review)
- 2026-11-20 E1 child d: matched ERM/IA controls always share type, nature and frequency (9 of 9 in the sample); AC-7 passes only via differing owners. Add realistic attribute disagreement (review of 005) (from 005-sample-pack-for-realism-review)

## Lessons recorded
- L-001 Owner-run commands: copy-paste blocks, never an editor
- L-002 AI rewrites invent facts unless code enforces the rule
- L-003 Cross-source text needs shared domain vocabulary for realistic near-misses
- L-004 capitan rescue runs from main and leaves files uncommitted

## Verification
- Plan critique: skipped (Five critique rounds; all findings fixed)
- Code review: PASS on code fingerprint `7969af3bf7a64d98`
- Size: 40 code files, +2700 / -0 lines
