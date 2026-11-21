# Three years of audits and issues with planted scenarios

```json plan
{
  "id": "009-three-years-of-audits-and-issues-with-pl",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-20",
  "objective": "O3",
  "areas": [
    "src/features/generator/**",
    "tests/**",
    "docs/data-model.md",
    "akg/**",
    "research/r2-synthetic-text-realism/sample_pack.md"
  ],
  "timebox": "2.5 working days of build time (half a day over the epic's ~2 per child, absorbed within the epic's 11-day total). Checkpoint after 2 hours: full-size audits and issues generated and the AC-1 mix and AC-4 scenario measures computed, or re-plan. Past the timebox, stop and re-plan with `capitan revise`; never drop criteria silently.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m akg build --seed 42` runs with no size flag",
      "then": "it builds full size (full size is now the default; `--size sample` builds the sample) with 68-82 audits, at least 20 in each of 2023, 2024 and 2025, and 225-275 issues: IA 40-60%, regulator 10-20%, self-identified 10-20%, 2nd line 10-20%; issue ratings High 15-35%, Medium 40-60%, Low 15-35%; 40-70% of issues opened before 2025-07-01 are closed",
      "test": "generator.test_issues.IssueTests.test_ac1_full_audit_and_issue_mix",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "either size is built",
      "then": "INV-4 holds (every IA issue links to exactly one audit; every issue links to at least one control or risk and has exactly one owner and one source) and INV-5 holds (closure never before opening; audits start and end inside 2023-01-01..2025-12-31; an issue never opens before the end of the audit that raised it)",
      "test": "generator.test_invariants.InvariantTests.test_ac2_inv4_inv5_issue_links_and_dates",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the full build has run",
      "then": "the audit plan reads as risk-based: every audit covers 1-3 auditable entities and tests only IA controls mitigating risks those entities are exposed to (epic rule); entities with at least one High IA risk average more audits than entities without; 10-25% of auditable entities are never audited in the window (a coverage gap); IA issues link only to controls their audit tested and risks those controls mitigate, other issues to ERM controls and risks (epic rule, via the shared helper)",
      "test": "generator.test_issues.IssueTests.test_ac3_audit_plan_is_risk_based",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the full build has run",
      "then": "the planted scenarios exist and answer_key/scenarios.csv lists them, each recomputed by the test from published files: (a) `repeat_finding:<n>` for at least 5 groups, each 2-4 IA issues against the same IA control in at least 2 different years with pairwise different titles; (b) `untested_high_risk` for at least 8 High-rated IA risks none of whose IA controls any audit tested; (c) `rising_category` naming one ERM L1 node whose issue count (each issue's ERM L1 taken from the answer key's true ERM node of its first linked risk, by sorted risk ID) rises at least 50% from 2023 to 2025 while total issues change less than 15%; (d) every regulation reaches at least one business unit through requires -> control -> mitigates -> risk -> exposed entity -> owning unit (checked, not listed)",
      "test": "generator.test_issues.IssueTests.test_ac4_planted_scenarios_are_present_and_listed",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the full build has run",
      "then": "every entity and every relationship type in the ER diagram has at least one row (the epic's final completeness check), and at least one ERM duplicate risk group exists so 008's shared-controls check exercises data; every control frequency is one of library.FREQUENCIES (parked from 008's review)",
      "test": "generator.test_issues.IssueTests.test_ac5_every_entity_and_relationship_is_populated",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "AI issue text is looked up",
      "then": "issue text keys are natural (source, control instance key, ordinal among that source's issues against that control), never positional; the 15 committed sample issue texts are re-keyed and re-hashed by script with their text unchanged and no API call, so `--text ai` at sample size still builds, check-text finds no orphans, and the sample golden is unchanged",
      "test": "generator.test_ai_text.AiTextTests.test_ac6_missing_stale_or_orphan_ai_text_fails and generator.test_issues.IssueTests.test_ac6_issue_text_keys_are_natural",
      "status": "pending"
    },
    {
      "id": "AC-7",
      "when": "the full build runs with `--count PERSON=100` instead of the full default",
      "then": "every file whose name contains no `person` is byte-identical to the default full build (issue owners and every other per-row choice at full size draw from their own streams; the sample keeps its frozen draws), closing 006's parked PERSON clause",
      "test": "generator.test_issues.IssueTests.test_ac7_person_count_leaves_other_files_unchanged",
      "status": "pending"
    },
    {
      "id": "AC-8",
      "when": "the build runs after this change",
      "then": "sample output is unchanged (the sample golden test passes with an explicit `--size sample`; the reviewer runs `git log --oneline main.. -- tests/golden/checksums.sha256` and expects no commits); tests/golden/checksums_full.sha256 is regenerated; the committed sample pack is regenerated so its name lists are current, with every data row unchanged; 006's full-size AI-text guard stays until child f",
      "test": "generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and test_ac5_full_build_matches_full_golden; generator.test_sample_pack.SamplePackTests.test_ac8_committed_pack_is_current",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "e"
}
```

## Why
The milestone's story rests on what audits and issues reveal: repeat findings filed under different names, high risks never tested, and a category whose issues are rising. E3's rounds query exactly these, and the page shows them. This change scales audits and issues to three years at full size, plants the scenarios on purpose and records them, and makes full size the default build.

## Data impact
- **Audit plan (full size).** About 75 audits, 25 per year, each covering 1-3 auditable entities and testing the IA controls (specific and generic) of the risks those entities are exposed to. Entities with High IA risks are sampled more often; 10-25% of entities go unaudited (a coverage gap, realistic and useful for E3 round 2).
- **Issues (full size).** About 250 from four sources. IA issues come from audits and link to a tested control and the risk it mitigates; regulator (MRA/MRIA), self-identified and 2nd-line issues link to ERM controls and risks. Titles come from several templates per source so repeat findings read differently.
- **Planted scenarios** written to `answer_key/scenarios.csv` after d's `shared_system` rows: `repeat_finding:<n>` (issue IDs), `untested_high_risk` (risk IDs), `rising_category` (one ERM L1 node ID). The rising trend is defined through the answer key's true ERM node (parked note), so ERM and IA issues count in one taxonomy, matching E3 round 7.
- **Stale coverage** (for E3 round 2): a control is stale when never tested in the window, or last tested more than 24 months before window end. Recorded in docs/data-model.md.
- **Streams.** At full size every per-row choice (audit scope, tested controls, issue source, owner, dates) draws from its own stream (L-005), so `--count PERSON` touches only person files (AC-7). Sample keeps its existing draws and output.
- **Text keys.** Issue AI-text keys become natural; the sample's 15 committed texts are re-keyed by a one-off script (text unchanged). Full-size issue text stays templated until child f.
- **Default size.** `python -m akg build` now builds full size; tests that mean sample pass `--size sample` explicitly.
- **docs/data-model.md**: INV-4 and INV-5 get test names; audit plan, issue sources, scenarios and stale coverage are documented.

## Test plan
- Done check: `.venv\Scripts\python -m unittest discover -s tests -v`; every named test `ok`.
- Real builds into temp dirs; scenarios recomputed from published files, never trusted from scenarios.csv alone.
- Not tested: full-size AI text (f); SQLite/Neo4j loading (E3).

## Risks
- **Planting distorts the mix** (e.g. forcing repeat findings skews IA share or ratings): measured at the checkpoint with AC-1 and AC-4 together.
- **Rising trend vs. stable total** may need explicit year allocation of issues by L1; allocate from an own stream, not by post-hoc deletion.
- **Default size flip** touches many tests' expectations: make the sample explicit in helpers first, then flip.

## Out of scope
- Full-size AI text and removing the guard (f); E3's query wording for stale coverage (parked for E3); sample-mode PERSON independence (sample stays frozen).

## Relevant lessons
- L-005: own streams for every per-row choice at full size (AC-7).
- L-006: sample output frozen (AC-8); AC-7 applies at full size only, so no criterion needs sample output to change.
- L-007: measure at the checkpoint; tune allocation, not bands.
- L-008: no new shared text vocabulary across sources here; issues are not cross-source matched.

## Slices
1. Make sample explicit in test helpers; flip the default to full; natural issue keys and the sample re-key script; AC-6.
2. Full-size audit plan and issues on own streams; AC-1, AC-2, AC-3, AC-7.
3. Planted scenarios and scenarios.csv rows; completeness check; AC-4, AC-5.
4. Full golden, sample pack refresh, data model; AC-8.
