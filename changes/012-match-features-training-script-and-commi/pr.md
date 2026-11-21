# Match features, training script and committed weights

Change `012-match-features-training-script-and-commi` · objective **O3**: It shows, and measures, the realistic hard part: reconciling ERM's and IA's separate risk taxonomies, risks and controls into one framework (ERM's Basel-style taxonomy). Signal: precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue rather than being merged silently.

## Why
E2 child b (O3). Child c needs a score and a band for every candidate pair before it can build canonical items and the review queue. Research R1 showed text plus structure reaches defensible accuracy with no embeddings. The owner chose (R1) to learn the weights once on a separate training bank, so the published bank's answer key is never read.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `pair_features(build_dir)` in `src/features/reconciliation/features.py` runs on a full build | it returns three feature tables, one per pair kind, each with sorted pair IDs and named columns, computed from published files only. Texts are `title + '. ' + description` for risks and controls alike. TF-IDF is similarity.py's two vectorizers, both fitted on the ERM and IA texts of that item type together.

- *Cross-source risks* (every ERM x IA pair; 27,000 at seed 42), 7 columns:
  - `word`, `char`: cosines, each turned into a tail score.
  - `rank`: 1/position of the ERM risk among the IA risk's ERM candidates, by raw `word + char` cosine, in a stable order.
  - `shared_entity`: the two risks share an exposed entity.
  - `shared_unit_only`: they share a business unit of their exposed entities but no exposed entity.
  - `taxonomy`: the IA risk's nearest ancestor-or-self that child a maps (not `unmapped`) maps to the ERM risk's node or one of its ancestors.
  - `same_rating`.
- *Within-ERM risk duplicates* (every unordered ERM pair; 16,110), 5 columns:
  - `word`, `char`: tail scores over these 16,110 pairs.
  - `rank`: the larger of the two directions' 1/position, ignoring self-pairs.
  - `same_node`, `same_rating`.

  Shared entity and taxonomy are left out: ERM exposure is business-unit wide, so nearly every same-unit pair shares an entity, and both risks sit in one tree.
- *Cross-source controls* (every ERM x IA pair; 118,105), 9 columns:
  - `word`, `char` and `rank`, as for risks, with the IA control as the row.
  - `risk_link`: the highest cross-source risk score from the risk model over the pairs of risks the two controls mitigate, 0 if none.
  - `same_type`, `same_nature`, `same_frequency`.
  - `shared_system`.
  - `citation`: 1 when the ERM title's text before its first ':' (trimmed and lower-cased) occurs in the lower-cased IA description; 0 for a title with no ':'.

A *tail score* is computed with numpy only (no scipy) from the value's percentile `p` within its own table (average rank of ties, scaled 0-1) as `-log10(1 - p + 1/n)`. That makes it scale-free across text styles without labels, and spreads out the top candidates. | `reconciliation.test_matching.MatchingTests.test_ac1_feature_tables_shapes_columns_and_definitions (shapes and columns on seed 42; a hand-built fixture for the tail score with ties, rank, shared_unit_only, taxonomy and citation)` | pass | PASS |
| AC-2 | `python -m src.features.reconciliation.train` runs | it builds the training bank (seed 7, full size, `--text templated`) in a temporary directory and reads that bank's answer key, the only place in this feature that reads one. It fits three logistic models in order: risks, then duplicates, then controls, whose `risk_link` uses the just-fitted risk model's in-sample scores. Each model is `LogisticRegression(class_weight='balanced', tol=1e-10, max_iter=100000)`, lbfgs, run until it converges (measured: 29-71 iterations). Thresholds are set on the training scores, at tie-group boundaries:
- *auto-accept:* the lowest score whose at-or-above set has at least 95% precision (none if no score reaches it);
- *review floor:* the highest score whose at-or-above set holds at least 99% of the true pairs, capped at the auto-accept threshold.

Duplicates are *review-only*: they have a floor but no auto-accept, because 13 true pairs per bank cannot support a 95% precision estimate (seed 1's single auto-accepted pair was wrong). It writes `src/features/reconciliation/weights.json`. For each model the file holds the feature names, coefficients, intercept, thresholds, and the training pair each threshold falls on. It also holds a fingerprint: a SHA-256 over the training bank's file checksums and the source of `similarity.py`, `taxonomy_map.py`, `features.py`, `train.py` and `match.py`. Training runs in seconds | `reconciliation.test_matching.MatchingTests.test_ac2_committed_weights_are_current (fast: the fingerprint matches; full: a retrain gives coefficients within 1e-6, selects the same training pair for each threshold, and puts every seed-42 pair in the same band)` | pass | PASS |
| AC-3 | `pair_scores(build_dir)` in `src/features/reconciliation/match.py` applies the committed weights, unchanged, to the published bank (seed 42, AI text) | it returns, for each pair kind, every pair's probability and band (`accept`, `review` or `below`; duplicates are never `accept`).

| Kind | Auto-accepted precision | Recall at the review floor |
|---|---|---|
| Cross-source risks | at least 0.90 (measured 0.95, 38 accepted, 122 queued) | at least 0.95 (measured 101/103) |
| Cross-source controls | at least 0.90 (measured 1.00, 68 accepted, 341 queued) | at least 0.95 (measured 240/245) |
| ERM duplicates | none: review-only (14 queued) | at least 0.75 (measured 12/13) |

The test prints every count | `reconciliation.test_matching.MatchingTests.test_ac3_transfer_to_the_published_bank` | pass | PASS |
| AC-4 | the same weights are applied to seed 1 (templated) | the same bars hold. Auto-accepted precision is at least 0.90 for risks (measured 0.93, 42 accepted) and controls (measured 0.98, 95 accepted). Recall at the floor is at least 0.95 for risks (measured 103/103) and controls (measured 246/248), and at least 0.75 for duplicates (measured 13/13, 15 queued). This shows the weights are not fitted to one bank | `reconciliation.test_matching.MatchingTests.test_ac4_transfer_to_another_bank` | pass | PASS |
| AC-5 | `pair_scores` runs on a copy of the published build with `answer_key/` deleted | it returns identical scores, and within `src/features/reconciliation/` only `train.py` mentions `answer_key`. That is INV-6 for this child; child c lands the new INV-6 wording | `reconciliation.test_matching.MatchingTests.test_ac5_scoring_never_reads_the_answer_key` | pass | PASS |
| AC-6 | docs/data-model.md and the feature README are read after this change | they describe the three pair kinds and their features, the training bank, the threshold rule, review-only duplicates, `weights.json`, and the figures the built module measures on seeds 42 and 1 (L-012). They also record why the method looks as it does:
- *Raw cosines:* the templated-trained duplicate model missed 10 of 13 AI-text duplicates.
- *Plain percentiles under class weighting:* duplicate scores bunched within 1e-5, too fragile for thresholds.
- *Unweighted models:* about doubled the control queue. | `reconciliation.test_matching.MatchingTests.test_ac6_docs_describe_matching` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/reconciliation/****: `src/features/reconciliation/features.py`, `src/features/reconciliation/match.py`, `src/features/reconciliation/train.py`, `src/features/reconciliation/weights.json`
3. **Tests**: `tests/reconciliation/test_matching.py`

## Data impact
- **No new published entity.** `weights.json` is a committed model artifact inside the feature folder. Pair scores are an in-memory result; child c writes the canonical layer and the review queue.
- **Reads published files only** for scoring: risks, controls, both taxonomies, classifies, exposure, business units, mitigates, depends-on, and child a's mapping.
- **Answer keys:** only `train.py` reads one, and only the training bank's (seed 7, built in a temporary directory). The published bank's answer key is never read (INV-6; AC-5).
- The generator, its outputs and its goldens are unchanged.

## Risks
- **Transfer across text styles:** the training bank is templated and the published bank is AI text, so the transfer is not guaranteed. Signal: AC-3; raw cosines broke on exactly this.
- **Large review queue** (about 120 risk pairs, 340 control pairs and 14 duplicate pairs): honest, but child c and the page must present it well. Signal: the counts AC-3 prints.
- **Float drift across platforms:** the fit converges at `tol=1e-10`; the retrain check compares weights within 1e-6, compares thresholds by the training pair they select, and checks that every seed-42 pair keeps its band.
- **Review-only duplicates** are a choice child c must honour: the epic's rule for an IA risk reaching two ERM risks then never sees an auto-accepted duplicate pair. This is stated for c.
- **Circular `risk_link`:** controls use risk scores, so training uses in-sample risk scores on seed 7 and scoring uses the committed risk model on the scored bank. This is stated in the README.

## Deliberately not in this PR
- Canonical items, the review-queue CSV and the `akg build` step: child c.
- Published precision and recall and the citation-cue share: child d.
- Embeddings: research R4 and M2.
- Learning from reviewer decisions: parked in the epic.

Parked for later:
- 2026-11-21 012 review minors: hand-built fixture for shared_unit_only and taxonomy (ancestor direction); data-model review-floor rule should say 'capped at the auto-accept threshold'; README line 9 says every module reads published files only (train.py reads the training bank's answer key); train.py guard for a kind with zero true training pairs (from 012-match-features-training-script-and-commi)

## Lessons recorded
- L-013 Learned models must transfer across text styles: use scale-free features and converge the fit

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `fd3da673973feb35`
- Size: 5 code files, +546 / -0 lines
