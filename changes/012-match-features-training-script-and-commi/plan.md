# Match features, training script and committed weights

```json plan
{
  "id": "012-match-features-training-script-and-commi",
  "tier": "standard",
  "status": "in-progress",
  "created": "2026-11-21",
  "objective": "O3",
  "areas": [
    "src/features/reconciliation/**",
    "tests/**",
    "docs/data-model.md"
  ],
  "timebox": "1.5 days. Past this, stop and re-plan or split.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`pair_features(build_dir)` in `src/features/reconciliation/features.py` runs on a full build",
      "then": "it returns three feature tables, one per pair kind, each with sorted pair IDs and named columns, computed from published files only. Texts are `title + '. ' + description` for risks and controls alike. TF-IDF is similarity.py's two vectorizers, both fitted on the ERM and IA texts of that item type together.\n\n- *Cross-source risks* (every ERM x IA pair; 27,000 at seed 42), 7 columns:\n  - `word`, `char`: cosines, each turned into a tail score.\n  - `rank`: 1/position of the ERM risk among the IA risk's ERM candidates, by raw `word + char` cosine, in a stable order.\n  - `shared_entity`: the two risks share an exposed entity.\n  - `shared_unit_only`: they share a business unit of their exposed entities but no exposed entity.\n  - `taxonomy`: the IA risk's nearest ancestor-or-self that child a maps (not `unmapped`) maps to the ERM risk's node or one of its ancestors.\n  - `same_rating`.\n- *Within-ERM risk duplicates* (every unordered ERM pair; 16,110), 5 columns:\n  - `word`, `char`: tail scores over these 16,110 pairs.\n  - `rank`: the larger of the two directions' 1/position, ignoring self-pairs.\n  - `same_node`, `same_rating`.\n\n  Shared entity and taxonomy are left out: ERM exposure is business-unit wide, so nearly every same-unit pair shares an entity, and both risks sit in one tree.\n- *Cross-source controls* (every ERM x IA pair; 118,105), 9 columns:\n  - `word`, `char` and `rank`, as for risks, with the IA control as the row.\n  - `risk_link`: the highest cross-source risk score from the risk model over the pairs of risks the two controls mitigate, 0 if none.\n  - `same_type`, `same_nature`, `same_frequency`.\n  - `shared_system`.\n  - `citation`: 1 when the ERM title's text before its first ':' (trimmed and lower-cased) occurs in the lower-cased IA description; 0 for a title with no ':'.\n\nA *tail score* is computed with numpy only (no scipy) from the value's percentile `p` within its own table (average rank of ties, scaled 0-1) as `-log10(1 - p + 1/n)`. That makes it scale-free across text styles without labels, and spreads out the top candidates.",
      "test": "reconciliation.test_matching.MatchingTests.test_ac1_feature_tables_shapes_columns_and_definitions (shapes and columns on seed 42; a hand-built fixture for the tail score with ties, rank, shared_unit_only, taxonomy and citation)",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "`python -m src.features.reconciliation.train` runs",
      "then": "it builds the training bank (seed 7, full size, `--text templated`) in a temporary directory and reads that bank's answer key, the only place in this feature that reads one. It fits three logistic models in order: risks, then duplicates, then controls, whose `risk_link` uses the just-fitted risk model's in-sample scores. Each model is `LogisticRegression(class_weight='balanced', tol=1e-10, max_iter=100000)`, lbfgs, run until it converges (measured: 29-71 iterations). Thresholds are set on the training scores, at tie-group boundaries:\n- *auto-accept:* the lowest score whose at-or-above set has at least 95% precision (none if no score reaches it);\n- *review floor:* the highest score whose at-or-above set holds at least 99% of the true pairs, capped at the auto-accept threshold.\n\nDuplicates are *review-only*: they have a floor but no auto-accept, because 13 true pairs per bank cannot support a 95% precision estimate (seed 1's single auto-accepted pair was wrong). It writes `src/features/reconciliation/weights.json`. For each model the file holds the feature names, coefficients, intercept, thresholds, and the training pair each threshold falls on. It also holds a fingerprint: a SHA-256 over the training bank's file checksums and the source of `similarity.py`, `taxonomy_map.py`, `features.py`, `train.py` and `match.py`. Training runs in seconds",
      "test": "reconciliation.test_matching.MatchingTests.test_ac2_committed_weights_are_current (fast: the fingerprint matches; full: a retrain gives coefficients within 1e-6, selects the same training pair for each threshold, and puts every seed-42 pair in the same band)",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "`pair_scores(build_dir)` in `src/features/reconciliation/match.py` applies the committed weights, unchanged, to the published bank (seed 42, AI text)",
      "then": "it returns, for each pair kind, every pair's probability and band (`accept`, `review` or `below`; duplicates are never `accept`).\n\n| Kind | Auto-accepted precision | Recall at the review floor |\n|---|---|---|\n| Cross-source risks | at least 0.90 (measured 0.95, 38 accepted, 122 queued) | at least 0.95 (measured 101/103) |\n| Cross-source controls | at least 0.90 (measured 1.00, 68 accepted, 341 queued) | at least 0.95 (measured 240/245) |\n| ERM duplicates | none: review-only (14 queued) | at least 0.75 (measured 12/13) |\n\nThe test prints every count",
      "test": "reconciliation.test_matching.MatchingTests.test_ac3_transfer_to_the_published_bank",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the same weights are applied to seed 1 (templated)",
      "then": "the same bars hold. Auto-accepted precision is at least 0.90 for risks (measured 0.93, 42 accepted) and controls (measured 0.98, 95 accepted). Recall at the floor is at least 0.95 for risks (measured 103/103) and controls (measured 246/248), and at least 0.75 for duplicates (measured 13/13, 15 queued). This shows the weights are not fitted to one bank",
      "test": "reconciliation.test_matching.MatchingTests.test_ac4_transfer_to_another_bank",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "`pair_scores` runs on a copy of the published build with `answer_key/` deleted",
      "then": "it returns identical scores, and within `src/features/reconciliation/` only `train.py` mentions `answer_key`. That is INV-6 for this child; child c lands the new INV-6 wording",
      "test": "reconciliation.test_matching.MatchingTests.test_ac5_scoring_never_reads_the_answer_key",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "docs/data-model.md and the feature README are read after this change",
      "then": "they describe the three pair kinds and their features, the training bank, the threshold rule, review-only duplicates, `weights.json`, and the figures the built module measures on seeds 42 and 1 (L-012). They also record why the method looks as it does:\n- *Raw cosines:* the templated-trained duplicate model missed 10 of 13 AI-text duplicates.\n- *Plain percentiles under class weighting:* duplicate scores bunched within 1e-5, too fragile for thresholds.\n- *Unweighted models:* about doubled the control queue.",
      "test": "reconciliation.test_matching.MatchingTests.test_ac6_docs_describe_matching",
      "status": "pending"
    }
  ],
  "epic": "002-e2-erm-ia-reconciliation",
  "child": "b",
  "approved": "2026-11-21",
  "approved_hash": "240cb70b186a667f",
  "in_progress": "2026-11-21"
}
```

## Why
E2 child b (O3). Child c needs a score and a band for every candidate pair before it can build canonical items and the review queue. Research R1 showed text plus structure reaches defensible accuracy with no embeddings. The owner chose (R1) to learn the weights once on a separate training bank, so the published bank's answer key is never read.

## Data impact
- **No new published entity.** `weights.json` is a committed model artifact inside the feature folder. Pair scores are an in-memory result; child c writes the canonical layer and the review queue.
- **Reads published files only** for scoring: risks, controls, both taxonomies, classifies, exposure, business units, mitigates, depends-on, and child a's mapping.
- **Answer keys:** only `train.py` reads one, and only the training bank's (seed 7, built in a temporary directory). The published bank's answer key is never read (INV-6; AC-5).
- The generator, its outputs and its goldens are unchanged.

## Test plan
Tests go in `tests/reconciliation/test_matching.py`, using the cached builder from 011 for seeds 42 and 1. The full-retrain half of AC-2 builds seed 7 itself (under a second). The whole suite stays the done-check.

**Evidence behind the bars.** A second pre-plan measurement on 2026-11-21, after a critique, imported the merged `similarity.py` and `taxonomy_map.py` and used exactly the settings pinned in AC-1 and AC-2 (tail scores, balanced weighting, `tol=1e-10`, tie-boundary thresholds). It trained on seed 7 and applied the models unchanged:

| Kind | Seed 42 (AI text) | Seed 1 (templated) |
|---|---|---|
| Risks | 38 auto-accepted (precision 0.95), queue 122, 2 of 103 missed | 42 (0.93), queue 131, 0 missed |
| Controls | 68 (1.00), queue 341, 5 of 245 missed | 95 (0.98), queue 318, 2 missed |
| ERM duplicates (review-only) | queue 14, 1 of 13 missed | queue 15, 0 missed |

The gap between the duplicate model's floor and its notional auto-accept threshold is 8e-3, far above float drift. Variants rejected:
- *Raw cosines:* 10 of 13 AI duplicates missed.
- *Plain percentiles:* the duplicate gap was 7e-6, and the first fit stopped before converging at the default tolerance, moving coefficients by up to 0.38.
- *Unweighted:* the control queue was 747.

The bars sit below these figures. Per L-012, the built module's figures are what get recorded; if a bar fails, stop and report rather than move it (L-007).

**Not tested here:** canonical assignment, the review-queue file and the build step (child c), and scoring against the published answer key for the page (child d). The tests here read the answer key only to check the bars.

## Risks
- **Transfer across text styles:** the training bank is templated and the published bank is AI text, so the transfer is not guaranteed. Signal: AC-3; raw cosines broke on exactly this.
- **Large review queue** (about 120 risk pairs, 340 control pairs and 14 duplicate pairs): honest, but child c and the page must present it well. Signal: the counts AC-3 prints.
- **Float drift across platforms:** the fit converges at `tol=1e-10`; the retrain check compares weights within 1e-6, compares thresholds by the training pair they select, and checks that every seed-42 pair keeps its band.
- **Review-only duplicates** are a choice child c must honour: the epic's rule for an IA risk reaching two ERM risks then never sees an auto-accepted duplicate pair. This is stated for c.
- **Circular `risk_link`:** controls use risk scores, so training uses in-sample risk scores on seed 7 and scoring uses the committed risk model on the scored bank. This is stated in the README.

## Out of scope
- Canonical items, the review-queue CSV and the `akg build` step: child c.
- Published precision and recall and the citation-cue share: child d.
- Embeddings: research R4 and M2.
- Learning from reviewer decisions: parked in the epic.

## Relevant lessons
- **L-012** (quote the built module's figures): the measurement imported the merged modules and the pinned settings, and the docs record the build's figures.
- **L-007** (measure early, no tuning after): the bars are fixed from the pre-plan measurement; a failure stops the build.
- **L-008** (exact shared phrases become lookup keys): the citation feature *is* such a key, documented and deliberate; child d measures its share.
- **L-010** (AI paraphrase erases shared wording): the reason for the percentile features.

## Slices
1. `features.py`: the three tables, with the AC-1 fixture test.
2. `train.py` and `weights.json`, with the AC-2 tests.
3. `match.py` (`pair_scores`), with the AC-3, AC-4 and AC-5 tests.
4. Docs (AC-6).
