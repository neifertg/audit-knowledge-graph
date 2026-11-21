# Score reconciliation against the answer key

```json plan
{
  "id": "014-score-reconciliation-against-the-answer",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-21",
  "objective": "O3",
  "areas": [
    "src/features/reconciliation/**",
    "tests/**",
    "docs/data-model.md"
  ],
  "timebox": "1 day. Past this, stop and re-plan or split.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`score(build_dir)` in `src/features/reconciliation/score.py` runs on a reconciled full build",
      "then": "it reads `<build_dir>/reconciled/` and `<build_dir>/answer_key/` and returns these figures:\n- *Cross-source risks and controls,* scored on the final canonical pairs:\n  - merged pairs, precision, recall and F1;\n  - review-queue rows of that kind and how many hold a true pair;\n  - true pairs missed (neither merged nor queued);\n  - the recall reached if a reviewer resolves the queue correctly;\n  - the raw accept-band figures before conflicts.\n- *ERM duplicates:* queued, true among the queued, missed.\n- *Taxonomy mapping:* correct per level on nodes holding risks, on all nodes, and falsely `unmapped`.\n- *Placement:* IA risks correct per method, and correct among misfiled IA risks (true node not under the IA node's true target).\n- *Review queue:* rows by kind and reason.\n- *Orphans:* the number of orphan controls.\n\nPair figures count pairs, so true non-matches, including orphans, cannot inflate them. Within `src/features/reconciliation/*.py`, only `score.py` (the published bank) and `train.py` (the training bank) mention `answer_key`; 013's static check is updated to that pair.",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac1_figures_from_a_reconciled_build (a hand-built mini build with known answers checks every count; the seed-42 figures are printed)",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the citation cue's share is measured",
      "then": "a function in `train.py` retrains the control model on the training bank with the `citation` column dropped, using the same rule, settings and thresholds. `score.py` applies that model to the scored bank and reports controls with and without the cue: accepted, precision, recall, queue and missed. Measured on seed 42: with the cue, 68 accepted at precision 1.00, a queue of 341 and 5 missed; without it, 82 accepted at precision 0.89, a queue of 505 and 1 missed. So the cue buys precision and a smaller queue rather than recall, and docs/data-model.md says so",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac2_citation_cue_share",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "`python -m src.features.reconciliation.score` runs",
      "then": "it builds seed 42 at full size (the published default) in a temporary directory, reconciles it, scores it, and writes `src/features/reconciliation/scores.json`. This is the one JSON E4's page reads. It holds:\n- every AC-1 and AC-2 figure, with ratios rounded to 4 decimals;\n- the provenance: seed 42, AI text, the training seed, and the weights fingerprint;\n- the thresholds' targets: 95% precision on the training bank for auto-accept, 99% of true pairs above the review floor;\n- the two page caveats as text:\n  - orphan controls (31 at seed 42) mitigate no risk and always score as unmatched, which is structure, not matcher skill (pair figures exclude them);\n  - the training bank comes from the same generator, so its weights know the generator's habits in a way a real bank's history would not.\n\nA test re-scores the cached seed-42 build and asserts the result equals the committed file exactly",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac3_committed_scores_are_current",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the figures are cross-checked",
      "then": "they agree with the reconciled output and with the earlier children:\n- the queue counts by kind sum to `review_queue.csv`'s rows (482 at seed 42);\n- merged counts match the maps-to files;\n- the taxonomy figures equal 011's;\n- placement equals 013's (130/150);\n- merged precision for risks and controls is at least 0.95, and recall if the queue is resolved is at least 0.95 for both (measured 0.98 and 0.98)",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac4_figures_agree_with_the_reconciled_output",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "docs/data-model.md is read after this change",
      "then": "a *Reconciliation results* section quotes each headline figure from `scores.json`, the citation-cue finding and both caveats, and the open data question about the matching method is closed (R1). A test fails if the doc stops quoting a headline figure (each as written with 2 decimals, or as a count `a/b`). The README names `score.py` and `scores.json`",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac5_docs_quote_the_published_figures",
      "status": "pending"
    }
  ],
  "epic": "002-e2-erm-ia-reconciliation",
  "child": "d"
}
```

## Why
E2 child d (O3's signal): "precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue." This child produces those numbers once, honestly framed, in one JSON the page reads. It also answers the data-model note asking how much of control accuracy comes from the citation cue.

## Data impact
- **No new data entity.** `scores.json` is a committed results artifact in the feature folder. It is not under `reconciled/`, so the INV-6 byte-identity test and the reconciled golden are unaffected.
- **INV-6:** `score.py` is the scoring step, the one place allowed to read the published bank's answer key; 013's static check is updated to allow `score.py` and `train.py`. The pipeline itself is unchanged.
- docs/data-model.md gains a results section and closes the R1 open question.

## Test plan
Tests go in `tests/reconciliation/test_scoring.py`, using the cached seed-42 build (which reconciles) and a hand-built mini build for exact counts. The ablation retrain in AC-2 builds seed 7 (under a second) and fits once (seconds). The whole suite stays the done-check.

**Evidence** (pre-plan measurement on 2026-11-21, on a fresh seed-42 build reconciled by the merged code):

| Figure | Risks | Controls |
|---|---|---|
| True pairs | 103 | 245 |
| Merged (precision / recall / F1) | 33 (1.00 / 0.32 / 0.49) | 68 (1.00 / 0.28 / 0.44) |
| Queue rows (true among them) | 127 (68) | 341 (172) |
| Missed | 2 | 5 |
| Recall if the queue is resolved | 0.98 | 0.98 |

The other figures:
- ERM duplicates: 14 queued (12 true), 1 missed.
- Taxonomy: L1 6/9, L2 14/20, L3 24/33 on nodes holding risks; 47/75 on all nodes.
- Placement: matched 33/33, mapped 89/103, nearest 8/14; misfiled IA risks 14/21.
- Orphan controls: 31.
- Citation cue: with it, 68 accepted at 1.00, a queue of 341 and 5 missed; without it, 82 at 0.89, 505 and 1.

Per L-012, the committed JSON comes from the built module.

**Not tested here:** how the page presents the figures (E4).

## Risks
- **Figures read as better than they are.** The page will show precision 1.00. The JSON therefore carries recall, the queue size and both caveats next to it, and E4 must show them together.
- **Ablation is a model comparison, not a causal share.** Retraining without the cue shifts other weights. The docs say "with and without the feature", not "the cue contributes X%".
- **scores.json drifts from the build.** AC-3's equality test catches it; regenerating takes one command.

## Out of scope
- Page design and charts (E4).
- Reviewer decisions: what the review queue would yield in practice, beyond the "resolved correctly" upper bound (parked in the epic).
- Other seeds' figures on the page: seed 1 figures stay in the child plans and the docs.

## Relevant lessons
- **L-012** (quote the built module): the figures come from the merged pipeline, and the JSON is generated, never hand-written.
- **L-008** (exact shared phrases become lookup keys): the citation cue's share is measured and published, as the data model asked.
- **L-013:** duplicates are review-only, so their figures are "queued, true, missed" with no precision.

## Slices
1. `score.py` figures, with the AC-1 mini-build test, and the updated static check.
2. The ablation in `train.py` and AC-2.
3. `scores.json`, the regeneration command and AC-3/AC-4.
4. Docs (AC-5).
