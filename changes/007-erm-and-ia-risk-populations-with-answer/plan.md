# ERM and IA risk populations with answer key

```json plan
{
  "id": "007-erm-and-ia-risk-populations-with-answer",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-20",
  "objective": "O3",
  "areas": [
    "src/features/generator/**",
    "tests/**",
    "docs/data-model.md"
  ],
  "timebox": "2.5 working days of build time (half a day over the epic's ~2 per child, absorbed within the epic's 11-day total; noted here). Checkpoint after 2 hours: at least 10 themes written and the same-business-unit near-miss share measured, or re-plan. Past the timebox, stop and re-plan with `capitan revise`; never drop criteria silently.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m akg build --size full --seed 42` runs",
      "then": "ERM has 162-198 risks and IA 135-165 (epic targets ±10%); 55-65% of IA risks share a true cluster with an ERM risk; within-ERM duplicates are 5-10% of ERM risks; 10-20% of IA risks are misfiled (true ERM node not under their IA node's mapped target, counting risks under unmapped IA nodes); inherent ratings fall within High 15-35%, Medium 40-60%, Low 15-35% per source",
      "test": "generator.test_risks.RiskTests.test_ac1_full_risk_counts_and_quotas",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "either size is built",
      "then": "every risk is classified by exactly one L3 node of its own source's taxonomy (INV-1, risk part) and is exposed to at least one auditable entity; at full size IA risks are exposed across at least 60% of auditable entities and ERM risks across at least 70%",
      "test": "generator.test_invariants.InvariantTests.test_ac2_inv1_each_risk_under_one_l3_of_its_source",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the full build has run",
      "then": "child a's size-independent answer-key rules (every risk in risk_clusters.csv exactly once, clusters share one ERM L3, true nodes are ERM L3s, cross-source IA risks carry the ERM risk's node), moved from test_answer_key into a shared helper in tests/generator/checks.py that a's test also calls, plus referential integrity (INV-10), data dictionary and name checks (INV-9), all hold at full size; and, at both sizes: no two risks of one source share an identical title plus description (the context entity appears in both sources' text), every control an audit tests mitigates a risk that one of its covered entities is exposed to, IA issues link only to controls their audit tested and risks those controls mitigate, and other issues link to ERM controls and risks",
      "test": "generator.test_risks.RiskTests.test_ac3_child_a_answer_key_rules_hold_at_full_size",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the full build has run (templated text, the full-size default until child f)",
      "then": "matching risks is realistically hard: exact-text match scores F1 below 0.5; a scikit-learn TF-IDF cosine baseline at its best threshold scores F1 between 0.40 and 0.75; at least 10% of IA risks have a hard negative (a cross-source non-match at or above the median cosine of true matches); child a's leakage rules hold for risks and controls (no shared ID number or sentence, cosine below 0.90, matched median below 0.70, row-order Spearman below 0.8, matched controls never equal on all of owner, frequency and type)",
      "test": "generator.test_risks.RiskTests.test_ac4_risk_matching_is_hard_but_possible",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the full build has run",
      "then": "structure does not give matches away, using only published files (never the answer key): (a) an exposure baseline that pairs an ERM and an IA risk whenever the IA risk's auditable entity is among the ERM risk's exposed entities scores F1 below 0.5; (b) a combined baseline that, for each IA risk, ranks the ERM risks exposed to any entity in the IA risk's business unit by TF-IDF cosine and keeps the best one above a threshold, scores F1 at most 0.80 at the threshold that maximizes its own F1; (c) of the IA risks that have at least one hard negative, at least 20% have one sharing their business unit; (d) 10-20% of ERM exposure links point to an entity in a different business unit of the same segment (stale links)",
      "test": "generator.test_risks.RiskTests.test_ac5_exposure_structure_does_not_leak_matches",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "the build runs after this change",
      "then": "sample output is unchanged (`git log main.. -- tests/golden/checksums.sha256` shows no commit, and the sample golden test passes); tests/golden/checksums_full.sha256 is regenerated for the new full output; 006's full-size AI-text guard (AC-9) stays in place until child f; 006's test_ac1 assertion that risks and controls stay at sample size at full size is narrowed to audits and issues, with a note (an intended change, not a regression)",
      "test": "generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and test_ac5_full_build_matches_full_golden; generator.test_full_build.FullBuildTests.test_ac9_full_size_explicit_ai_text_fails_loudly; the reviewer also runs `git log --oneline main.. -- tests/golden/checksums.sha256` (no commits expected)",
      "status": "pending"
    },
    {
      "id": "AC-7",
      "when": "`python -m akg sample-pack --size full` runs",
      "then": "the pack's introduction describes the full-size bank (no '~15 rows' wording) and, when no AI text is shown, drops the text-choice prompt and the AI column instead of showing '(not generated)'",
      "test": "generator.test_sample_pack.SamplePackTests.test_ac7_full_size_pack_describes_full_size",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "c"
}
```

## Why
E2's precision and recall only mean something if the risk populations look like a real bank's: two registers of different size and style, overlapping unevenly, with duplicates, misfiling and near-misses, and no structural shortcut to the answer. This change scales risks from 15 per source to the epic's targets and sets the difficulty of the reconciliation problem.

## Data impact
- **Risk themes x context.** The 22 risk concepts become themes (about 45) with a context slot. A concept instance is a theme applied to one auditable entity ("Fraudulent wire transfers" for Wire Transfer Operations vs Real-Time Payments). ERM and IA write each instance in their own voice; same theme, different entity is the natural hard negative.
- **Exposure differs by source (AC-5).** IA links a risk to its specific auditable entity. ERM links at business-unit breadth (every entity in the owning business unit), and 10-20% of ERM links point to an entity in another business unit of the same segment, as a stale register would.
- **Where same-theme risks sit.** A theme's instances are placed on entities of as few business units as the organization allows, multi-entity units first (wire and real-time payments both under Payment Operations), so some near-misses survive a business-unit filter (AC-5 b, c). Most units have 1-2 entities, so the same-unit share is measured at the checkpoint before more themes are written.
- **Context in the text.** Each instance names its entity's context in both sources' wording, so two instances of one theme never produce identical rows (AC-3).
- **Audits and issues at full size** keep sample counts but draw from the full-size risk and control instances, with the epic's linking rules intact (IA issues link only to controls their audit tested).
- **Sample unchanged.** Sample mode keeps today's 22 concepts and code path; full size uses the theme library. 006's taxonomies have 50 ERM L3 nodes for about 45 themes; a theme may add an L3 node only through this plan's data-model update.
- **Answer key.** `risk_clusters.csv` at full size; `taxonomy_map.csv` is b's. Misfiling counts risks under unmapped IA nodes (parked note from 006).
- **Controls at full size** follow risk instances one-to-one, templated, with owners always differing between matched ERM and IA controls, until child d resizes them. Audits and issues stay at sample size (e).
- **Text.** Templated at full size. All full-size AI text moves to child f (epic revision 1); nothing here calls an API.
- **docs/data-model.md** gains the risk answer-key schema, the misfiling rule, the theme-by-context model, ERM vs IA exposure, and the ratings bands; INV-1's risk part gets its test name.
- Every per-row choice draws from its own stream (L-005).

## Test plan
- Done check: `.venv\Scripts\python -m unittest discover -s tests -v`; every named test `ok`.
- Real builds into temp dirs; child a's sample tests keep running unchanged.
- Not tested: E2's matcher (E2), control and issue volumes (d, e), AI text at full size (f).

## Risks
- **Hard-negative rate at full size** (L-003): measured on templated text after slice 1, before writing the remaining themes; tune themes, not thresholds.
- **Content volume**: the 2-hour checkpoint in the timebox.
- **The TF-IDF band at full size** may conflict with the hard-negative rate; if so, report the measurements and re-plan rather than loosen a band silently.

## Out of scope
- Full-size AI text (child f); controls at full size and attribute disagreement beyond owners (d, parked); audits, issues, planted scenarios, rising-L1 trend, issue text keys (e, parked); full size as the default build (e).

## Relevant lessons
- L-003: hard negatives measured at full size first (Risks).
- L-005: every per-row choice gets its own stream.
- L-006: sample output is frozen (AC-6); no criterion here needs it to change.
- L-002: no AI text here; child f carries the guards.

## Slices
1. Theme library (first 10 themes) and full-size populations with source-specific exposure; measure difficulty; AC-1, AC-2, AC-5.
2. Remaining themes; answer key at full size; tune difficulty; AC-3, AC-4.
3. Full-size pack wording, full golden, data model; AC-6, AC-7.
