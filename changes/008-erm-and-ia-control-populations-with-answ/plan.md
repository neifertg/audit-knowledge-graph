# ERM and IA control populations with answer key

```json plan
{
  "id": "008-erm-and-ia-control-populations-with-answ",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-20",
  "objective": "O3",
  "areas": [
    "src/features/generator/**",
    "tests/**",
    "docs/data-model.md"
  ],
  "timebox": "2.5 working days of build time (half a day over the epic's ~2 per child, absorbed within the epic's 11-day total). Checkpoint after 2 hours: the generic control library written and every AC-1, AC-4 and AC-5 measure computed on the full build, or re-plan. Past the timebox, stop and re-plan with `capitan revise`; never drop criteria silently.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m akg build --size full --seed 42` runs",
      "then": "ERM has 270-330 controls and IA 360-440 (epic targets ±10%); 55-65% of IA controls share a true cluster with an ERM control; orphan controls (mitigating no risk) are 3-6% of each source's controls; every matched pair differs in level of detail (the IA description has at least twice the ERM description's words); no matched pair is equal on all of owner, frequency and type, and at least 15% of matched pairs disagree on frequency or type",
      "test": "generator.test_controls.ControlTests.test_ac1_full_control_counts_and_quotas",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "either size is built",
      "then": "every non-orphan control mitigates at least one risk of its own source and every risk is mitigated by at least one control; every control has exactly one owner; at full size at least 3 systems are depended on by controls of 3 or more auditable entities (the shared-system scenario), and answer_key/scenarios.csv lists those systems under `shared_system` (d writes these rows; e appends the rest)",
      "test": "generator.test_controls.ControlTests.test_ac2_control_links_and_shared_system_scenario",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "either size is built",
      "then": "child a's answer-key rules (every control in control_clusters.csv exactly once), referential integrity (INV-10), data dictionary, name checks (INV-9), no identical title plus description among one source's controls, and the epic's audit-scope and issue-linking rules all hold, through the shared helpers",
      "test": "generator.test_controls.ControlTests.test_ac3_shared_rules_hold_at_both_sizes",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the full build has run (templated text)",
      "then": "matching controls is realistically hard: exact-text match and exact owner-plus-frequency match each score F1 below 0.5; a TF-IDF cosine baseline at its best threshold scores F1 between 0.40 and 0.75; at least 10% of IA controls have a hard negative; and child a's leakage rules hold for controls (no shared ID number or sentence, cosine below 0.90, matched median below 0.70, row-order Spearman below 0.8)",
      "test": "generator.test_controls.ControlTests.test_ac4_control_matching_is_hard_but_possible",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the full build has run",
      "then": "attributes and links do not give matches away, using only published files: (a) pairing ERM and IA controls with the same type, nature and frequency scores F1 below 0.5; (b) pairing controls that depend on the same set of systems scores F1 below 0.5; (c) for each IA control, taking the best TF-IDF match among ERM controls that share a system, at its best threshold, scores F1 at most 0.80. Matching controls through already-matched risks is the intended graph strategy for E2, not a leak, and is not capped",
      "test": "generator.test_controls.ControlTests.test_ac5_attributes_and_systems_do_not_leak_matches",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "the build runs after this change",
      "then": "sample output is unchanged (the sample golden test passes; the reviewer runs `git log --oneline main.. -- tests/golden/checksums.sha256` and expects no commits); tests/golden/checksums_full.sha256 is regenerated; 006's full-size AI-text guard stays until child f",
      "test": "generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and test_ac5_full_build_matches_full_golden; generator.test_full_build.FullBuildTests.test_ac9_full_size_explicit_ai_text_fails_loudly",
      "status": "pending"
    },
    {
      "id": "AC-7",
      "when": "child c's difficulty measures run",
      "then": "the stale-link measure counts only links to another business unit of the same segment (links to another segment fail the test), and the entity-mention baseline searches ERM titles as well as descriptions; child c's AC-5 bands still hold (parked findings from 007's review)",
      "test": "generator.test_risks.RiskTests.test_ac5_exposure_structure_does_not_leak_matches",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "d"
}
```

## Why
E2 reconciles controls as well as risks, and the epic's shared-system scenario (E3's blast-radius round) lives in control dependencies. Controls reach the epic's targets only with several per risk, written the way each team writes them: ERM's RCSA is brief and leans on generic controls (policies, management review, training), IA's RCM is detailed and specific.

## Data impact
- **Control instances.** Each risk instance gets its theme's specific control plus generic controls drawn from a small library (policy and procedures, management review, reconciliation, segregation of duties, training, exception reporting, system access restriction, key risk indicator), each worded with the theme's subject ("outgoing wire transfers") and the instance's context. A control instance is (risk instance, control kind). ERM keeps about 1.6 per risk, IA about 2.6, so IA documents controls ERM never lists.
- **Matching truth.** A control cluster is the same (risk instance, control kind) in both sources. Generic controls across themes are the natural hard negatives.
- **Attributes.** Matched pairs disagree realistically: owners always differ (as now), and IA records a different frequency or type for some pairs (parked from 005's review). ERM lists systems for only some controls (RCSAs rarely name systems), so system overlap is not a shortcut (AC-5 b).
- **Orphans.** 3-6% of each source's controls mitigate no risk (controls written for instances that source does not hold).
- **Shared systems (scenario).** d writes `shared_system` rows to `answer_key/scenarios.csv`; e appends its scenarios (parked decision, now made).
- **Context in text.** Each control's text carries its instance context (ERM business terms, IA audit area), so no two controls of one source are identical (AC-3).
- **Sample unchanged**: sample mode keeps today's one control per concept. Audits and issues stay at sample size (e) and keep the epic's linking rules.
- **docs/data-model.md** gains the control model, the generic library, the attribute and system rules, and the scenarios.csv split.
- Every per-row choice draws from its own stream (L-005).

## Test plan
- Done check: `.venv\Scripts\python -m unittest discover -s tests -v`; every named test `ok`.
- Difficulty measures for controls live beside child c's in `tests/generator/difficulty.py`, one sorted sweep per best-threshold F1 (L-007).
- Not tested: E2's matcher; audits and issues at full size (e); AI text at full size (f).

## Risks
- **Generic controls too uniform**: TF-IDF may fall below 0.40 if generic wording swamps the specific signal. Measured at the checkpoint; tune wording, never the band (L-007).
- **Volume**: ~700 controls make the leakage checks slower; keep helpers linear or sorted.
- **Theme subject phrases** (56 short noun phrases) are new content; written first.

## Out of scope
- Full-size AI text (f); audits, issues, other planted scenarios, issue text keys (e); within-ERM control duplicates (the epic defines duplicates for risks only).

## Relevant lessons
- L-002: no AI text here.
- L-005: every per-row choice gets its own stream.
- L-006: sample output frozen (AC-6); no criterion here needs it to change.
- L-007: difficulty measured at the checkpoint; content tuned, not bands.

## Slices
1. Theme subjects, generic control library, control instances and attributes; measure at the checkpoint; AC-1, AC-4, AC-5.
2. Links (mitigates, depends_on, requires, owned_by), orphans, shared-system scenario rows; AC-2, AC-3.
3. 007 test tightenings, full golden, data model; AC-6, AC-7.
