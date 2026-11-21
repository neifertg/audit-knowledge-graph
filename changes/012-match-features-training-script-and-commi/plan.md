# Match features, training script and committed weights

```json plan
{
  "id": "012-match-features-training-script-and-commi",
  "tier": "standard",
  "status": "draft",
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
      "when": "`pair_features(build_dir)` runs on a full build",
      "then": "it returns three feature tables, one per pair kind, each with sorted pair IDs and named columns, computed from published files only:\n- *Cross-source risks* (every ERM x IA pair; 27,000 at seed 42), 7 columns: `word`, `char`, `rank`, `shared_entity`, `shared_unit_only`, `taxonomy`, `same_rating`.\n- *Within-ERM risk duplicates* (every unordered ERM pair; 16,110), 5 columns: `word`, `char`, `rank`, `same_node`, `same_rating`.\n- *Cross-source controls* (every ERM x IA pair; 118,105), 9 columns: `word`, `char`, `rank`, `risk_link`, `same_type`, `same_nature`, `same_frequency`, `shared_system`, `citation`.\n\nThe column definitions:\n- `word` and `char` are cosine similarities (the 1-2 gram and `char_wb` 3-5 gram TF-IDF of similarity.py), each converted to its percentile within its own table: average rank of ties, scaled 0-1. This makes the features scale-free across text styles, with no labels used.\n- `rank` is 1/position of the pair among the row item's candidates, by `word + char` raw cosine, stable order.\n- `taxonomy` is 1 when the IA risk's nearest mapped ancestor (child a's `map_taxonomy`) is the ERM risk's node or one of its ancestors.\n- `risk_link` is the highest cross-source risk score (from the committed risk model) over the pairs of risks the two controls mitigate, 0 if none.\n- `citation` is 1 when the ERM control's title subject (the text before ':') appears in the IA control's description.",
      "test": "reconciliation.test_matching.MatchingTests.test_ac1_feature_tables_shapes_columns_and_definitions (shapes and columns on seed 42; a hand-built fixture for percentile ties, rank, taxonomy and citation)",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "`python -m src.features.reconciliation.train` runs",
      "then": "it builds the training bank (seed 7, full size, `--text templated`) in a temporary directory and reads that bank's answer key, the only place in this feature that reads one. It fits three logistic models in order: risks, then duplicates, then controls, whose `risk_link` uses the just-fitted risk model. Each model is `LogisticRegression(max_iter=5000, class_weight='balanced')`, deterministic with lbfgs. Each model's two thresholds are set on its training scores:\n- *auto-accept:* the lowest score at which the pairs scoring at or above it have at least 95% precision (scanning scores from the top);\n- *review floor:* the highest score at which the pairs at or above it hold at least 99% of the true pairs.\n\nIt writes `src/features/reconciliation/weights.json` with, for each model, the feature names, coefficients, intercept and both thresholds, plus the training pair each threshold falls on. The file also holds a fingerprint: a SHA-256 over the training bank's file checksums and the source of `similarity.py`, `taxonomy_map.py`, `features.py` and `train.py`. It runs in under a minute (measured: 2 s of training plus about 3 s of features)",
      "test": "reconciliation.test_matching.MatchingTests.test_ac2_committed_weights_are_current (fast: the fingerprint matches; full: a retrain gives coefficients within 1e-6 and selects the same training pair for each threshold)",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "`pair_scores(build_dir)` applies the committed weights, unchanged, to the published bank (seed 42, AI text)",
      "then": "it returns, for each pair kind, every pair's probability and its band (`accept`, `review` or `below`).\n\n| Kind | Auto-accepted precision | Recall at the review floor |\n|---|---|---|\n| Cross-source risks | at least 0.90 (measured 1.00, 38 pairs) | at least 0.95 (measured 101/103) |\n| Cross-source controls | at least 0.90 (measured 1.00, 48 pairs) | at least 0.95 (measured 242/245) |\n| ERM duplicates | (only 4 auto-accepted, no bar) | at least 0.75 (measured 12/13) |\n\nThe test prints every count: auto-accepted, queued, and true pairs missed below the floor",
      "test": "reconciliation.test_matching.MatchingTests.test_ac3_transfer_to_the_published_bank",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the same weights are applied to seed 1 (templated)",
      "then": "the same bars hold: risks and controls auto-accepted precision at least 0.90 (measured 0.98 and 0.97), and recall at the floor at least 0.95 for both (measured 103/103 and 248/248). Duplicates' recall at the floor is at least 0.75 (measured 13/13). This shows the weights are not fitted to one bank",
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
      "then": "they describe the three pair kinds and their features, the training bank, the threshold rule, `weights.json`, and the measured figures on seeds 42 and 1, taken from the built module (L-012). They also say why the features are percentiles: with raw cosines, the templated-trained duplicate model missed 10 of 13 AI-text duplicates; with percentiles, it misses 1",
      "test": "reconciliation.test_matching.MatchingTests.test_ac6_docs_describe_matching",
      "status": "pending"
    }
  ],
  "epic": "002-e2-erm-ia-reconciliation",
  "child": "b"
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

**Evidence behind the bars.** A pre-plan measurement on 2026-11-21 imported the merged `similarity.py` and `taxonomy_map.py` and used exactly the settings pinned in AC-1 and AC-2. It trained on seed 7 and applied the result unchanged:

| Kind | Seed 42 (AI text) | Seed 1 (templated) |
|---|---|---|
| Risks | 38 auto-accepted (precision 1.00), queue 150, 2 of 103 missed | 42 (0.98), queue 170, 0 missed |
| Controls | 48 (1.00), queue 391, 3 of 245 missed | 65 (0.97), queue 390, 0 missed |
| ERM duplicates | 4 (1.00), queue 10, 1 of 13 missed | 2 (0.50), queue 12, 0 missed |

With raw cosine features instead of percentiles, risks and controls were slightly better on seed 42. The trained duplicate model, however, missed 10 of 13 AI-text duplicates: templated duplicates are near-copies, and AI ones are paraphrases. Percentiles fix that without labels.

The bars sit below these figures. Per L-012, the built module's figures are what get recorded; if a bar fails, stop and report rather than move it (L-007).

**Not tested here:** canonical assignment, the review-queue file and the build step (child c), and scoring against the published answer key for the page (child d). The tests here read the answer key only to check the bars.

## Risks
- **Transfer across text styles:** the training bank is templated and the published bank is AI text, so the transfer is not guaranteed. Signal: AC-3; this is exactly what broke the raw-cosine duplicate model.
- **Large review queue** (about 150 risk pairs and 390 control pairs): honest, but child c and the page must present it well. Signal: the counts AC-3 prints.
- **Float drift across platforms** in the retrain check: weights are compared within 1e-6, and thresholds by the training pair they select, not their value.
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
3. `pair_scores`, with the AC-3, AC-4 and AC-5 tests.
4. Docs (AC-6).
