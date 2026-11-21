# Map IA taxonomy onto ERM taxonomy

```json plan
{
  "id": "011-map-ia-taxonomy-onto-erm-taxonomy",
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
      "when": "`map_taxonomy(build_dir)` runs on a full build",
      "then": "it returns one row per IA taxonomy node (all 75 at seed 42): `ia_node_id`, `erm_node_id` or `unmapped`, `score` and `basis`. `basis` is `vote` for a node whose subtree holds IA risks, and `no_risks` otherwise; a `no_risks` node is `unmapped` with score 0, since there is nothing to map it by and no risk depends on it. `score` is the winning ERM node's vote share; for a `vote` node left `unmapped` it is the best allowed share found (below 0.5). Every target is an ERM node at an allowed level for its IA node's level (IA L1 -> ERM L1; IA L2 -> ERM L1 or L2; IA L3 -> ERM L2 or L3, the E1 answer-key schema). Two runs give identical rows",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac1_one_row_per_ia_node_at_allowed_levels_deterministic",
      "status": "pass"
    },
    {
      "id": "AC-2",
      "when": "the method runs",
      "then": "it is the risk-level vote measured before this plan, with every setting a module constant in `src/features/reconciliation/similarity.py` (shared with child b) or `taxonomy_map.py`:\n- *Risk similarity:* the text is `title + '. ' + description`. Word TF-IDF uses 1-2 grams and character TF-IDF uses `char_wb` 3-5 grams, both with `sublinear_tf`, both fitted on all ERM and IA risk texts. Similarity is the sum of the two cosines, plus 0.3 when the risks share an exposed entity, or else plus 0.15 when they share a business unit of their exposed entities.\n- *Votes:* each IA risk votes for its most similar ERM risk, with ties going to the lowest ERM risk ID. The vote counts for every ancestor of the IA risk's node, toward every ancestor of the ERM risk's node.\n- *Shares:* an IA node's share for an ERM node is votes divided by the number of IA risks in the IA node's subtree.\n- *Pick:* among ERM nodes at an allowed level with share of at least 0.5, take the deepest, then the highest share, then the lowest ERM node ID. If none qualifies, the node is `unmapped`.",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac2_vote_picks_deepest_node_with_majority (hand-built two-tree fixture with known votes: a majority at L3, a split that falls back to L2, a no-majority `unmapped`, a tie broken by ID, and a `no_risks` node)",
      "status": "pass"
    },
    {
      "id": "AC-3",
      "when": "the mapping is scored against the answer key's taxonomy_map on the seed-42 full build with AI text (the default)",
      "then": "on the 62 IA nodes holding risks: accuracy is at least 0.65 (measured 0.74, 46 of 62); each level's correct count is at least the names-only baseline's on all nodes at that level (L1 4, L2 5, L3 16; measured L1 6/9, L2 16/20, L3 24/33); and at most 5 are falsely `unmapped` (measured 2). On all 75 nodes, accuracy is at least 0.55 (measured 0.65). Known limit, stated and not barred: the 3 truly unmapped nodes that hold risks are not detected, because their risks truly sit in one ERM node (a generator design point); only the 3 truly unmapped `no_risks` nodes come out `unmapped`. The test prints counts as well as ratios",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac3_accuracy_beats_names_only_baseline",
      "status": "pass"
    },
    {
      "id": "AC-4",
      "when": "the same mapping runs on the seed-1 and seed-7 full builds with templated text",
      "then": "on the nodes holding risks, accuracy is at least 0.55 on each (measured 0.64 on seed 7 and 0.62 on seed 1), and at most 12 are falsely `unmapped` (measured 7 and 9), so the method is not fitted to seed 42. Builds for other seeds use a small cached builder in `tests/reconciliation/helpers.py` that takes the seed as a parameter",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac4_holds_on_other_seeds",
      "status": "pass"
    },
    {
      "id": "AC-5",
      "when": "the mapping runs on a copy of the build with `answer_key/` deleted",
      "then": "it returns rows identical to those from the full build directory, and the module's source never mentions `answer_key` (INV-6 for this module; child c adds the folder-wide check)",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac5_never_reads_the_answer_key",
      "status": "pass"
    },
    {
      "id": "AC-6",
      "when": "docs/data-model.md is read after this change",
      "then": "it describes the IA-to-ERM mapping as E2 output: `ia_maps_to_erm` with columns `ia_node_id`, `erm_node_id` (or `unmapped`), `score` and `basis`, the allowed levels, the method in one paragraph, the measured accuracy, and the known limit (unmapped nodes that hold risks are not detected; `no_risks` nodes are left `unmapped`); and `src/features/reconciliation/README.md` exists (capitan feature)",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac6_data_model_and_readme_describe_the_mapping",
      "status": "pass"
    }
  ],
  "epic": "002-e2-erm-ia-reconciliation",
  "child": "a",
  "approved": "2026-11-21",
  "approved_hash": "080962f701c7fe35",
  "in_progress": "2026-11-21"
}
```

## Why
E2 child a (O3). IA's audit universe and ERM's Basel-style taxonomy are separate trees that map unevenly: level mismatches, 6 IA nodes with no ERM counterpart, and misfiled risks. Child b uses this mapping as a matching feature, and child c uses it to place IA risks that match no ERM risk. Names alone get only a third of nodes right, so the mapping has to come from what the nodes hold.

## Data impact
- **New E2 output relationship** `TAXONOMY_NODE ia_maps_to_erm` (already in the ER diagram as E2 output): `ia_node_id`, `erm_node_id` or `unmapped`, `score`, `basis`. In this child it is a function result; child c writes it to `<out>/reconciled/ia_maps_to_erm.csv` (the epic's output contract).
- **Reads published files only:** both taxonomies and their parent links, the classifies, risk, exposure and business-unit files.
- **Invariants:**
  - INV-6: this module never reads the answer key (AC-5); tests read it only to score.
  - INV-10 is unaffected: the mapping is E2 output, the one place ERM-IA links may exist.
  - The allowed-level rule from E1's answer-key schema now also binds E2's output (AC-1).
- The generator, its outputs and its goldens are unchanged.

## Test plan
Tests live in `tests/reconciliation/`, using real builds (seeds 42, 1 and 7, full size) through the existing `tests/generator/helpers.build`, which caches each build. The whole suite stays the done-check.

**Evidence behind the bars.** A scratch experiment on 2026-11-21 measured each method. Seed 42 uses AI text; seeds 7 and 1 use templated text.

| Method | Seed 42 | Seed 7 | Seed 1 |
|---|---|---|---|
| Names only (character TF-IDF), all 75 nodes | 0.33 | 0.33 | 0.32 |
| Pooled risk text under each node, all nodes | 0.60 | 0.56 | |
| **Risk vote, nodes holding risks** | **0.74 (46/62)** | **0.64 (40/63)** | **0.62 (39/63)** |
| Risk vote, all 75 nodes (`no_risks` counted as `unmapped`) | 0.65 | 0.57 | 0.56 |
| Falsely `unmapped`, nodes holding risks | 2 | 7 | 9 |

12-13 IA nodes per seed hold no risks. They produce every correct `unmapped` (3 of 6), and they don't affect risk placement. A first critique showed the earlier draft's name fallback for those nodes contradicted the experiment, and that the vote cannot detect unmapped nodes that hold risks. Both are now stated.

The bars sit below the measured figures with margin. If the build measures differently from the experiment (for example, a different tie-break), the figures are re-measured once before the bars are checked, and the plan is not changed to fit (L-007): if a bar fails, stop and report.

**Not tested here:** the build step and the CSV file (child c), and use as a matching feature (child b).

## Risks
- **The vote looks circular.** It uses risk similarity before child b's matcher exists. It is a deliberately simple nearest-neighbour vote, and b may later replace its similarity with the learned score. Signal: AC-3 and AC-4 figures.
- **Misfiled IA risks (10-20%, by design) add noise to votes.** A majority threshold absorbs it. Signal: L3 accuracy, which is the lowest level (measured 26/44).
- **Speed.** About 150 x 180 risk similarities per build: well under a second.

## Out of scope
- Writing `ia_maps_to_erm.csv` and the `akg build` step: child c.
- Learned weights for the vote: possible later via child b's training bank; parked if it comes up.
- Per-risk placement scoring, including misfiled risks: children c and d.

## Relevant lessons
- **L-007** (measure early; no tuning after the fact): the bars come from a pre-plan measurement across three seeds and are fixed here.
- **L-008** (exact shared phrases become lookup keys): node names share some words across the trees. Names alone are measured as the baseline the method must beat.
- **L-003** (shared vocabulary): the vote relies on it at the risk level, and AC-4 checks it holds on templated text too.
- **L-002, L-011:** not applicable (no AI text is written here).

## Slices
1. `capitan feature src/features/reconciliation`; the similarity helper and the vote, with the AC-2 fixture test.
2. The AC-1, AC-3, AC-4 and AC-5 tests on real builds.
3. docs/data-model.md and the README (AC-6).
