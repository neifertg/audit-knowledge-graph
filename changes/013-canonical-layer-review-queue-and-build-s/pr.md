# Canonical layer, review queue and build step

Change `013-canonical-layer-review-queue-and-build-s` · objective **O3**: It shows, and measures, the realistic hard part: reconciling ERM's and IA's separate risk taxonomies, risks and controls into one framework (ERM's Basel-style taxonomy). Signal: precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue rather than being merged silently.

## Why
E2 child c (O3). Child b scores every pair; this child turns scores into the canonical layer E3 loads: one canonical risk or control per real-world item, ERM L3 placement for every risk, and a review queue for everything uncertain, so nothing below the confidence threshold merges silently (INV-3). It also adds reconciliation to `python -m akg build`.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `python -m akg build` runs (either size), or `python -m akg reconcile --out <dir>` runs on an existing build | reconciliation runs after generation, unless `build --no-reconcile` is given, and writes `<out>/reconciled/`.

Every file is UTF-8 with LF line endings. Scores are written as the pair's **logit**, the model's log-odds `X.w + b`, with 6 decimals. Bands and merge order use the unrounded value; the logit is what gets written because probabilities above 0.9999 lose precision. Each file and its row order:
- `canonical_risk.csv`: `canonical_risk_id`, `erm_l3_node_id`, `placement` (`erm`, `matched`, `mapped` or `nearest`); sorted by ID.
- `canonical_control.csv`: `canonical_control_id`; sorted by ID.
- `risk_maps_to_canonical.csv`: `source`, `risk_id`, `canonical_risk_id`, `logit`; sorted by (`source`, `risk_id`). `logit` is the merged edge's value and is empty for an unmerged risk.
- `control_maps_to_canonical.csv`: the same columns for controls, sorted the same way. An IA control's row carries its merged edge's logit, and an ERM control's row the highest logit among its merged edges.
- `ia_maps_to_erm.csv`: `ia_node_id`, `erm_node_id`, `score`, `basis` (child a's rows, with score to 6 decimals); sorted by `ia_node_id`.
- `review_queue.csv`: `kind`, `item_a`, `item_b`, `logit`, `reason`, `drivers`.
  - `kind` is `risk`, `duplicate` or `control`. `item_a` is the ERM item, or the lower ID for a duplicate; `item_b` is the IA item, or the higher ERM ID.
  - `reason` is `review_band` or `conflict`.
  - `drivers` holds the names of the 3 features with the largest signed contribution (coefficient x value), largest first, ties in column order, joined by `;`.
  - Rows are sorted by kind (risk, duplicate, control), then `logit` descending, then `item_a`, then `item_b`.

Canonical IDs are `CR-0001...` and `CC-0001...`, numbered in plain string order of each item's lowest member ID. | `reconciliation.test_canonical.CanonicalTests.test_ac1_build_writes_the_reconciled_files` | pass | PASS |
| AC-2 | the canonical assignment runs on the pair scores (child b's `pair_scores`) | merged edges are the cross-source pairs in the `accept` band, taken in the order (logit descending, ERM ID, IA ID):
- *Risks:* an edge merges only if neither of its risks already has a merged edge, so a canonical risk holds at most one ERM and one IA risk. This is the mirror rule the epic critique asked for; ERM duplicates are review-only, so they never chain.
- *Controls:* an edge merges only if its IA control has no merged edge yet, so each IA control joins its best accepted ERM control, and a canonical control holds at most one ERM control.
- A losing accepted edge goes to the queue with reason `conflict`.
- Pairs in the `review` band, and every duplicate pair at or above its floor, go to the queue with reason `review_band`.
- Every other item is a singleton canonical item.

*Placement:*
- An ERM-only or matched canonical risk takes the ERM risk's node (`erm`, `matched`).
- An IA-only risk whose IA node maps (child a) to an ERM L3 node takes that node (`mapped`).
- Otherwise it takes the node of its most similar ERM risk (similarity.py), searched within the mapped target's subtree. If the node is unmapped, or that subtree holds no ERM risk, the search covers all ERM risks. Ties go to the lowest ERM risk ID (`nearest`). | `reconciliation.test_canonical.CanonicalTests.test_ac2_assignment_and_placement_rules (hand-built scored pairs: a two-ERM conflict, a two-IA conflict, an IA control with two accepted edges, a review-band pair, a duplicate pair; placement on a small fixture)` | pass | PASS |
| AC-3 | the reconciled output of the seed-42 full build is checked as a whole (INV-3) | the structural rules hold exactly:
- every source risk and control maps to exactly one canonical item;
- every merged edge is in the accept band;
- no canonical risk holds two ERM risks or two IA risks;
- no canonical control holds two ERM controls.

The figures are floors: merged precision at least 0.95 for risks and controls, and IA placement at least 0.80. The test prints every count: merged, precision, recall, demoted for conflict, queue by kind and reason, and placement by kind. Before freezing, the counts are re-measured with the built module and recorded in docs/data-model.md (L-012). The pre-plan figures were: risks 33 merged (1.00), 5 demoted; controls 68 (1.00); placement 130/150. Child d publishes the final figures. | `reconciliation.test_canonical.CanonicalTests.test_ac3_inv3_whole_output` | pass | PASS |
| AC-4 | `akg reconcile` runs on a copy of a full build with `answer_key/` deleted | a copy of the seed-42 full build with both `answer_key/` and `reconciled/` deleted is reconciled with `akg reconcile`. The test asserts all six files are recreated and byte-identical to those reconciled from the full build. Within `src/features/reconciliation/*.py`, only `train.py` mentions `answer_key`.

INV-6 in docs/data-model.md reads: "The reconciliation pipeline never reads the published bank's answer key; only the scoring step does. The training script alone may read the training bank's (seed 7) answer key, to learn the committed weights."

INV-3 reads: "Each source risk or control maps to exactly one canonical item (a singleton when unmatched). An ERM-IA pair merges only at or above its kind's auto-accept threshold; uncertain pairs go to the review queue, so nothing below the confidence threshold merges silently."

The invariants table names this test for INV-6 and AC-3's test for INV-3. | `reconciliation.test_canonical.CanonicalTests.test_ac4_inv6_reconciled_output_ignores_the_answer_key` | pass | PASS |
| AC-5 | the goldens are checked | the generator goldens (`checksums.sha256`, `checksums_full.sha256`) are unchanged. `checksums()` in `tests/generator/golden.py` skips the `reconciled/` folder itself, so every caller (test_determinism, test_issues, the drift checks) compares generator files only. The generator test helper `build()` passes `--no-reconcile` for speed; tests that call `run_akg` directly still reconcile, and that is fine. A new `tests/golden/checksums_reconciled.sha256` holds the seed-42 full build's `reconciled/` files. It is regenerated with `.venv\Scripts\python -m tests.reconciliation.golden`, and a test regenerates and compares it (INV-7 for E2 output). Two runs are byte-identical. | `reconciliation.test_canonical.CanonicalTests.test_ac5_reconciled_output_matches_its_golden; generator.test_determinism (unchanged goldens)` | pass | PASS |
| AC-6 | docs/data-model.md and the feature README are read after this change | they describe the reconciled files and their columns, the assignment rule, placement, the review queue's reasons and drivers, INV-3 (enforced by AC-3's test) and INV-6's new wording (enforced by AC-4's test), with the measured counts from the built module (L-012). The invariants table names the tests for INV-3 and INV-6 | `reconciliation.test_canonical.CanonicalTests.test_ac6_docs_describe_the_canonical_layer` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/reconciliation/****: `src/features/reconciliation/canonical.py`, `src/features/reconciliation/match.py`, `src/features/reconciliation/weights.json`
3. **akg/****: `akg/__main__.py`
4. **Tests**: `tests/generator/golden.py`, `tests/generator/helpers.py`, `tests/golden/checksums_reconciled.sha256`, `tests/reconciliation/golden.py`, `tests/reconciliation/test_canonical.py`

## Data impact
- **New E2 output** in `<out>/reconciled/` (the epic's output contract):
  - `CANONICAL_RISK` and `CANONICAL_CONTROL`, with `RISK maps_to CANONICAL_RISK` and `CONTROL maps_to CANONICAL_CONTROL`;
  - `TAXONOMY_NODE ia_maps_to_erm`, written from child a;
  - the review queue.
- **INV-3 becomes enforced** (AC-3). **INV-6 is reworded and enforced** (AC-4). **INV-7 is extended** to the reconciled output (AC-5).
- **INV-10:** ERM-IA links appear only in the canonical layer, as the invariant allows.
- **Generator outputs and goldens are unchanged.** Generator tests build with `--no-reconcile`, so their drift checks compare generator files only.
- `akg build` gains a reconciliation step (`akg/**`) and `akg reconcile` is a new command.

## Risks
- **Cross-platform bytes:** logits are floating point, and the reconciled golden must match on Windows and Linux. A logit is written with 6 decimals, and a last-digit difference on another platform would change the bytes; a pair within float noise of a threshold could band differently. Signal: the CI run in E3. If it differs, the golden records bands rather than score digits.
- **Test-suite time:** every non-generator full build now reconciles (about 7 s each). Signal: suite time; the helpers cache builds.
- **Review queue size** (about 480 rows at seed 42): this is E2's honest output; d and E4 present it.

## Deliberately not in this PR
- Precision and recall export, the citation-cue share, and the page caveats: child d.
- Reviewer decisions and a queue UI: parked in the epic.
- Loading the canonical layer into SQLite and Neo4j: E3.

Parked for later:
- 2026-11-21 013 review minors: write_reconciled crashes on a file with no rows (take header from FILES, not rows[0]); test the review queue on the hand-built example and the placement fallback to all ERM risks; AC-3 control check should assert exactly once and canonical IDs match canonical_control.csv; compute map_taxonomy and risk_similarity once per reconcile (speed); suite now ~3 min (from 013-canonical-layer-review-queue-and-build-s)

## Lessons recorded
- L-014 Estimate test-suite cost by counting the builds each new step adds

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `d66a62fd94ed3c4f`
- Size: 9 code files, +429 / -9 lines
