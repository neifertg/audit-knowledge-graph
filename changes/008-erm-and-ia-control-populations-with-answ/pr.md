# ERM and IA control populations with answer key

Change `008-erm-and-ia-control-populations-with-answ` · objective **O3**: It shows, and measures, the realistic hard part: reconciling ERM's and IA's separate risk taxonomies, risks and controls into one framework (ERM's Basel-style taxonomy). Signal: precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue rather than being merged silently.

## Why
E2 reconciles controls as well as risks, and the epic's shared-system scenario (E3's blast-radius round) lives in control dependencies. Controls reach the epic's targets only with several per risk, written the way each team writes them: ERM's RCSA is brief and leans on generic controls (policies, management review, training), IA's RCM is detailed and specific.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `python -m akg build --size full --seed 42` runs | ERM has 270-330 controls and IA 360-440 (epic targets ±10%); 55-65% of IA controls share a true cluster with an ERM control; no cluster holds two ERM controls; orphan controls (mitigating no risk) are 3-6% of each source's controls, sit in no cluster and have no counterpart in the other source (the build refuses an orphan whose twin exists, so the answer key never labels a true pair unmatched); every matched pair differs in level of detail (the IA description has at least twice the ERM description's words); owners always differ within a matched pair and 15-30% of matched pairs record a different frequency (control type always agrees) | `generator.test_controls.ControlTests.test_ac1_full_control_counts_and_quotas` | pass | PASS |
| AC-2 | either size is built | every non-orphan control mitigates at least one risk of its own source and every risk is mitigated by at least one control (an ERM duplicate shares its original's controls); every control has exactly one owner; at full size answer_key/scenarios.csv lists under `shared_system` the 3 systems whose dependent controls reach the most distinct auditable entities, where reach is the union over both sources of control -> mitigates -> risk -> exposed entity (each source's own links) and ties are broken by system name; each listed system reaches at least 3 entities in at least 2 business units, the third system's reach is strictly greater than the fourth's (no name tie-break decides the list), and the test recomputes the ranking from published files and checks the rows match (d writes these rows; e appends the rest) | `generator.test_controls.ControlTests.test_ac2_control_links_and_shared_system_scenario` | pass | PASS |
| AC-3 | either size is built | child a's answer-key rules (every control in control_clusters.csv exactly once), referential integrity (INV-10), data dictionary, name checks (INV-9), no identical title plus description among one source's controls, and the epic's audit-scope and issue-linking rules all hold, through the shared helpers | `generator.test_controls.ControlTests.test_ac3_shared_rules_hold_at_both_sizes` | pass | PASS |
| AC-4 | the full build has run (templated text) | matching controls is realistically hard: exact-text match and exact owner-plus-frequency match each score F1 below 0.5; a TF-IDF cosine baseline at its best threshold scores F1 between 0.40 and 0.75; at least 10% of IA controls have a hard negative; and child a's leakage rules hold for controls (no shared ID number or sentence, cosine below 0.90, matched median below 0.70, row-order Spearman below 0.8) | `generator.test_controls.ControlTests.test_ac4_control_matching_is_hard_but_possible` | pass | PASS |
| AC-5 | the full build has run | attributes, links and text cues do not give matches away, using only published files and never the answer key: (a) pairing ERM and IA controls equal on type, nature and frequency scores F1 below 0.5; (b) pairing controls whose system sets intersect scores F1 below 0.5 (controls listing no system are never predicted, so their true pairs count as misses); (c) pairing controls required by the same regulation scores F1 below 0.5; (d) for each IA control, the best TF-IDF match among ERM controls that share a system with it, at its best threshold, scores F1 at most 0.80 (IA controls with no candidate predict nothing); (e) the same for ERM controls mitigating a risk exposed to the IA control's business unit, at most 0.80; (f) the entity-mention baseline (ERM controls whose title or description contains a distinctive word of the IA control's entity name, then best TF-IDF) scores at most 0.80. Matching controls through already-matched risks is E2's intended graph strategy, not a leak, and is not capped. (h) a subject-and-kind lookup (pair controls whose titles share every word of a kind label and at least two subject words) scores F1 at most 0.80, because ERM and IA word each theme's subject and each kind label differently; (g) control counts reveal nothing: for each source, the mean number of controls mitigating a risk differs by less than 0.3 between risks that have a cross-source match and risks that do not | `generator.test_controls.ControlTests.test_ac5_attributes_and_systems_do_not_leak_matches` | pass | PASS |
| AC-6 | the build runs after this change | sample output is unchanged (the sample golden test passes; the reviewer runs `git log --oneline main.. -- tests/golden/checksums.sha256` and expects no commits); tests/golden/checksums_full.sha256 is regenerated; 006's full-size AI-text guard stays until child f | `generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and test_ac5_full_build_matches_full_golden; generator.test_full_build.FullBuildTests.test_ac9_full_size_explicit_ai_text_fails_loudly` | pass | PASS |
| AC-7 | child c's difficulty measures run | the stale-link measure counts only links to another business unit of the same segment (links to another segment fail the test), and the entity-mention baseline searches ERM titles as well as descriptions; child c's AC-5 bands still hold (parked findings from 007's review) | `generator.test_risks.RiskTests.test_ac5_exposure_structure_does_not_leak_matches` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/generator/****: `src/features/generator/generate.py`, `src/features/generator/library.py`
3. **Tests**: `tests/generator/checks.py`, `tests/generator/difficulty.py`, `tests/generator/test_controls.py`, `tests/generator/test_risks.py`, `tests/golden/checksums_full.sha256`

## Data impact
- **Control instances.** Each risk instance gets its theme's specific control in each source that holds it. Generic controls come from a small library of kinds (policy and procedures, management review, exception reporting, reconciliation, segregation of duties, training, access restriction, key risk indicator); ERM and IA word every kind separately.
- **ERM generic controls are bank-wide, per theme** (about 2 kinds per theme, roughly 119 controls): "Wire transfer policy and procedures" mitigates every ERM risk of that theme. Their text names the theme's subject only, so (theme, kind) is unique.
- **IA generic controls are per risk instance** (about 1.5 per IA risk): IA picks each kind from ERM's kinds for that theme with a set probability (IA tests the enterprise policy) and otherwise from the general skewed mix. That probability is the dial for the 55-65% overlap: set to 0.6 (mid-band; the critique's simulation gives a 58-64% range), recorded in docs/data-model.md, measured first at the checkpoint. IA text names its audit area (the entity), so every IA control is unique.
- **Matching truth.** Specific controls match when both sources hold the risk instance. A cluster for a generic control is one ERM control (theme, kind) plus every IA control of the same theme and kind; no cluster holds two ERM controls. Generic controls across themes are the natural hard negatives. An ERM duplicate risk shares its original's controls. Counts per risk come from per-theme and per-instance draws that never look at the other source, so they reveal no match (AC-5 g).
- **Attributes.** Owners always differ within a matched pair; IA records a different frequency for 15-30% of matched pairs (parked from 005's review); control type always agrees. ERM lists systems for only some controls (RCSAs rarely name systems).
- **Orphans.** 3-6% of each source's controls mitigate no risk. An orphan is only ever a control with no counterpart in the other source: a specific control for an instance neither source holds, or a generic control whose theme and kind the other source never uses. The generator refuses to build if an orphan has a twin, so the answer key stays truthful; orphans sit in no cluster.
- **Separate wording.** Each theme has an ERM subject phrase and an IA subject phrase ("outgoing wire transfers" vs "wire release"), and each control kind an ERM label and an IA label, so titles alone do not pair generic controls (AC-5 h).
- **System dependencies.** Only specific controls and the reconciliation and access-restriction kinds depend on systems; policies, training, management review, exception reporting, segregation of duties and key risk indicators do not.
- **Shared systems (scenario).** Reach is the union over both sources of control -> mitigates -> risk -> exposed entity (each source's own links), ties broken by system name. d writes the top 3 systems as `shared_system` rows in `answer_key/scenarios.csv`; e appends its scenarios (parked decision, now made).
- **Context in text.** Each control's text carries its instance context (ERM business terms, IA audit area), so no two controls of one source are identical (AC-3).
- **Sample unchanged**: sample mode keeps today's one control per concept. Audits and issues stay at sample size (e) and keep the epic's linking rules.
- **docs/data-model.md** gains the control model, the generic library, the attribute and system rules, and the scenarios.csv split.
- Every per-row choice draws from its own stream (L-005).

## Risks
- **Generic controls too uniform**: TF-IDF may fall below 0.40 if generic wording swamps the specific signal. Measured at the checkpoint; tune wording, never the band (L-007).
- **Volume**: ~700 controls make the leakage checks slower; keep helpers linear or sorted.
- **Theme subject phrases** (56 short noun phrases) are new content; written first.

## Deliberately not in this PR
- Full-size AI text (f); audits, issues, other planted scenarios, issue text keys (e); within-ERM control duplicates (the epic defines duplicates for risks only).

Parked for later:
- 2026-11-20 E1 child e: assert at least one ERM duplicate group exists at full size in 008's shared-controls check, and assert every control frequency is in library.FREQUENCIES (008 review suggestions) (from 008-erm-and-ia-control-populations-with-answ)

## Lessons recorded
- L-008 Any exact shared phrase becomes a lookup key; measure it

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `f4e7596499924337`
- Size: 7 code files, +803 / -80 lines
