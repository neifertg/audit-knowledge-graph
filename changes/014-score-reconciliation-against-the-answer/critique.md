VERDICT: READY

The revision answers every point of the previous critique:
- Orphans: AC-3 caveat 1 now uses the epic's wording ("helps the figures and is not matcher skill"), drops "pair figures exclude them", and AC-1 adds the orphan figures (31; 0 merged; 2 queue rows).
- Ablation: the model is committed in `weights.json` as `control_without_citation`, with thresholds by training pair and 012's 1e-6 currency test extended to it. AC-3's exact equality now depends only on committed weights applied to the golden-frozen seed-42 build.
- Every figure definition is pinned in AC-1, and the mini build exercises each one.
- Taxonomy precision and recall per level are reported.
- Every ratio is stored with its `a/b`.
- The one-bank and conservative-threshold caveats are added.
- AC-4 cross-checks against figures recorded independently in docs/data-model.md.
- The README, the static check and INV-6's enforced-by entry are in scope.

I checked the evidence arithmetic: 33+68+2=103, 68+172+5=245, 101/103 and 240/245, 6+14+24=44 over 9+20+33=62, and 122+14+341+5=482. It is consistent with the data model. Nothing left is a blocker or major.

1. [minor] There is a stale sentence in the test plan. "The ablation retrain in AC-2 builds seed 7 (under a second) and fits once (seconds)" contradicts AC-2's "No training runs while scoring or testing". The only retrain is inside 012's existing currency test (`test_matching.py:80`), which already builds seed 7 and retrains every kind. -> Reword: the ablated entry is retrained only inside the extended currency test. Also extend that test's final band-identity check (`pair_scores(full_build(42), fresh)`, which loops over `M.KINDS` only) to the ablated model's bands on seed 42. Otherwise a fresh-retrain threshold flip there goes unnoticed.
2. [minor] AC-5 still says "the citation-cue finding and both caveats", but AC-3 now has four caveats. -> Say "the four caveats". Make the AC-5 test check one key phrase per caveat (for example "not matcher skill", "same generator", "one bank", "conservative"), not just the figures.
3. [minor] Caveat 3 compares unlike figures. "the precision of 1.00 rests on 33 risk and 68 control merges ... and on seed 1 risks reached 0.93". 1.00 is merged (final-canonical) precision. Seed 1's 0.93 is raw auto-accept precision (012: "42 (0.93)"). Seed 42's own raw figure is 36/38 = 0.95. -> Label the seed-1 figure as raw auto-accept precision, or quote seed 42's raw 36/38 beside it, so the caveat does not mix definitions.
4. [minor] AC-2 quotes "82 accepted at precision 0.89" without its count, against AC-1's own rule that every ratio is stored as `a/b`. -> Record the numerator (for example 73/82) in the plan's evidence and in `scores.json`.
5. [minor] Taxonomy recall denominators include truly mapped nodes that hold no risks (L3 recall is 24/41, against 33 L3 nodes holding risks). The mapper leaves those nodes `unmapped` by design (`basis` = `no_risks`), and no risk's placement depends on them. -> State this in the AC-5 docs section in one sentence, so recall below accuracy is not read as a mapper error on risk-bearing nodes.
6. [minor] AC-4's identity "merged plus queued plus missed true pairs equals true pairs" holds by construction, because *missed* is defined as the remainder. The independent checks are the four data-model figures and AC-1's mini build, which is enough. -> Either drop the identity or replace it with something that can fail. One option: no true pair is counted both merged and queued.

Not checked: I did not re-run the build or the ablation, so the seed-42 figures (including 82/505/1 without the cue, the 2 orphan-touching queue rows, and the per-level taxonomy precision and recall) are taken from the plan as measured. Whether `score.py`'s `__main__` full build plus reconcile fits CI time is also unchecked, although the AC-3 test uses the cached build.
