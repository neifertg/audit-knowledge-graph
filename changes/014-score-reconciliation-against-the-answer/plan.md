# Score reconciliation against the answer key

```json plan
{
  "id": "014-score-reconciliation-against-the-answer",
  "tier": "standard",
  "status": "in-progress",
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
      "then": "it reads `<build_dir>/reconciled/`, the published files and `<build_dir>/answer_key/`, and returns figures. Every ratio is stored with its count (`a/b`). The figures are defined as follows:\n- *True pair:* an (ERM, IA) item pair, over all ERM x IA pairs of that type, whose answer-key `cluster_id` is the same and not `none`.\n- *Merged pair:* an (ERM, IA) pair sharing a canonical ID in the maps-to files.\n- *Queued pair:* a `review_queue.csv` row of that kind, as (`item_a`, `item_b`), with ERM first and IA second (for duplicates, the lower ID first).\n- *Cross-source risks and controls:*\n  - merged pairs, with precision `true merged / merged`, recall `true merged / true` and F1;\n  - queued pairs and true queued;\n  - *missed*: true pairs neither merged nor queued;\n  - *recall if resolved*: `(true merged + true queued) / true`;\n  - *raw accept*: merged plus `conflict` rows, with its precision.\n- *ERM duplicates:* queued, true queued, and missed (true duplicate pairs not queued).\n- *Taxonomy mapping, per IA level:* precision `correct / mapped` (non-`unmapped` predictions); recall `correct / truly mapped nodes`; and accuracy on nodes holding risks.\n- *Placement:* IA risks correct per method (`matched`, `mapped`, `nearest`), and correct among misfiled IA risks. A risk is misfiled when its true ERM node is not under its IA node's true target, or that target is `unmapped`.\n- *Review queue:* rows by kind and reason.\n- *Orphan controls* (mitigating no risk): their count, how many are in merged canonical controls, and how many queue rows touch one.\n\nWithin `src/features/reconciliation/*.py`, only `score.py` (the published bank) and `train.py` (the training bank) mention `answer_key`. 013's static check, the README and INV-6's enforced-by entry are updated to that pair.",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac1_figures_from_a_reconciled_build (a hand-built mini build exercising every definition: a merged true pair, a merged false pair, a queued true pair, a conflict row, a missed pair, a duplicate, an unmapped and a misfiled case, an orphan; the seed-42 figures are printed)",
      "status": "pass"
    },
    {
      "id": "AC-2",
      "when": "the citation cue's share is measured",
      "then": "`train.py` also fits, with the same rule and settings, a control model without the `citation` column. It commits that model in `weights.json` as `control_without_citation`, with its thresholds chosen by training pair. 012's currency test covers the new entry too: weights within 1e-6, and the same threshold pairs. No training runs while scoring or testing. `score.py` applies both control models to the scored bank and reports, at pair-band level, accepted (precision), review band and below-floor true pairs. Measured on seed 42:\n- with the cue: 68 accepted at precision 68/68, a review band of 341, and 5 true pairs below the floor;\n- without it: 82 accepted at precision 0.89, a review band of 505, and 1 below the floor.\n\nThe docs state the finding as \"with and without the feature\": the cue buys precision and a smaller queue rather than recall. A retrained model also shifts its other weights, so this is not a causal share",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac2_citation_cue_share",
      "status": "pass"
    },
    {
      "id": "AC-3",
      "when": "`python -m src.features.reconciliation.score` runs",
      "then": "it builds seed 42 at full size (the published default) in a temporary directory, reconciles it, scores it, and writes `src/features/reconciliation/scores.json`. This is the one JSON E4's page reads. It holds:\n- every AC-1 and AC-2 figure, as counts with 4-decimal ratios;\n- the provenance: seed 42, AI text, the training seed, and the weights fingerprint;\n- the thresholds' targets: 95% precision on the training bank for auto-accept, 99% of true pairs above the review floor.\n\nIt also holds these caveats as text, for the page to show beside the figures:\n1. *Orphans:* the 31 orphan controls mitigate no risk and enter the candidate pairs as easy negatives. None is merged, and 2 queue rows touch one. This helps the figures and is not matcher skill (the epic's wording).\n2. *Same generator:* the training bank comes from the same generator, so its weights know the generator's habits in a way a real bank's history would not.\n3. *One bank, small samples:* the precision of 1.00 rests on 33 risk and 68 control merges in one bank, and on seed 1 risks reached 0.93.\n4. *Conservative thresholds:* only pairs at a training precision of 95% or more merge, so merged recall is low and the queue carries the rest. The best-threshold F1 in research R1 (about 0.81 and 0.74) is therefore not comparable with the merged F1 (0.49 and 0.44).\n\nA test re-scores the cached seed-42 build and asserts the result equals the committed file exactly. No training happens in that path, so the figures are counts from deterministic output",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac3_committed_scores_are_current",
      "status": "pass"
    },
    {
      "id": "AC-4",
      "when": "the figures are cross-checked",
      "then": "they agree with what earlier children recorded independently in docs/data-model.md:\n- taxonomy accuracy on nodes holding risks, 44/62 (011);\n- merged risks and controls, 33 and 68 (013);\n- queue rows, 482 (013);\n- IA placement, 130/150 (013).\n\nThey are also internally consistent: merged plus queued plus missed true pairs equals true pairs, and the queue counts by kind sum to the file's rows. And they clear floors: merged precision for risks and controls at least 0.95, and recall if resolved at least 0.95 for both (measured 101/103 and 240/245)",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac4_figures_agree_with_the_reconciled_output",
      "status": "pass"
    },
    {
      "id": "AC-5",
      "when": "docs/data-model.md is read after this change",
      "then": "a *Reconciliation results* section quotes each headline figure from `scores.json`, the citation-cue finding and both caveats, and the open data question about the matching method is closed (R1). A test fails if the doc stops quoting a headline figure (each as written with 2 decimals, or as a count `a/b`). The README names `score.py` and `scores.json`",
      "test": "reconciliation.test_scoring.ScoringTests.test_ac5_docs_quote_the_published_figures",
      "status": "pass"
    }
  ],
  "epic": "002-e2-erm-ia-reconciliation",
  "child": "d",
  "approved": "2026-11-21",
  "approved_hash": "174cfab48c229526",
  "in_progress": "2026-11-21"
}
```

## Why
E2 child d (O3's signal): "precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue." This child produces those numbers once, honestly framed, in one JSON the page reads. It also answers the data-model note asking how much of control accuracy comes from the citation cue.

## Data impact
- **No new data entity.** `scores.json` is a committed results artifact in the feature folder. It is not under `reconciled/`, so the INV-6 byte-identity test and the reconciled golden are unaffected.
- **INV-6:** `score.py` is the scoring step, the one place allowed to read the published bank's answer key. 013's static check, the README and INV-6's enforced-by entry are updated to allow `score.py` and `train.py`. The pipeline itself is unchanged.
- **`weights.json`** gains a `control_without_citation` entry from `train.py`. That changes the fingerprint; the other models' coefficients and thresholds are unchanged.
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
- Taxonomy (precision / recall per level): L1 6/9 / 6/8, L2 14/20 / 14/20, L3 24/31 / 24/41; 44/62 on nodes holding risks.
- Orphans: 31; 0 merged; 2 queue rows touch one.
- Placement: matched 33/33, mapped 89/103, nearest 8/14; misfiled IA risks 14/21.
- Orphan controls: 31.
- Citation cue: with it, 68 accepted at 1.00, a queue of 341 and 5 missed; without it, 82 at 0.89, 505 and 1.

Per L-012, the committed JSON comes from the built module.

**Not tested here:** how the page presents the figures (E4).

## Risks
- **Figures read as better than they are.** The page will show precision 1.00. The JSON therefore carries recall, the queue size and both caveats next to it, and E4 must show them together.
- **Ablation is a model comparison, not a causal share.** Retraining without the cue shifts other weights. The docs say "with and without the feature", not "the cue contributes X%". The ablated model is committed, so no training runs in tests, and platform drift is caught by 012's currency check rather than by an exact-equality test.
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
