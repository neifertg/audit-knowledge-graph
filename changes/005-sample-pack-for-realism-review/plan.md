# Sample pack for realism review

```json plan
{
  "id": "005-sample-pack-for-realism-review",
  "tier": "standard",
  "status": "done",
  "created": "2026-11-19",
  "objective": "O3",
  "areas": [
    "src/features/generator/**",
    "tests/**",
    "docs/data-model.md",
    "akg/**",
    "requirements.txt",
    ".gitattributes",
    "research/r2-synthetic-text-realism/**"
  ],
  "timebox": "2 working days of build time. Past this, stop and re-plan with `capitan revise` (e.g. moving AI text and its criteria AC-6, AC-4 AI part and AC-8's AI column into a new child); never drop criteria silently.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m akg build --size sample --seed 42 --out <dir>` runs on a fresh checkout",
      "then": "it writes the file layout in Data impact: one CSV per shared entity type, one per source (erm, ia) for TAXONOMY_NODE, RISK and CONTROL, and one per (from, label, to) relationship, split by source wherever one end is a sourced entity; CANONICAL_*, maps_to and ia_maps_to_erm appear only in answer_key/; `tested` has only `audit_tested_control_ia.csv` (audits test IA controls only, per the epic); every relationship CSV has at least one row; every entity CSV has 1-20 rows except the taxonomy files (up to 30 each: all L1 nodes plus a thin L2-L3 branch under each)",
      "test": "generator.test_sample_build.SampleBuildTests.test_ac1_sample_build_writes_every_entity_and_edge",
      "status": "pass"
    },
    {
      "id": "AC-2",
      "when": "the sample build has run",
      "then": "answer_key/ holds taxonomy_map.csv, risk_clusters.csv, control_clusters.csv and scenarios.csv (header only), passing the epic's consistency rules, and contains at least 5 cross-source risk matches, 5 cross-source control matches, 1 within-ERM duplicate, 1 unmapped IA node and 1 misfiled IA risk; and, computed in the test with scikit-learn TF-IDF on the published descriptions, separately for risks and for controls and for both `--text templated` and `--text ai`, at least one cross-source non-matching pair whose cosine is at or above the median cosine of true matching pairs (a hard negative)",
      "test": "generator.test_answer_key.AnswerKeyTests.test_ac2_answer_key_consistent_and_covers_each_case",
      "status": "pass"
    },
    {
      "id": "AC-3",
      "when": "the build runs twice with seed 42 at default settings (sample size, templated text)",
      "then": "every output file is UTF-8 without BOM with LF line endings, and its SHA-256 matches tests/golden/checksums.sha256 (INV-7)",
      "test": "generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums",
      "status": "pass"
    },
    {
      "id": "AC-4",
      "when": "the sample build has run, the AI text is committed, and the test has generated a sample pack to a temp path",
      "then": "every text column in the data dictionary is marked either `name_list: <list>` or `free_text` (the test fails on an unmarked text column); every `name_list` column takes its values only from that list in src/features/generator/names/; no list entry, and no token sequence in any text cell of any output CSV, the committed AI text or the generated pack, matches (case-insensitive, whole-token sequence) the committed deny-list of real US bank, vendor and core-system names (INV-9). Deny-list entries are distinctive forms (e.g. 'KeyBank', 'Regions Bank', 'Citizens Financial'), never a single common word, so 'key control' does not match. Also, every capitalized word or run of capitalized words in the AI text (ignoring the sentence-initial word) is on a name list or on a committed allow-list of domain terms (e.g. 'General Ledger', 'ACH', 'SOX'), so the AI cannot invent unlisted one-word or multi-word names",
      "test": "generator.test_names.NameTests.test_ac4_inv9_names_from_lists_and_no_denied_name_anywhere",
      "status": "pass"
    },
    {
      "id": "AC-5",
      "when": "the build runs in a subprocess whose socket connections raise, once with `--text templated` and once with `--text ai`",
      "then": "both complete, and neither `anthropic` nor `yaml` is in sys.modules afterwards",
      "test": "generator.test_offline.OfflineTests.test_ac5_build_is_offline_and_never_imports_anthropic",
      "status": "pass"
    },
    {
      "id": "AC-6",
      "when": "the build runs with `--text ai --text-dir <tmp copy of the committed AI text>` where the copy has one entry removed, one input hash altered, or one extra key that matches no item",
      "then": "the build fails naming the key (removed, altered), or `python -m akg check-text --text-dir <dir>` (the orphan check) fails naming the key (extra); with an unaltered copy both succeed",
      "test": "generator.test_ai_text.AiTextTests.test_ac6_missing_stale_or_orphan_ai_text_fails",
      "status": "pass"
    },
    {
      "id": "AC-7",
      "when": "two items share a true cluster in the answer key, in a build with `--text templated` and in one with `--text ai`",
      "then": "their published IDs share no numeric part; their descriptions share no full template sentence; their TF-IDF cosine is below 0.90 and the median cosine of matched pairs is below 0.70 (so AI paraphrases are not near-copies); owner/frequency/type are not all equal (controls); and the Spearman rank correlation between matched clusters' row positions in risk_erm.csv / control_erm.csv and in risk_ia.csv / control_ia.csv has absolute value below 0.8",
      "test": "generator.test_leakage.LeakageTests.test_ac7_matched_items_share_no_id_sentence_attributes_or_order",
      "status": "pass"
    },
    {
      "id": "AC-8",
      "when": "`python -m akg sample-pack --out <path>` runs (default path research/r2-synthetic-text-realism/sample_pack.md)",
      "then": "it writes a markdown pack with every entity type's rows, templated and AI descriptions side by side for risks, controls and issues, every name list in full (for the owner's one-time INV-9 review), and a review table (entity type | realistic? | notes) plus a text-choice line for the owner; the test writes to a temp path, never the committed file",
      "test": "generator.test_sample_pack.SamplePackTests.test_ac8_sample_pack_shows_every_entity_and_both_text_variants",
      "status": "pass"
    },
    {
      "id": "AC-9",
      "when": "the sample build has run",
      "then": "every CSV and column in the output, including the answer_key/ files, is listed in src/features/generator/README.md (the data dictionary) with type and allowed values, and the README lists nothing the output lacks",
      "test": "generator.test_data_dictionary.DataDictionaryTests.test_ac9_data_dictionary_matches_output",
      "status": "pass"
    },
    {
      "id": "AC-10",
      "when": "requirements.txt is read",
      "then": "every line is an exact pin (`name==x.y.z`); every pinned package is on the approved list (anthropic, scikit-learn, pandas, neo4j, networkx, pyyaml) or in the transitive dependency closure of one (resolved via importlib.metadata in the installed venv), so numpy, six, h11, pydantic-core and the like are pinned too",
      "test": "test_requirements.RequirementsTests.test_ac10_requirements_exactly_pinned_and_approved",
      "status": "pass"
    },
    {
      "id": "AC-11",
      "when": "the build runs with seed 42 and `--count REGULATION=5` (sample default 8; an early type with few dependents), and separately with `--count ISSUE=5` (sample default 15; the last type)",
      "then": "the test first asserts each override differs from the default, then that in the first run every CSV whose file name does not contain `regulation`, and in the second every CSV whose name contains no `issue`, is byte-identical to the default run, proving per-type and per-relationship random streams are independent",
      "test": "generator.test_determinism.DeterminismTests.test_ac11_changing_one_type_count_leaves_other_types_unchanged",
      "status": "pass"
    },
    {
      "id": "AC-12",
      "when": "the sample build has run",
      "then": "every ID in every relationship CSV exists in the entity file its column names, and in that source's file when the relationship file has a source suffix; no relationship row links an ERM item to an IA item (the new no-cross-source rule)",
      "test": "generator.test_referential.ReferentialTests.test_ac12_relationship_ids_exist_and_never_cross_sources",
      "status": "pass"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "a",
  "approved": "2026-11-20",
  "approved_hash": "81a70753a75aa8df",
  "critique_skipped": "Five critique rounds; all findings fixed",
  "in_progress": "2026-11-20",
  "done": "2026-11-20"
}
```

## Why
The milestone's riskiest assumption is that the synthetic bank reads as real to audit professionals (O3's numbers mean nothing otherwise). This change builds a thin, working slice of the real generator and renders its output as a sample pack the owner reviews before b-e scale it up, and it settles R2 (templated vs AI-written text).

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

## Test plan
- Done check: `python -m unittest discover -s tests -v`. Tests are `unittest.TestCase` methods; `tests/` and `tests/generator/` have `__init__.py`; the names in the criteria are the dotted names that verbose output prints, and each must appear there as `ok` (not skipped) before its criterion is marked pass.
- Real files, real build, no mocks; tests build into a temp directory and never write committed files.
- TF-IDF settings are fixed in one test helper used by AC-2 and AC-7: scikit-learn `TfidfVectorizer(lowercase=True, ngram_range=(1, 2))`, fit per comparison on all ERM and IA descriptions of that kind (risks or controls).
- `.venv/` and `__pycache__/` must be ignored by `.gitignore` (governance; the owner's change). The builder never stages either.
- AC-5 blocks network with a socket guard in the subprocess only; it is a guard, not a mock of our code.
- The AI-text script (`write_text.py`) is not run by tests; it is run once by hand (key read at runtime from `~/.claude/secrets.yaml` with PyYAML, approved by the owner 2026-11-20 for script-only use; AC-5 proves the build never needs it), and its committed output is what AC-4 and AC-6 check.
- Not tested here: F1 bands, quotas, hard-negative rates, planted scenarios and full sizes (meaningless at ~15 rows; c-e own them). The owner's realism verdict is a manual gate recorded in R2's decision.md, not a test.

## Gate hand-off
When every criterion passes, `sample_pack.md` (generated by the command at its default path) is committed with the change. The owner fills its review table and records the verdict and text choice in `research/r2-synthetic-text-realism/decision.md`. Both are research, so they reach the base branch per rule 9 (`capitan rescue` if needed) before b's start is checked. The pack's header tells the reviewer that taxonomy breadth and population sizes belong to b-e; the review is about whether rows and text read as real.

## Risks
- Sample size too small to judge realism of ratios: the review asks about text and attributes, not distributions (stated in the pack header).
- Windows/Linux byte differences: AC-3 written first, with explicit `newline="\n"` and encoding in the writer.
- AI text keys drift as code changes: generate AI text last (slice 6), after the internal keys are stable.
- AI text mentioning real names or paraphrasing its match too closely: AC-4 and AC-7 run on the AI variant; the generation prompt gives the model only the project's names and the item's own facts.
- Deny-list completeness: it is a floor, backed by the owner's one-time review of the name lists in the pack.
- Thin slice grows into the full generator: rules beyond what the criteria need are out of scope (below).

## Out of scope
- Full sizes, quotas, F1 baseline bands, hard-negative rates: c and d.
- Taxonomy breadth and organization realism rules: b.
- Planted scenarios and INV-4/INV-5 date and link rules: e.
- Loading into SQLite or Neo4j, CI workflow: E3.

## Relevant lessons
- None found for: sample, pack, realism, review, generator, seed, text. New project.

## Slices
1. `.venv`, `requirements.txt`, `akg` package with `build` (flags `--size`, `--seed`, `--out`, `--count TYPE=N`, `--text`, `--text-dir`), `sample-pack` and `check-text` commands, `.gitattributes`; AC-10.
2. Name lists and deny-list; AC-4 (name-column part).
3. Entity and edge generators at sample size with sub-seeded streams, plus the answer key; AC-1, AC-2, AC-7 (templated), AC-12.
4. Writer encoding and golden checksums; AC-3, AC-5, AC-11.
5. Data dictionary README; AC-9.
6. `write_text.py`, run once, committed text with input hashes; AC-6; AC-2, AC-4 and AC-7 on the AI variant.
7. Sample pack renderer and review table; AC-8, AC-4 (pack part). Update `docs/data-model.md`.
