# Map IA taxonomy onto ERM taxonomy

```json plan
{
  "id": "011-map-ia-taxonomy-onto-erm-taxonomy",
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
      "when": "`map_taxonomy(build_dir)` runs on a full build",
      "then": "it returns one row per IA taxonomy node (all 75 at seed 42): `ia_node_id`, `erm_node_id` or `unmapped`, and `score` (the winning vote share, 0-1). Every target is an ERM node at an allowed level for its IA node's level (IA L1 -> ERM L1; IA L2 -> ERM L1 or L2; IA L3 -> ERM L2 or L3, the E1 answer-key schema). Ties break by the lower ERM node ID, and two runs give identical rows",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac1_one_row_per_ia_node_at_allowed_levels_deterministic",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the method runs",
      "then": "it is the risk-level vote measured before this plan. Each IA risk votes for the ERM risk most similar to it: word plus character TF-IDF on title and description, +0.3 when they share an exposed entity, +0.15 when they share only a business unit. Each IA node takes the deepest allowed ERM node holding at least 0.5 of the votes of the IA risks in its subtree, or `unmapped` when none does. A node whose subtree holds no IA risk maps by name similarity (character TF-IDF), with score 0. The weights 0.3, 0.15 and 0.5 are module constants, set from the pre-plan experiment and documented in the feature README",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac2_vote_picks_deepest_node_with_majority (hand-built two-tree fixture with known votes, including an unmapped case and a no-risk node)",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the mapping is scored against the answer key's taxonomy_map on the seed-42 full build with AI text (the default)",
      "then": "overall accuracy (exact target, `unmapped` counting as a target) is at least 0.55, against 0.65 measured and 0.33 for names alone. Each level's accuracy is at least the names-only baseline's at that level (measured L1 4/9, L2 5/22, L3 16/44). At least 3 of the 6 truly unmapped nodes are predicted `unmapped`. The test prints the measured figures",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac3_accuracy_beats_names_only_baseline",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the same mapping runs on the seed-1 and seed-7 full builds with templated text",
      "then": "overall accuracy is at least 0.50 on each (measured 0.56 and 0.57), so the method is not fitted to seed 42",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac4_holds_on_other_seeds",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the mapping runs on a copy of the build with `answer_key/` deleted",
      "then": "it returns rows identical to those from the full build directory, and the module's source never mentions `answer_key` (INV-6 for this module; child c adds the folder-wide check)",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac5_never_reads_the_answer_key",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "docs/data-model.md is read after this change",
      "then": "it describes the IA-to-ERM mapping as E2 output: `ia_maps_to_erm` with columns `ia_node_id`, `erm_node_id` (or `unmapped`) and `score`, the allowed levels, the method in one paragraph, and the measured accuracy; and `src/features/reconciliation/README.md` exists (capitan feature)",
      "test": "reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac6_data_model_and_readme_describe_the_mapping",
      "status": "pending"
    }
  ],
  "epic": "002-e2-erm-ia-reconciliation",
  "child": "a"
}
```

## Why
E2 child a (O3). IA's audit universe and ERM's Basel-style taxonomy are separate trees that map unevenly: level mismatches, 6 IA nodes with no ERM counterpart, and misfiled risks. Child b uses this mapping as a matching feature, and child c uses it to place IA risks that match no ERM risk. Names alone get only a third of nodes right, so the mapping has to come from what the nodes hold.

## Data impact
- **New E2 output relationship** `TAXONOMY_NODE ia_maps_to_erm` (already in the ER diagram as E2 output): `ia_node_id`, `erm_node_id` or `unmapped`, `score`. In this child it is a function result; child c writes it to `<out>/reconciled/ia_maps_to_erm.csv` (the epic's output contract).
- **Reads published files only:** both taxonomies and their parent links, the classifies, risk, exposure and business-unit files.
- **Invariants:**
  - INV-6: this module never reads the answer key (AC-5); tests read it only to score.
  - INV-10 is unaffected: the mapping is E2 output, the one place ERM-IA links may exist.
  - The allowed-level rule from E1's answer-key schema now also binds E2's output (AC-1).
- The generator, its outputs and its goldens are unchanged.

## Test plan
Tests live in `tests/reconciliation/`, using real builds (seeds 42, 1 and 7, full size) through the existing `tests/generator/helpers.build`, which caches each build. The whole suite stays the done-check.

**Evidence behind the bars.** A scratch experiment on 2026-11-21 measured accuracy across all 75 IA nodes:

| Method | Seed 42 (AI) | Seed 7 | Seed 1 |
|---|---|---|---|
| Names only (character TF-IDF) | 0.33 | 0.33 | 0.32 |
| Path words | 0.41-0.45 | | |
| Pooled risk text under each node | 0.60 | 0.56 | |
| Risk vote (top-1, majority 0.5) | 0.65 | 0.57 | 0.56 |

The bars sit below the measured figures with margin, and above the names-only baseline. No band is tuned after the fact (L-007): if a bar fails, stop and report.

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
