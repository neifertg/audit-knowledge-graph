# Canonical layer, review queue and build step

```json plan
{
  "id": "013-canonical-layer-review-queue-and-build-s",
  "tier": "standard",
  "status": "draft",
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
      "then": "reconciliation runs after generation, unless `build --no-reconcile` is given, and writes `<out>/reconciled/` with these files:\n- `canonical_risk.csv`: `canonical_risk_id`, `erm_l3_node_id`, `placement`, where `placement` is `erm`, `matched`, `mapped` or `nearest`;\n- `canonical_control.csv`: `canonical_control_id`;\n- `risk_maps_to_canonical.csv`: `source`, `risk_id`, `canonical_risk_id`, `score`;\n- `control_maps_to_canonical.csv`: `source`, `control_id`, `canonical_control_id`, `score`;\n- `ia_maps_to_erm.csv`: `ia_node_id`, `erm_node_id`, `score`, `basis`;\n- `review_queue.csv`: `kind`, `item_a`, `item_b`, `score`, `reason`, `drivers`.\n\nFormats:\n- Files are UTF-8 with LF line endings, rows sorted by their first column, and scores written with 6 decimals.\n- `score` in the maps-to files is the merged edge's score, and empty for an unmerged item.\n- Canonical IDs are `CR-0001...` and `CC-0001...`, numbered in order of each item's lowest member ID.\n- `reason` is `review_band` or `conflict`.\n- `drivers` holds the 3 features with the largest coefficient x value for that pair, joined by `;`.",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac1_build_writes_the_reconciled_files",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the canonical assignment runs on the pair scores (child b's `pair_scores`)",
      "then": "merged edges are the cross-source pairs in the `accept` band, taken in order of score (highest first, then pair IDs):\n- *Risks:* an edge merges only if neither its ERM nor its IA risk already has a merged edge, so a canonical risk holds at most one ERM and one IA risk. This is the mirror rule the epic critique asked for. Because ERM duplicates are review-only, duplicates never chain.\n- *Controls:* an edge merges only if its IA control has no merged edge yet, so each IA control joins its best accepted ERM control, and a canonical control holds at most one ERM control.\n- A losing accepted edge goes to the queue with reason `conflict`.\n- Pairs in the `review` band, and every duplicate pair at or above its floor, go to the queue with reason `review_band`.\n- Every other item is a singleton canonical item.\n\n*Placement* gives each canonical risk an ERM L3 node:\n- an ERM risk's own node, for ERM-only and matched items (`erm`, `matched`);\n- for an IA-only risk, its IA node's mapped target from child a when that target is ERM L3 (`mapped`);\n- otherwise, the node of the IA risk's most similar ERM risk (similarity.py), searched within the target's subtree, or among all ERM risks if the node is unmapped (`nearest`).",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac2_assignment_and_placement_rules (hand-built scored pairs: a two-ERM conflict, a two-IA conflict, an IA control with two accepted edges, a review-band pair, a duplicate pair; placement on a small fixture)",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the reconciled output of the seed-42 full build is checked as a whole (INV-3)",
      "then": "every source risk and control maps to exactly one canonical item. Every merged edge is in the accept band (score at or above its kind's auto-accept threshold). No canonical risk holds two ERM risks or two IA risks, and no canonical control holds two ERM controls. Measured on seed 42, with the bars at the measured value and an exact test:\n\n| Kind | Merged | Precision | Recall | Demoted for conflict | Review band |\n|---|---|---|---|---|---|\n| Risks | 33 | 1.00 | 0.32 | 5 | 122 |\n| Controls | 68 | 1.00 | 0.28 | 0 | 341 |\n| Duplicates | none | | | | 14 |\n\nMerged precision must be at least 0.95 for risks and controls (measured 1.00), and IA placement at least 0.80 (measured 130/150 = 0.87). The test prints all counts. Child d publishes the figures",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac3_inv3_whole_output",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "`akg reconcile` runs on a copy of a full build with `answer_key/` deleted",
      "then": "the `reconciled/` files are byte-identical to those reconciled from the full build. Within `src/features/reconciliation/`, only `train.py` mentions `answer_key`. docs/data-model.md's INV-6 reads: \"The reconciliation pipeline never reads the published bank's answer key; only the scoring step does. The training script alone may read the training bank's (seed 7) answer key, to learn the committed weights.\" The test is named in the invariants table",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac4_inv6_reconciled_output_ignores_the_answer_key",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the goldens are checked",
      "then": "the generator goldens (`checksums.sha256`, `checksums_full.sha256`) are unchanged, because `tests/generator/golden.py` skips `reconciled/` and the generator test helper builds with `--no-reconcile`. A new `tests/golden/checksums_reconciled.sha256` holds the seed-42 full build's `reconciled/` files, and a test regenerates and compares them (INV-7 for E2 output). Two runs are byte-identical",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac5_reconciled_output_matches_its_golden; generator.test_determinism (unchanged goldens)",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "docs/data-model.md and the feature README are read after this change",
      "then": "they describe the reconciled files and their columns, the assignment rule, placement, the review queue's reasons and drivers, INV-3 (enforced by AC-3's test) and INV-6's new wording (enforced by AC-4's test), with the measured counts from the built module (L-012). The invariants table names the tests for INV-3 and INV-6",
      "test": "reconciliation.test_canonical.CanonicalTests.test_ac6_docs_describe_the_canonical_layer",
      "status": "pending"
    }
  ],
  "epic": "002-e2-erm-ia-reconciliation",
  "child": "c"
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

**Speed.** Reconciliation takes about 7 s at full size and under 1 s at sample size. Generator tests skip it.

**Not tested here:** scoring against the answer key for the page (child d).

## Risks
- **Cross-platform bytes:** scores are floating point, and the reconciled golden must match on Windows and Linux. Scores are written with 6 decimals; a pair sitting within 1e-6 of a threshold could still band differently. Signal: the CI run in E3. If it differs, the golden records bands rather than score digits.
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
