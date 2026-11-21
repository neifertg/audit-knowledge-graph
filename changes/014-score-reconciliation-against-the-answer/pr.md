# Score reconciliation against the answer key

Change `014-score-reconciliation-against-the-answer` · objective **O3**: It shows, and measures, the realistic hard part: reconciling ERM's and IA's separate risk taxonomies, risks and controls into one framework (ERM's Basel-style taxonomy). Signal: precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue rather than being merged silently.

## Why
E2 child d (O3's signal): "precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue." This child produces those numbers once, honestly framed, in one JSON the page reads. It also answers the data-model note asking how much of control accuracy comes from the citation cue.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `score(build_dir)` in `src/features/reconciliation/score.py` runs on a reconciled full build | it reads `<build_dir>/reconciled/`, the published files and `<build_dir>/answer_key/`, and returns figures. Every ratio is stored with its count (`a/b`). The figures are defined as follows:
- *True pair:* an (ERM, IA) item pair, over all ERM x IA pairs of that type, whose answer-key `cluster_id` is the same and not `none`.
- *Merged pair:* an (ERM, IA) pair sharing a canonical ID in the maps-to files.
- *Queued pair:* a `review_queue.csv` row of that kind, as (`item_a`, `item_b`), with ERM first and IA second (for duplicates, the lower ID first).
- *Cross-source risks and controls:*
  - merged pairs, with precision `true merged / merged`, recall `true merged / true` and F1;
  - queued pairs and true queued;
  - *missed*: true pairs neither merged nor queued;
  - *recall if resolved*: `(true merged + true queued) / true`;
  - *raw accept*: merged plus `conflict` rows, with its precision.
- *ERM duplicates:* queued, true queued, and missed (true duplicate pairs not queued).
- *Taxonomy mapping, per IA level:* precision `correct / mapped` (non-`unmapped` predictions); recall `correct / truly mapped nodes`; and accuracy on nodes holding risks.
- *Placement:* IA risks correct per method (`matched`, `mapped`, `nearest`), and correct among misfiled IA risks. A risk is misfiled when its true ERM node is not under its IA node's true target, or that target is `unmapped`.
- *Review queue:* rows by kind and reason.
- *Orphan controls* (mitigating no risk): their count, how many are in merged canonical controls, and how many queue rows touch one.

Within `src/features/reconciliation/*.py`, only `score.py` (the published bank) and `train.py` (the training bank) mention `answer_key`. 013's static check, the README and INV-6's enforced-by entry are updated to that pair. | `reconciliation.test_scoring.ScoringTests.test_ac1_figures_from_a_reconciled_build (a hand-built mini build exercising every definition: a merged true pair, a merged false pair, a queued true pair, a conflict row, a missed pair, a duplicate, an unmapped and a misfiled case, an orphan; the seed-42 figures are printed)` | pass | PASS |
| AC-2 | the citation cue's share is measured | `train.py` also fits, with the same rule and settings, a control model without the `citation` column. It commits that model in `weights.json` as `control_without_citation`, with its thresholds chosen by training pair. 012's currency test covers the new entry too: weights within 1e-6, and the same threshold pairs. No training runs while scoring or testing. `score.py` applies both control models to the scored bank and reports, at pair-band level, accepted (precision), review band and below-floor true pairs. Measured on seed 42:
- with the cue: 68 accepted at precision 68/68, a review band of 341, and 5 true pairs below the floor;
- without it: 82 accepted at precision 0.89, a review band of 505, and 1 below the floor.

The docs state the finding as "with and without the feature": the cue buys precision and a smaller queue rather than recall. A retrained model also shifts its other weights, so this is not a causal share | `reconciliation.test_scoring.ScoringTests.test_ac2_citation_cue_share` | pass | PASS |
| AC-3 | `python -m src.features.reconciliation.score` runs | it builds seed 42 at full size (the published default) in a temporary directory, reconciles it, scores it, and writes `src/features/reconciliation/scores.json`. This is the one JSON E4's page reads. It holds:
- every AC-1 and AC-2 figure, as counts with 4-decimal ratios;
- the provenance: seed 42, AI text, the training seed, and the weights fingerprint;
- the thresholds' targets: 95% precision on the training bank for auto-accept, 99% of true pairs above the review floor.

It also holds these caveats as text, for the page to show beside the figures:
1. *Orphans:* the 31 orphan controls mitigate no risk and enter the candidate pairs as easy negatives. None is merged, and 2 queue rows touch one. This helps the figures and is not matcher skill (the epic's wording).
2. *Same generator:* the training bank comes from the same generator, so its weights know the generator's habits in a way a real bank's history would not.
3. *One bank, small samples:* the precision of 1.00 rests on 33 risk and 68 control merges in one bank, and on seed 1 risks reached 0.93.
4. *Conservative thresholds:* only pairs at a training precision of 95% or more merge, so merged recall is low and the queue carries the rest. The best-threshold F1 in research R1 (about 0.81 and 0.74) is therefore not comparable with the merged F1 (0.49 and 0.44).

A test re-scores the cached seed-42 build and asserts the result equals the committed file exactly. No training happens in that path, so the figures are counts from deterministic output | `reconciliation.test_scoring.ScoringTests.test_ac3_committed_scores_are_current` | pass | PASS |
| AC-4 | the figures are cross-checked | they agree with what earlier children recorded independently in docs/data-model.md:
- taxonomy accuracy on nodes holding risks, 44/62 (011);
- merged risks and controls, 33 and 68 (013);
- queue rows, 482 (013);
- IA placement, 130/150 (013).

They are also internally consistent: merged plus queued plus missed true pairs equals true pairs, and the queue counts by kind sum to the file's rows. And they clear floors: merged precision for risks and controls at least 0.95, and recall if resolved at least 0.95 for both (measured 101/103 and 240/245) | `reconciliation.test_scoring.ScoringTests.test_ac4_figures_agree_with_the_reconciled_output` | pass | PASS |
| AC-5 | docs/data-model.md is read after this change | a *Reconciliation results* section quotes each headline figure from `scores.json`, the citation-cue finding and both caveats, and the open data question about the matching method is closed (R1). A test fails if the doc stops quoting a headline figure (each as written with 2 decimals, or as a count `a/b`). The README names `score.py` and `scores.json` | `reconciliation.test_scoring.ScoringTests.test_ac5_docs_quote_the_published_figures` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/reconciliation/****: `src/features/reconciliation/score.py`, `src/features/reconciliation/scores.json`, `src/features/reconciliation/train.py`, `src/features/reconciliation/weights.json`
3. **Tests**: `tests/reconciliation/test_canonical.py`, `tests/reconciliation/test_matching.py`, `tests/reconciliation/test_scoring.py`

## Data impact
- **No new data entity.** `scores.json` is a committed results artifact in the feature folder. It is not under `reconciled/`, so the INV-6 byte-identity test and the reconciled golden are unaffected.
- **INV-6:** `score.py` is the scoring step, the one place allowed to read the published bank's answer key. 013's static check, the README and INV-6's enforced-by entry are updated to allow `score.py` and `train.py`. The pipeline itself is unchanged.
- **`weights.json`** gains a `control_without_citation` entry from `train.py`. That changes the fingerprint; the other models' coefficients and thresholds are unchanged.
- docs/data-model.md gains a results section and closes the R1 open question.

## Risks
- **Figures read as better than they are.** The page will show precision 1.00. The JSON therefore carries recall, the queue size and both caveats next to it, and E4 must show them together.
- **Ablation is a model comparison, not a causal share.** Retraining without the cue shifts other weights. The docs say "with and without the feature", not "the cue contributes X%". The ablated model is committed, so no training runs in tests, and platform drift is caught by 012's currency check rather than by an exact-equality test.
- **scores.json drifts from the build.** AC-3's equality test catches it; regenerating takes one command.

## Deliberately not in this PR
- Page design and charts (E4).
- Reviewer decisions: what the review queue would yield in practice, beyond the "resolved correctly" upper bound (parked in the epic).
- Other seeds' figures on the page: seed 1 figures stay in the child plans and the docs.

Parked for later:
- 2026-11-21 014 review minors: docs/data-model.md INV-6 enforced-by cell should name the score.py/train.py check, and line ~207 still says only train.py reads an answer key; AC-1 test uses pre-built sets, so score() CSV reading, misfiled and orphan figures lack an independent on-disk check; score.py recall divides by zero when a kind has no true pairs; score main() swallows build stderr on failure (from 014-score-reconciliation-against-the-answer)

## Lessons recorded
- L-015 Check published caveats against the code that builds the candidates

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `9726d744614d700b`
- Size: 7 code files, +521 / -5 lines
