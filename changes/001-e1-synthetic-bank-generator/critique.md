VERDICT: READY
1. [minor] The epic's areas don't match what f used. **Areas.** says "Every child: `src/features/generator/**`, `tests/**`, `docs/data-model.md`. a also: `akg/**`, `requirements.txt`, `.gitattributes`, `research/r2-synthetic-text-realism/**`." But 010's approved plan also claims `akg/**` and `research/r2-synthetic-text-realism/**`, and f did write `cost_log.md` there, which the epic's own f budget bullet requires. As written, the epic implies f went outside its areas, when the child plan in fact claimed them. -> Add "f also: `akg/**`, `research/r2-synthetic-text-realism/**`".
2. [minor] One percentage in the budget bullet is slightly off. "they came out 15-27% low on the small duplicate batches": in cost_log.md the three 13-item batches cost $0.0773, $0.0730 and $0.0813 against an estimate of $0.0639 each, so actual cost was 14-27% above the estimate. The second batch, at 14%, falls below the stated lower bound. This doesn't change any decision. -> "14-27%", or "actual cost exceeded the estimate by up to 27%".
3. [minor] **Determinism (INV-7)** still says text is "committed with a hash of the item's template inputs". The new **Staleness (INV-7)** bullet in the revision gives the full-size truth: the prompt version is part of the hash, and duplicates also carry their original's text hash and note hash. A reader of the original paragraph won't see that. -> Add a forward pointer ("at full size, see Staleness below"). This is optional, since the revision section already states it clearly.

All seven items from the previous critique are resolved:
- (1) The leakage paragraph now states the separate bands: risks 0.40-0.75 and controls 0.25-0.75, with a note that the control floor was lowered. This matches test_controls.py:138 and test_risks.py:54.
- (2) The three duplicate attempts are recorded: the close-copy note scored 0.93, the looser note 0.16, and the owner's middle note 0.60. Commit c9eec09 gives 0.929 against the 0.80 ceiling, 4405ecc gives 0.157, 94fdfaf gives 0.600, and L-010 matches.
- (3) The cost bullet now describes all eight batches as three repeat attempts at the same 13 items plus resubmissions, totalling $5.26. The budget bullet now says it uses fixed R2 figures that came out low.
- (4) The opening of the revision now separates the two band decisions from the rule calibration and the measured finding.
- (5) The per-item checks now include the issue openings and the 900-token retry cap.
- (6) Staleness is recorded in the revision.
- (7) The lessons list now includes L-002, L-007, L-008, L-010 and L-011, and L-010 and L-011 both exist in LESSONS.md.

Checked against what was built:
- tests/golden/cue_figures.json: control TF-IDF 0.2819 against chance 0.0041; risk 0.4715; duplicate 0.60 with median cosine 0.5568 against 0.3073 (margin 0.25, test minimum 0.15, test_risks.py:59); repeat-finding recall and precision 0.0; citation cues 0.45, 0.64 and 0.74.
- The duplicate floor is still 0.30 and the ceiling 0.80 (test_risks.py:56).
- The data-model.md notes for full-size AI text and AI-text difficulty, including the one hand edit, agree with the epic's revision.
- 010 plan AC-3 and AC-5 match the recorded decisions.

Not checked: whether the owner's chat-only decisions were worded exactly as recorded (I checked only their traces in the repo); the Neo4j-dependent tests; whether the full test suite passes now (I did not run it).
