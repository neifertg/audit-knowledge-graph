VERDICT: READY

Reproduction: I rebuilt seeds 7 (templated), 42 (AI) and 1 (templated) and reran the new pre-plan script (`e2b_v2.py`, TAIL=1, balanced weighting). Every figure in AC-3, AC-4 and the evidence table came out the same: seed 42 risks 38 accepted (0.95), queue 122, 2 of 103 missed; controls 68 (1.00), 341, 5 missed; duplicates 3 + 11 = 14 queued, 1 of 13 missed. Seed 1 risks 42 (0.93), 131, 0 missed; controls 95 (0.98), 318, 2 missed; duplicates 1 + 14 = 15 queued, 0 missed. All three fits converged well under `max_iter`.

The revision answers the previous critique:
- #1: `tol=1e-10` is pinned and the figures were re-measured.
- #2: tail scores fix the saturation. The seed-7 top-20 duplicate scores now span 0.965-1.000, not 1e-5. The full AC-2 test now checks the band of every seed-42 pair.
- #3 and #4: the duplicate corpus, the 16,110-pair table, the max-of-directions rank, the reason for the dropped features, the `shared_unit_only` and `citation` definitions, the text and the row/candidate roles are all pinned. They match the script.
- #6: duplicates are now review-only.
- #7: the modules are named, and `match.py` is fingerprinted.
- #8: numpy only, no scipy.

Review-only duplicates fit the epic's contract. The canonical rule's clause about an "auto-accepted within-ERM duplicate pair" simply never fires: an IA risk that clears auto-accept against both members of a duplicate pair merges its best edge and queues the other. INV-3 ("nothing below the confidence threshold is merged silently") is served better than before. The remaining issues are minor.

1. [minor] L-007 says to use one sorted sweep for the thresholds, because "the naive loop timed out at 27,000 pairs". The plan says only "at tie-group boundaries" and "Training runs in seconds". The measured script's `thresholds()` re-scans the whole score array once per unique score. On seed 7 that took about 70 s of a 73 s training run, mostly on 118,105 control pairs. Features and all three fits took under 3 s together. Copied as-is, it would make the full AC-2 test slow in CI. -> In AC-2, pin a single sorted sweep (cumulative true and total counts over descending tie groups), and in the Test plan state the full retrain's measured time, which the epic requires ("child b states its measured time").

2. [minor] The previous critique's #5 asked for a fixture covering the threshold edge cases. AC-1's fixture covers tail-score ties, rank, `shared_unit_only`, taxonomy and citation, but not the threshold rule. AC-2's tests only compare the committed and retrained results. A wrong rule could slip through:
   - first failure instead of the lowest qualifying score;
   - ties split at the cut;
   - no qualifying score not giving "none";
   - the floor not capped at auto-accept.

   Both the committed file and the retrain would carry the same bug, so the currency test still passes. -> Add a small hand-built scores/labels fixture to the AC-2 test that covers those four cases.

3. [minor] The duplicate floor's cap is ambiguous. The plan says "*review floor:* ... capped at the auto-accept threshold", and duplicates have "no auto-accept". It does not say whether the duplicate floor is capped at the notional auto-accept threshold or left uncapped. On seed 7 it makes no difference: the floor is 0.9922 and the notional threshold 0.99999. On another training bank it could. -> State that the duplicate floor is uncapped (and that the notional threshold is neither computed nor stored). The 8e-3 "gap to notional auto-accept" sentence in the evidence can then go, since that threshold no longer exists.

4. [minor] The tail score's scaling is described loosely: "percentile `p` ... (average rank of ties, scaled 0-1)". The measured code uses the 0-based average rank divided by (n - 1). Other readings, such as (rank + 1) / n, shift every value, and could move a threshold's training pair. -> Write the formula exactly in AC-1: p = (0-based average rank) / (n - 1). The fixture test then pins it.

5. [minor] AC-2 says "measured: 29-71 iterations". On this machine the pinned script took 46 (risks), 31 (duplicates) and 48 (controls). The 29-71 range may come from an earlier variant. -> Quote the build's own counts per model in the docs (L-012), or drop the number. Convergence (`n_iter_ < max_iter`) is what matters, and the test could assert it.

6. [minor] Review-only duplicates move away from the epic's "trained the same way" for duplicates: the epic gives every model an auto-accept threshold. The move is conservative and fits O3. It is stated only in the plan's Risks and in AC-6's docs. -> At approval, the owner should acknowledge it explicitly as an amendment to the epic's threshold rule, so child c's plan and child d's reporting ("auto-accepted, queued and missed" per kind) treat duplicates as queue-only without a revision dispute.

Not checked:
- The figures on Linux and in CI; my run was on Windows only. The AC-2 band check is the right guard. Around each threshold, the neighbouring training scores are 2e-7 to 1e-2 apart in probability, which is large in logit terms near p = 1.
- Whether the refactor of `similarity.py` to expose separate word and character cosines stays inside 011's existing tests. It is in the plan's areas.
