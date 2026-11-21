# Canonical layer, review queue and build step

```json plan
{
  "id": "013-canonical-layer-review-queue-and-build-s",
  "tier": "standard",
  "status": "in-progress",
  "created": "2026-11-21",
  "objective": "O3",
  "areas": [
    "src/features/reconciliation/**",
    "tests/**",
    "docs/data-model.md",
    "akg/**"
  ],
  "timebox": "1 day. Past this, stop and re-plan or split.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m akg build` runs (either size), or `python -m akg reconcile --out <dir>` runs on an existing build",
      "then": "reconciliation runs after generation, unless `build --no-reconcile` is given, and writes `<out>/reconciled/`.\n\nEvery file is UTF-8 with LF line endings. Scores are written as the pair's **logit**, the model's log-odds `X.w + b`, with 6 decimals. Bands and merge order use the unrounded value; the logit is what gets written because probabilities above 0.9999 lose precision. Each file and its row order:\n- `canonical_risk.csv`: `canonical_risk_id`, `erm_l3_node_id`, `placement` (`erm`, `matched`, `mapped` or `nearest`); sorted by ID.\n- `canonical_control.csv`: `canonical_control_id`; sorted by ID.\n- `risk_maps_to_canonical.csv`: `source`, `risk_id`, `canonical_risk_id`, `logit`; sorted by (`source`, `risk_id`). `logit` is the merged edge's value and is empty for an unmerged risk.\n- `control_maps_to_canonical.csv`: the same columns for controls, sorted the same way. An IA control's row carries its merged edge's logit, and an ERM control's row the highest logit among its merged edges.\n- `ia_maps_to_erm.csv`: `ia_node_id`, `erm_node_id`, `score`, `basis` (child a's rows, with score to 6 decimals); sorted by `ia_node_id`.\n- `review_queue.csv`: `kind`, `item_a`, `item_b`, `logit`, `reason`, `drivers`.\n  - `kind` is `risk`, `duplicate` or `control`. `item_a` is the ERM item, or the lower ID for a duplicate; `item_b` is the IA item, or the higher ERM ID.\n  - `reason` is `review_band` or `conflict`.\n  - `drivers` holds the names of the 3 features with the largest signed contribution (coefficient x value), largest first, ties in column order, joined by `;`.\n  - Rows are sorted by kind (risk, duplicate, control), then `logit` descending, then `item_a`, then `item_b`.\n\nCanonical IDs are `CR-0001...` and `CC-0001...`, numbered in plain string order of each item's lowest member ID.",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac1_build_writes_the_reconciled_files",
      "status": "pass"
    },
    {
      "id": "AC-2",
      "when": "the canonical assignment runs on the pair scores (child b's `pair_scores`)",
      "then": "merged edges are the cross-source pairs in the `accept` band, taken in the order (logit descending, ERM ID, IA ID):\n- *Risks:* an edge merges only if neither of its risks already has a merged edge, so a canonical risk holds at most one ERM and one IA risk. This is the mirror rule the epic critique asked for; ERM duplicates are review-only, so they never chain.\n- *Controls:* an edge merges only if its IA control has no merged edge yet, so each IA control joins its best accepted ERM control, and a canonical control holds at most one ERM control.\n- A losing accepted edge goes to the queue with reason `conflict`.\n- Pairs in the `review` band, and every duplicate pair at or above its floor, go to the queue with reason `review_band`.\n- Every other item is a singleton canonical item.\n\n*Placement:*\n- An ERM-only or matched canonical risk takes the ERM risk's node (`erm`, `matched`).\n- An IA-only risk whose IA node maps (child a) to an ERM L3 node takes that node (`mapped`).\n- Otherwise it takes the node of its most similar ERM risk (similarity.py), searched within the mapped target's subtree. If the node is unmapped, or that subtree holds no ERM risk, the search covers all ERM risks. Ties go to the lowest ERM risk ID (`nearest`).",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac2_assignment_and_placement_rules (hand-built scored pairs: a two-ERM conflict, a two-IA conflict, an IA control with two accepted edges, a review-band pair, a duplicate pair; placement on a small fixture)",
      "status": "pass"
    },
    {
      "id": "AC-3",
      "when": "the reconciled output of the seed-42 full build is checked as a whole (INV-3)",
      "then": "the structural rules hold exactly:\n- every source risk and control maps to exactly one canonical item;\n- every merged edge is in the accept band;\n- no canonical risk holds two ERM risks or two IA risks;\n- no canonical control holds two ERM controls.\n\nThe figures are floors: merged precision at least 0.95 for risks and controls, and IA placement at least 0.80. The test prints every count: merged, precision, recall, demoted for conflict, queue by kind and reason, and placement by kind. Before freezing, the counts are re-measured with the built module and recorded in docs/data-model.md (L-012). The pre-plan figures were: risks 33 merged (1.00), 5 demoted; controls 68 (1.00); placement 130/150. Child d publishes the final figures.",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac3_inv3_whole_output",
      "status": "pass"
    },
    {
      "id": "AC-4",
      "when": "`akg reconcile` runs on a copy of a full build with `answer_key/` deleted",
      "then": "a copy of the seed-42 full build with both `answer_key/` and `reconciled/` deleted is reconciled with `akg reconcile`. The test asserts all six files are recreated and byte-identical to those reconciled from the full build. Within `src/features/reconciliation/*.py`, only `train.py` mentions `answer_key`.\n\nINV-6 in docs/data-model.md reads: \"The reconciliation pipeline never reads the published bank's answer key; only the scoring step does. The training script alone may read the training bank's (seed 7) answer key, to learn the committed weights.\"\n\nINV-3 reads: \"Each source risk or control maps to exactly one canonical item (a singleton when unmatched). An ERM-IA pair merges only at or above its kind's auto-accept threshold; uncertain pairs go to the review queue, so nothing below the confidence threshold merges silently.\"\n\nThe invariants table names this test for INV-6 and AC-3's test for INV-3.",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac4_inv6_reconciled_output_ignores_the_answer_key",
      "status": "pass"
    },
    {
      "id": "AC-5",
      "when": "the goldens are checked",
      "then": "the generator goldens (`checksums.sha256`, `checksums_full.sha256`) are unchanged. `checksums()` in `tests/generator/golden.py` skips the `reconciled/` folder itself, so every caller (test_determinism, test_issues, the drift checks) compares generator files only. The generator test helper `build()` passes `--no-reconcile` for speed; tests that call `run_akg` directly still reconcile, and that is fine. A new `tests/golden/checksums_reconciled.sha256` holds the seed-42 full build's `reconciled/` files. It is regenerated with `.venv\\Scripts\\python -m tests.reconciliation.golden`, and a test regenerates and compares it (INV-7 for E2 output). Two runs are byte-identical.",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac5_reconciled_output_matches_its_golden; generator.test_determinism (unchanged goldens)",
      "status": "pass"
    },
    {
      "id": "AC-6",
      "when": "docs/data-model.md and the feature README are read after this change",
      "then": "they describe the reconciled files and their columns, the assignment rule, placement, the review queue's reasons and drivers, INV-3 (enforced by AC-3's test) and INV-6's new wording (enforced by AC-4's test), with the measured counts from the built module (L-012). The invariants table names the tests for INV-3 and INV-6",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac6_docs_describe_the_canonical_layer",
      "status": "pass"
    }
  ],
  "epic": "002-e2-erm-ia-reconciliation",
  "child": "c",
  "approved": "2026-11-21",
  "approved_hash": "cf8f228b823682ff",
  "in_progress": "2026-11-21"
}
```

## Why
E2 child c (O3). Child b scores every pair; this child turns scores into the canonical layer E3 loads: one canonical risk or control per real-world item, ERM L3 placement for every risk, and a review queue for everything uncertain, so nothing below the confidence threshold merges silently (INV-3). It also adds reconciliation to `python -m akg build`.

## Data impact
- **New E2 output** in `<out>/reconciled/` (the epic's output contract):
  - `CANONICAL_RISK` and `CANONICAL_CONTROL`, with `RISK maps_to CANONICAL_RISK` and `CONTROL maps_to CANONICAL_CONTROL`;
  - `TAXONOMY_NODE ia_maps_to_erm`, written from child a;
  - the review queue.
- **INV-3 becomes enforced** (AC-3). **INV-6 is reworded and enforced** (AC-4). **INV-7 is extended** to the reconciled output (AC-5).
- **INV-10:** ERM-IA links appear only in the canonical layer, as the invariant allows.
- **Generator outputs and goldens are unchanged.** Generator tests build with `--no-reconcile`, so their drift checks compare generator files only.
- `akg build` gains a reconciliation step (`akg/**`) and `akg reconcile` is a new command.

## Test plan
Tests go in `tests/reconciliation/test_canonical.py`, using the cached full build from 011 (which now also reconciles) and `akg reconcile` on copies. The offline test (`generator.test_offline`) now covers reconciliation too, since default builds reconcile under the network block. The whole suite stays the done-check.

**Evidence** (pre-plan measurement on 2026-11-21, importing the merged `pair_scores`, `map_taxonomy` and `risk_similarity`):

| Seed | Risks merged (precision) | Demoted for conflict | Controls merged (precision) | Canonical risks / controls | IA placement |
|---|---|---|---|---|---|
| 42 (AI text) | 33 (1.00) | 5, 3 of them true | 68 (1.00) | 297 / 626 | 130/150 |
| 1 (templated) | 40 (0.95) | 2 | 95 (0.98) | 290 / 588 | 128/150 |
| Sample size | 0 | 0 | 0 | 30 / 30 | 13/15 |

The 3 true demoted edges are IA risks that truly match both an ERM risk and its duplicate. Only one edge can merge while duplicates are review-only, and the other waits in the queue, as intended.

**Speed.** Reconciliation takes about 7 s at full size and under 1 s at sample size. The generator helper skips it. Tests that call `run_akg` directly (test_determinism, test_issues, test_offline) reconcile, which adds an estimated 30-40 s to the suite.

**Not tested here:** scoring against the answer key for the page (child d).

## Risks
- **Cross-platform bytes:** logits are floating point, and the reconciled golden must match on Windows and Linux. A logit is written with 6 decimals, and a last-digit difference on another platform would change the bytes; a pair within float noise of a threshold could band differently. Signal: the CI run in E3. If it differs, the golden records bands rather than score digits.
- **Test-suite time:** every non-generator full build now reconciles (about 7 s each). Signal: suite time; the helpers cache builds.
- **Review queue size** (about 480 rows at seed 42): this is E2's honest output; d and E4 present it.

## Out of scope
- Precision and recall export, the citation-cue share, and the page caveats: child d.
- Reviewer decisions and a queue UI: parked in the epic.
- Loading the canonical layer into SQLite and Neo4j: E3.

## Relevant lessons
- **L-012** (quote the built module): the figures come from the merged modules.
- **L-006** (frozen goldens): the generator goldens are untouched (`golden.py` skips `reconciled/`, `--no-reconcile` in generator helpers), and E2 gets its own golden.
- **L-013** (transfer, review-only kinds): duplicates stay review-only here.

## Slices
1. `canonical.py`: assignment, placement and queue, with the AC-2 fixture test.
2. `reconcile.py` writer, the `akg build` step, `akg reconcile` and `--no-reconcile`; `golden.py` skips `reconciled/`.
3. The AC-1, AC-3, AC-4 and AC-5 tests, and the reconciled golden.
4. Docs and invariants (AC-6).
