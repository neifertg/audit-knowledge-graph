# Sample pack for realism review

```json plan
{
  "id": "005-sample-pack-for-realism-review",
  "tier": "standard",
  "status": "draft",
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
  "timebox": "2 working days of build time. If slices 1-5 take more than 1.5 days, cut slice 6 (AI text) into its own change and show only templated text in the first pack. Past 2 days, stop and re-plan.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m akg build --size sample --seed 42 --out <dir>` runs on a fresh checkout",
      "then": "it writes one CSV per entity type and one per (from, label, to) relationship in the ER diagram (so issue_against_control.csv and issue_against_risk.csv, control_owned_by_person.csv and issue_owned_by_person.csv are separate), excluding CANONICAL_*, maps_to and ia_maps_to_erm (answer key only); every relationship CSV has at least one row; every entity CSV has 1-20 rows except TAXONOMY_NODE (up to 60: all ERM and IA L1 nodes plus a thin L2-L3 branch under each)",
      "test": "tests/generator/test_sample_build.py::test_ac1_sample_build_writes_every_entity_and_edge",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the sample build has run",
      "then": "answer_key/ holds taxonomy_map.csv, risk_clusters.csv, control_clusters.csv and scenarios.csv (header only), passing the epic's consistency rules, and contains at least one cross-source risk match, cross-source control match, within-ERM duplicate, unmapped IA node and misfiled IA risk; and, computed in the test with scikit-learn TF-IDF on the published descriptions, at least one cross-source non-matching pair whose cosine is at or above the median cosine of true matching pairs (a hard negative)",
      "test": "tests/generator/test_answer_key.py::test_ac2_answer_key_consistent_and_covers_each_case",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the build runs twice with seed 42 at default settings (sample size, templated text)",
      "then": "every output file is UTF-8 without BOM with LF line endings, and its SHA-256 matches tests/golden/checksums.sha256 (INV-7)",
      "test": "tests/generator/test_determinism.py::test_ac3_inv7_output_matches_golden_checksums",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the sample build, the committed AI text and the sample pack exist",
      "then": "every name column takes its values only from the lists in src/features/generator/names/; no list entry, and no token sequence in any text cell of any output CSV, the committed AI text or sample_pack.md, matches (case-insensitive, whole-token) the committed deny-list of real US bank, vendor and core-system names (INV-9)",
      "test": "tests/generator/test_names.py::test_ac4_inv9_names_from_lists_and_no_denied_name_anywhere",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the build runs in a subprocess whose socket connections raise",
      "then": "it completes, and `anthropic` is not in sys.modules afterwards",
      "test": "tests/generator/test_offline.py::test_ac5_build_is_offline_and_never_imports_anthropic",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "the build runs with `--text ai --text-dir <tmp copy of the committed AI text>` where the copy has one entry removed, one input hash altered, or one extra key that matches no item",
      "then": "the build fails naming the key (removed, altered), or the orphan check fails naming the key (extra); with an unaltered copy the build succeeds",
      "test": "tests/generator/test_ai_text.py::test_ac6_missing_stale_or_orphan_ai_text_fails",
      "status": "pending"
    },
    {
      "id": "AC-7",
      "when": "two items share a true cluster in the answer key",
      "then": "their published IDs share no numeric part, their descriptions share no full template sentence, owner/frequency/type are not all equal (controls), and the order of matched clusters in the ERM CSV differs from their order in the IA CSV",
      "test": "tests/generator/test_leakage.py::test_ac7_matched_items_share_no_id_sentence_attributes_or_order",
      "status": "pending"
    },
    {
      "id": "AC-8",
      "when": "`python -m akg sample-pack --out <path>` runs (default path research/r2-synthetic-text-realism/sample_pack.md)",
      "then": "it writes a markdown pack with every entity type's rows, templated and AI descriptions side by side for risks, controls and issues, and a review table (entity type | realistic? | notes) plus a text-choice line for the owner; the test writes to a temp path, never the committed file",
      "test": "tests/generator/test_sample_pack.py::test_ac8_sample_pack_shows_every_entity_and_both_text_variants",
      "status": "pending"
    },
    {
      "id": "AC-9",
      "when": "the sample build has run",
      "then": "every CSV and column in the output is listed in src/features/generator/README.md (the data dictionary) with type and allowed values, and the README lists nothing the output lacks",
      "test": "tests/generator/test_data_dictionary.py::test_ac9_data_dictionary_matches_output",
      "status": "pending"
    },
    {
      "id": "AC-10",
      "when": "requirements.txt is read",
      "then": "every line is an exact pin (`name==x.y.z`) of a package on the approved list (anthropic, scikit-learn, pandas, neo4j, networkx)",
      "test": "tests/test_requirements.py::test_ac10_requirements_exactly_pinned_and_approved",
      "status": "pending"
    },
    {
      "id": "AC-11",
      "when": "the build runs with seed 42 and `--count ISSUE=5` (instead of the sample default)",
      "then": "every CSV not derived from issues (all except issue.csv, audit_raised_issue.csv, issue_against_control.csv, issue_against_risk.csv, issue_owned_by_person.csv) is byte-identical to the default run, proving per-type random streams are independent",
      "test": "tests/generator/test_determinism.py::test_ac11_changing_one_type_count_leaves_other_types_unchanged",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "a"
}
```

## Why
The milestone's riskiest assumption is that the synthetic bank reads as real to audit professionals (O3's numbers mean nothing otherwise). This change builds a thin, working slice of the real generator and renders its output as a sample pack the owner reviews before b-e scale it up, and it settles R2 (templated vs AI-written text).

## Data impact
- Creates first, sample-size versions of every non-canonical entity and edge in `docs/data-model.md`, one CSV per entity and per (from, label, to) relationship. Columns are provisional; b-e may add columns and update the data dictionary.
- **Published description:** the build writes templated text by default (`--text templated`). `--text ai` swaps in the committed AI text. All criteria and golden checksums use the default until R2 is GO; if R2 picks AI text, child b switches the default and regenerates the checksums.
- First answer-key files, in the epic's schema.
- Invariants enforced here: INV-7 (golden checksums), INV-9 (names + deny-list over all text). Replaces their `TBD (E1)` in `docs/data-model.md` with the AC-3 and AC-4 test names. INV-1, 2, 4, 5 are left to b-e.
- Random streams are sub-seeded per entity type from the start (epic rule; AC-11), so b-e can extend without changing a's output.

## Test plan
- Real files, real build, no mocks; tests build into a temp directory and never write committed files.
- AC-5 blocks network with a socket guard in the subprocess only; it is a guard, not a mock of our code.
- The AI-text script (`write_text.py`) is not run by tests; it is run once by hand (key read at runtime from `~/.claude/secrets.yaml`), and its committed output is what AC-4 and AC-6 check.
- Not tested here: F1 bands, quotas, hard-negative rates, planted scenarios and full sizes (meaningless at ~15 rows; c-e own them). The owner's realism verdict is a manual gate recorded in R2's decision.md, not a test.

## Gate hand-off
When every criterion passes, `sample_pack.md` (generated by the command at its default path) is committed with the change. The owner fills its review table and records the verdict and text choice in `research/r2-synthetic-text-realism/decision.md`. Both are research, so they reach the base branch per rule 9 (`capitan rescue` if needed) before b's start is checked. The pack's header tells the reviewer that taxonomy breadth and population sizes belong to b-e; the review is about whether rows and text read as real.

## Risks
- Sample size too small to judge realism of ratios: the review asks about text and attributes, not distributions (stated in the pack header).
- Windows/Linux byte differences: AC-3 written first, with explicit `newline="\n"` and encoding in the writer.
- AI text keys drift as code changes: generate AI text last (slice 6), after the internal keys are stable.
- AI text mentioning real names: AC-4 scans the committed AI text; the generation prompt also tells the model to use only names given to it.
- Deny-list completeness: it is a floor, backed by the owner's one-time review of the name lists in the pack.
- Thin slice grows into the full generator: rules beyond what the criteria need are out of scope (below).
- Timebox: AI text is the first cut (see timebox).

## Out of scope
- Full sizes, quotas, F1 baseline bands, hard-negative rates: c and d.
- Taxonomy breadth and organization realism rules: b.
- Planted scenarios and INV-4/INV-5 date and link rules: e.
- Loading into SQLite or Neo4j, CI workflow: E3.

## Relevant lessons
- None found for: sample, pack, realism, review, generator, seed, text. New project.

## Slices
1. `akg` package with `build` (flags `--size`, `--seed`, `--out`, `--count TYPE=N`, `--text`, `--text-dir`) and `sample-pack` commands, `requirements.txt`, `.gitattributes`; AC-10.
2. Name lists and deny-list; AC-4 (name-column part).
3. Entity and edge generators at sample size with sub-seeded streams, plus the answer key; AC-1, AC-2, AC-7.
4. Writer encoding and golden checksums; AC-3, AC-5, AC-11.
5. Data dictionary README; AC-9.
6. `write_text.py`, run once, committed text with input hashes; AC-6, AC-4 (AI-text part).
7. Sample pack renderer and review table; AC-8, AC-4 (pack part). Update `docs/data-model.md`.
