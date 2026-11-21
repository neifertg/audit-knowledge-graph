# Map IA taxonomy onto ERM taxonomy

Change `011-map-ia-taxonomy-onto-erm-taxonomy` · objective **O3**: It shows, and measures, the realistic hard part: reconciling ERM's and IA's separate risk taxonomies, risks and controls into one framework (ERM's Basel-style taxonomy). Signal: precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue rather than being merged silently.

## Why
E2 child a (O3). IA's audit universe and ERM's Basel-style taxonomy are separate trees that map unevenly: level mismatches, 6 IA nodes with no ERM counterpart, and misfiled risks. Child b uses this mapping as a matching feature, and child c uses it to place IA risks that match no ERM risk. Names alone get only a third of nodes right, so the mapping has to come from what the nodes hold.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `map_taxonomy(build_dir)` runs on a full build | it returns one row per IA taxonomy node (all 75 at seed 42): `ia_node_id`, `erm_node_id` or `unmapped`, `score` and `basis`. `basis` is `vote` for a node whose subtree holds IA risks, and `no_risks` otherwise; a `no_risks` node is `unmapped` with score 0, since there is nothing to map it by and no risk depends on it. `score` is the winning ERM node's vote share; for a `vote` node left `unmapped` it is the best allowed share found (below 0.5). Every target is an ERM node at an allowed level for its IA node's level (IA L1 -> ERM L1; IA L2 -> ERM L1 or L2; IA L3 -> ERM L2 or L3, the E1 answer-key schema). Two runs give identical rows | `reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac1_one_row_per_ia_node_at_allowed_levels_deterministic` | pass | PASS |
| AC-2 | the method runs | it is the risk-level vote measured before this plan, with every setting a module constant in `src/features/reconciliation/similarity.py` (shared with child b) or `taxonomy_map.py`:
- *Risk similarity:* the text is `title + '. ' + description`. Word TF-IDF uses 1-2 grams and character TF-IDF uses `char_wb` 3-5 grams, both with `sublinear_tf`, both fitted on all ERM and IA risk texts. Similarity is the sum of the two cosines, plus 0.3 when the risks share an exposed entity, or else plus 0.15 when they share a business unit of their exposed entities.
- *Votes:* each IA risk votes for its most similar ERM risk, with ties going to the lowest ERM risk ID. The vote counts for every ancestor of the IA risk's node, toward every ancestor of the ERM risk's node.
- *Shares:* an IA node's share for an ERM node is votes divided by the number of IA risks in the IA node's subtree.
- *Pick:* among ERM nodes at an allowed level with share of at least 0.5, take the deepest, then the highest share, then the lowest ERM node ID. If none qualifies, the node is `unmapped`. | `reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac2_vote_picks_deepest_node_with_majority (hand-built two-tree fixture with known votes: a majority at L3, a split that falls back to L2, a no-majority `unmapped`, a tie broken by ID, and a `no_risks` node)` | pass | PASS |
| AC-3 | the mapping is scored against the answer key's taxonomy_map on the seed-42 full build with AI text (the default) | on the 62 IA nodes holding risks: accuracy is at least 0.65 (measured 0.74, 46 of 62); each level's correct count is at least the names-only baseline's on all nodes at that level (L1 4, L2 5, L3 16; measured L1 6/9, L2 16/20, L3 24/33); and at most 5 are falsely `unmapped` (measured 2). On all 75 nodes, accuracy is at least 0.55 (measured 0.65). Known limit, stated and not barred: the 3 truly unmapped nodes that hold risks are not detected, because their risks truly sit in one ERM node (a generator design point); only the 3 truly unmapped `no_risks` nodes come out `unmapped`. The test prints counts as well as ratios | `reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac3_accuracy_beats_names_only_baseline` | pass | PASS |
| AC-4 | the same mapping runs on the seed-1 and seed-7 full builds with templated text | on the nodes holding risks, accuracy is at least 0.55 on each (measured 0.64 on seed 7 and 0.62 on seed 1), and at most 12 are falsely `unmapped` (measured 7 and 9), so the method is not fitted to seed 42. Builds for other seeds use a small cached builder in `tests/reconciliation/helpers.py` that takes the seed as a parameter | `reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac4_holds_on_other_seeds` | pass | PASS |
| AC-5 | the mapping runs on a copy of the build with `answer_key/` deleted | it returns rows identical to those from the full build directory, and the module's source never mentions `answer_key` (INV-6 for this module; child c adds the folder-wide check) | `reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac5_never_reads_the_answer_key` | pass | PASS |
| AC-6 | docs/data-model.md is read after this change | it describes the IA-to-ERM mapping as E2 output: `ia_maps_to_erm` with columns `ia_node_id`, `erm_node_id` (or `unmapped`), `score` and `basis`, the allowed levels, the method in one paragraph, the measured accuracy, and the known limit (unmapped nodes that hold risks are not detected; `no_risks` nodes are left `unmapped`); and `src/features/reconciliation/README.md` exists (capitan feature) | `reconciliation.test_taxonomy_map.TaxonomyMapTests.test_ac6_data_model_and_readme_describe_the_mapping` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/reconciliation/****: `src/features/reconciliation/__init__.py`, `src/features/reconciliation/similarity.py`, `src/features/reconciliation/taxonomy_map.py`
3. **Tests**: `tests/reconciliation/__init__.py`, `tests/reconciliation/helpers.py`, `tests/reconciliation/test_taxonomy_map.py`

## Data impact
- **New E2 output relationship** `TAXONOMY_NODE ia_maps_to_erm` (already in the ER diagram as E2 output): `ia_node_id`, `erm_node_id` or `unmapped`, `score`, `basis`. In this child it is a function result; child c writes it to `<out>/reconciled/ia_maps_to_erm.csv` (the epic's output contract).
- **Reads published files only:** both taxonomies and their parent links, the classifies, risk, exposure and business-unit files.
- **Invariants:**
  - INV-6: this module never reads the answer key (AC-5); tests read it only to score.
  - INV-10 is unaffected: the mapping is E2 output, the one place ERM-IA links may exist.
  - The allowed-level rule from E1's answer-key schema now also binds E2's output (AC-1).
- The generator, its outputs and its goldens are unchanged.

## Risks
- **The vote looks circular.** It uses risk similarity before child b's matcher exists. It is a deliberately simple nearest-neighbour vote, and b may later replace its similarity with the learned score. Signal: AC-3 and AC-4 figures.
- **Misfiled IA risks (10-20%, by design) add noise to votes.** A majority threshold absorbs it. Signal: L3 accuracy, which is the lowest level (measured 26/44).
- **Speed.** About 150 x 180 risk similarities per build: well under a second.

## Deliberately not in this PR
- Writing `ia_maps_to_erm.csv` and the `akg build` step: child c.
- Learned weights for the vote: possible later via child b's training bank; parked if it comes up.
- Per-risk placement scoring, including misfiled risks: children c and d.

Parked for later:
- 2026-11-21 011 review minors: test the vote's tie between equally similar ERM risks (lowest risk ID); give seed 7/1 counts and per-level figures in docs/data-model.md (from 011-map-ia-taxonomy-onto-erm-taxonomy)

## Lessons recorded
- L-012 Quote the built module's figures, not the pre-plan experiment's

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `5406233057191383`
- Size: 6 code files, +290 / -0 lines
