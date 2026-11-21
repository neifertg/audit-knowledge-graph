VERDICT: READY

Reproduction (scratch script outside the repo, AC-2 settings exactly as written: title + '. ' + description, word 1-2 gram + char_wb 3-5 gram TF-IDF, both sublinear, fit on all ERM+IA risk texts, cosines summed, +0.3 shared entity else +0.15 shared business unit, nearest ERM risk with ties to lowest ID, ancestor-to-ancestor votes, share over subtree risk count, pick deepest >= 0.5 then share then ID; `no_risks` nodes unmapped with score 0):

| | Seed 42 (AI) | Seed 7 (templated) | Seed 1 (templated) | Bar |
|---|---|---|---|---|
| Nodes holding risks | 44/62 = 0.71 (plan 46/62 = 0.74) | 39/63 = 0.62 (plan 0.64) | 41/63 = 0.65 (plan 0.62) | 0.65 / 0.55 / 0.55 |
| All 75 nodes | 47/75 = 0.63 (plan 0.65) | 0.56 | 0.59 | 0.55 (seed 42) |
| Falsely `unmapped` | 2 (plan 2) | 7 (plan 7) | 9 (plan 9) | 5 / 12 / 12 |
| Per level, seed 42 | L1 6/9, L2 14/20, L3 24/33 (plan L2 16/20) | | | L1 4, L2 5, L3 16 |
| Names-only baseline | L1 4/9, L2 5/22, L3 16/44 (25/75 = 0.33) | same | same | |

Every bar clears, with the tightest margin on seed 42's holding-node accuracy (0.71 vs 0.65). Two runs gave identical rows, every target sat at an allowed level, and the 3 truly unmapped `no_risks` nodes came out `unmapped` on every seed while the 3 truly unmapped risk-holding nodes did not, as AC-3 now states. The previous critique's blocker (an unmeetable unmapped bar) and both majors (unpinned settings, no false-`unmapped` bar) are answered.

1. [minor] Seed 42 reproduces 2 nodes below the plan's figure (44/62 vs 46/62, all at L2), so some setting still differs between the plan's experiment and its own AC-2 text, even though the bars hold. Seed 1 lands 2 nodes above. -> At build time, record the figures the real module measures in the plan's evidence table (the "re-measured once" clause already allows this), so the published numbers come from the module and not the scratch experiment. Do not move any bar.
2. [minor] Test plumbing contradicts itself. The Test plan says builds go "through the existing `tests/generator/helpers.build`", while AC-4 says "a small cached builder in `tests/reconciliation/helpers.py` that takes the seed as a parameter". The existing helper hard-codes `--seed 42` and builds the sample unless `--size` is passed. -> Pick one (AC-4's new helper is cleaner) and fix the Test plan sentence. Remember `tests/reconciliation/__init__.py` so the dotted test IDs resolve.
3. [minor] AC-3's per-level bar quotes the baseline as constants (L1 4, L2 5, L3 16), but the baseline method is not pinned ("Names only (character TF-IDF)"). If the test recomputes the baseline, its settings change the bar. -> State that the test uses the fixed counts, or pin the baseline as well. I reproduced 4/5/16 with `char_wb` 3-5 grams, no sublinear tf, fit on all node names, best allowed-level ERM node, ties to the lowest ID.
4. [minor] AC-5's static check names "the module's source", but AC-2 puts settings in `similarity.py` (shared with b) as well as `taxonomy_map.py`. -> Make the check cover both files, or every file a imports from the feature folder, until c's folder-wide check lands.
5. [minor] The epic says a's "evidence comes from node names and the text of the risks each node classifies". This plan uses names only as the baseline, never as evidence, and the change is justified by measurement. -> Say in Why or Out of scope that node names are deliberately not used as evidence, so the deviation from the epic's wording is explicit when the owner approves. The added `basis` column is within the epic's allowance ("column lists are final in each child's plan").
6. [minor] Per-level bars and false-`unmapped` counts rest on small numbers (L1 has 9 nodes; one flip moves accuracy by 0.11). The bars are fixed with margin, which is acceptable. -> Keep AC-3's printed counts per level and per seed, so a later failure is easy to read.

Not checked: the plan's own experiment script (not in the repo), so the source of the 2-node seed-42 gap is unknown; child b's actual use of the mapping as a feature.
