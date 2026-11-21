VERDICT: REVISE

Reproduction: I rebuilt seeds 7 (templated), 42 (AI) and 1 (templated) and reran the pre-plan script with PCT=1. Every figure in the plan's evidence table came out exactly the same (training took 2 s, features about 3 s per bank). The figures are real. The issues below are about whether the plan text pins what produced them and whether the tests are sound.

1. [major] AC-2 says "`LogisticRegression(max_iter=5000, class_weight='balanced')`, deterministic with lbfgs" and the full test expects "coefficients within 1e-6". With the default `tol=1e-4`, lbfgs stops early: 23 iterations for risks and 18 for duplicates on seed 7. Refitting the same data with `tol=1e-10` moves coefficients by up to 0.29 (risks) and 0.38 (duplicates). So the committed weights are wherever the optimizer happened to stop, not the unique optimum of a convex problem. A Linux CI retrain with different BLAS or thread counts can stop somewhere else, far outside 1e-6, and that is exactly the Windows-vs-Linux case the epic's 1e-6 rule exists for. -> Pin a tight `tol` (for example 1e-10) in AC-2 so the fit converges to the optimum, then re-measure. With `tol=1e-10` all the bars still hold, but the control figures shift: seed 42 gives 49 auto-accepted (1.00) and a queue of 378; seed 1 gives 64 (0.97) and 381. Record the re-measured figures (L-012).

2. [major] The duplicate model is saturated, so its bands rest on differences of about 1e-6. On seed 7, the top 20 duplicate scores all fall between 0.994788 and 0.994800, true and false pairs interleaved. The auto-accept threshold is 0.994798 and the review floor 0.994792, only 6e-6 apart. That spread is the same size as AC-2's coefficient tolerance and as plausible cross-platform drift. A retrain that "passes" within 1e-6 could still select a different training pair, or put different seed-42 pairs in `accept` or `review`. The likely cause is that whole-table percentiles over about 32,000 cells compress the top pairs to nearly 1.0. -> At minimum, the AC-2 full test should also assert that the seed-42 band of every duplicate pair is unchanged after the retrain. The plan should also state this fragility in Risks and docs (AC-6). Better, re-check whether the duplicate features (see 3) give a usable score spread before approval.

3. [major] The duplicate features in AC-1 do not describe what was measured (L-012). The script:
   - fits the duplicate TF-IDF on IA plus ERM texts, while the plan does not say which corpus;
   - takes the percentile over the full symmetric ERM x ERM matrix with the diagonal set to -1, not "within its own table" of 16,110 unordered pairs. The two differ by a bank-dependent affine shift, because the ERM count differs per seed;
   - sets `rank` to the max of the two directions' 1/position. The plan's "1/position of the pair among the row item's candidates" is undefined for an unordered pair.

   An implementer following AC-1 literally builds different features than the ones behind the 12/13 and 13/13 figures. -> Pin all three in AC-1 as measured, or re-measure with the plan's wording. Also say why duplicates drop `shared_entity`/`shared_unit_only` and `taxonomy` and add `same_node`. The epic says "the same features except cross-source ones", and shared entity is not inherently cross-source; ERM's business-unit-wide exposure is presumably the reason.

4. [minor] Other unpinned cross-source definitions in AC-1:
   - `rank`'s "row item" should be named: rows are IA items, candidates are ERM items, as in R1 and the script.
   - `shared_unit_only` is never defined. It should read: the two risks share a business unit of their exposed entities but no exposed entity.
   - Control text is not stated (`title + '. ' + description`, as `risk_text`).
   - `citation` should say: case-insensitive, and 0 when the ERM title has no ':'.

   -> Add one line each.

5. [minor] The threshold rule leaves edge cases open. The script takes the *last* index where cumulative precision is at least 0.95, the global lowest qualifying score, not the first failure while "scanning scores from the top". It falls back to the top score when nothing qualifies, and tied scores at the cut are all admitted by `>=`. -> Pin these behaviours in AC-2 and cover the no-qualifying-score case and ties in the AC-1/AC-2 fixture.

6. [minor] "ERM duplicates | (only 4 auto-accepted, no bar)", while seed 1 measured auto-accepted precision 0.50 (1 of 2 wrong). Under the epic's canonical rule, child c merges auto-accepted duplicate pairs, so one wrong merge in two would be silent, against O3's "not merged silently". -> Keep no bar if the owner agrees, but have the test print it and AC-6's docs state it, and flag it to child c (for example, child c could send duplicate auto-accepts to the queue).

7. [minor] The plan never names the module that holds `pair_features` and `pair_scores` (`features.py`? a `matching.py`, given `test_matching`?). The fingerprint covers only `similarity.py`, `taxonomy_map.py`, `features.py` and `train.py`. If scoring code lives elsewhere, a change to it would not stale the weights. -> Name the module(s), and fingerprint every file the training path imports.

8. [minor] The measurement computes percentiles with `scipy.stats.rankdata`. scipy is pinned in requirements.txt only as a scikit-learn dependency and is not on the approved list. -> Pin the implementation to pandas `rank(method="average")` (approved) or numpy, or get the owner's OK to import scipy directly.

Not checked: the plan's figures on Linux, since my reproduction ran on Windows only. Whether CI time is acceptable for the full-retrain test, which builds seed 7 and computes features and should take about 5-10 s. Goal fit, areas, timebox and INV-6 handling (AC-5, deferring the new wording to child c) all look consistent with the epic.
