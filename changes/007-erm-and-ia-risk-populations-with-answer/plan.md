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
    "docs/data-model.md",
    "akg/**",
    "research/r2-synthetic-text-realism/**"
  ],
  "timebox": "2.5 working days of build time, not counting the owner's cost approval or batch turnaround. Past this, stop and re-plan with `capitan revise` (e.g. split AI text into its own change); never drop criteria silently.",
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
      "then": "every risk is classified by exactly one L3 node of its own source's taxonomy (INV-1, risk part), and is exposed to at least one auditable entity; at full size at least 70% of auditable entities are exposed to at least one risk",
      "test": "generator.test_invariants.InvariantTests.test_ac2_inv1_each_risk_under_one_l3_of_its_source",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the full build has run",
      "then": "child a's answer-key consistency rules (every risk in risk_clusters.csv exactly once, clusters share one ERM L3, true nodes are ERM L3s, cross-source IA risks carry the ERM risk's node), referential integrity (INV-10), data dictionary and name checks (INV-9) all hold, run through the shared helpers in tests/generator/checks.py",
      "test": "generator.test_risks.RiskTests.test_ac3_child_a_answer_key_rules_hold_at_full_size",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the full build has run, with templated text and with AI text",
      "then": "matching risks is realistically hard: exact-text match scores F1 below 0.5; a scikit-learn TF-IDF cosine baseline at its best threshold scores F1 between 0.40 and 0.75; at least 10% of IA risks have a hard negative (a cross-source non-match at or above the median cosine of true matches); and child a's leakage rules hold (matched items share no ID number or sentence, cosine below 0.90, matched median below 0.70, row-order Spearman below 0.8)",
      "test": "generator.test_risks.RiskTests.test_ac4_risk_matching_is_hard_but_possible",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the build runs after this change",
      "then": "sample output is unchanged (`git log main.. -- tests/golden/checksums.sha256` shows no commit and the sample golden test passes); tests/golden/checksums_full.sha256 is regenerated for the new full output",
      "test": "generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and test_ac5_full_build_matches_full_golden",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "`build --size full --text ai` runs",
      "then": "every row of risk_erm.csv and risk_ia.csv takes its description from committed AI text (none falls back to templated); files without full-size AI coverage (controls, issues) stay templated and the build prints which files used AI text; a missing or stale risk entry fails the build naming its key; `--size full` now defaults to `--text ai`. This replaces 006's all-or-nothing guard (AC-9) with per-file coverage",
      "test": "generator.test_risks.RiskTests.test_ac6_full_size_ai_text_covers_risk_files",
      "status": "pending"
    },
    {
      "id": "AC-7",
      "when": "the full-size AI risk text is committed",
      "then": "it passes child a's AI-text rules: no deny-list name, no capitalized word outside the name lists and allow-list, no system its draft lacks; keys are natural (theme, context entity, ordinal), never positional",
      "test": "generator.test_names.NameTests.test_ac4_inv9_names_from_lists_and_no_denied_name_anywhere",
      "status": "pending"
    },
    {
      "id": "AC-8",
      "when": "`write_text --batch --budget <USD>` is asked to generate text whose estimated batch cost (items x measured per-item usage at batch prices) exceeds the budget",
      "then": "it refuses before contacting the API and prints the estimate; with a sufficient budget it submits one Message Batch, and records the actual tokens and cost in research/r2-synthetic-text-realism/cost_log.md",
      "test": "generator.test_ai_text.AiTextTests.test_ac8_batch_refuses_over_budget_without_calling_api",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "c"
}
```

## Why
E2's precision and recall only mean something if the risk populations look like a real bank's: two registers of different size and style, overlapping unevenly, with duplicates, misfiling and near-misses. This change scales risks from 15 per source to the epic's targets and sets the difficulty of the reconciliation problem.

## Data impact
- **Risk themes x context.** The 22 risk concepts become themes (about 45 by the end) with a context slot. A concept instance is a theme applied to one auditable entity ("Fraudulent wire transfers" for Wire Transfer Operations vs Real-Time Payments). ERM and IA write each instance in their own voice. Same theme, different entity is the natural hard negative.
- **Sample unchanged.** Sample mode keeps today's 22 concepts and code path; full size uses the theme library.
- **Answer key.** `risk_clusters.csv` at full size; `taxonomy_map.csv` is b's. Misfiling counts risks under unmapped IA nodes (parked note from 006).
- **Controls at full size** follow risk instances one-to-one with templated text until child d resizes them. Audits and issues stay at sample size (e).
- **Text.** Per-file AI coverage replaces 006's guard. AI text keys become natural keys. Full-size risk text is generated once through the Message Batches API with claude-opus-5-5 (R2 update): measured 2026-11-20 at 971 input and 199 output tokens per item, about $0.0039 per item at batch prices, so about **$1.30 for ~330 risks**. Nothing is submitted until the owner approves that budget (relay rule applies).
- **docs/data-model.md** gains the risk answer-key schema, the misfiling rule, the theme-by-context model and the ratings bands; INV-1's risk part gets its test name.
- New stream for every per-row choice (L-005).

## Test plan
- Done check: `.venv\Scripts\python -m unittest discover -s tests -v`; every named test `ok`.
- Real builds into temp dirs; the batch test never calls the API (refusal happens before any client is made).
- Child a's sample tests keep running unchanged.
- Not tested: E2's matcher (E2), control and issue volumes (d, e).

## Risks
- **Hard-negative rate at full size** (L-003): measure on templated text before writing more themes; tune themes, not thresholds.
- **AI text making matches too easy** (L-002): the AI-variant run of AC-4 catches it; regenerate the guarded way.
- **Content volume** (45 themes): stop at half a day of writing and re-plan if behind.
- **Batch turnaround** (up to 24h): the build and tests use templated text until results arrive.

## Out of scope
- Controls at full size, attribute disagreement (d, parked); audits, issues, planted scenarios, rising-L1 trend, issue text keys (e, parked).
- Making full size the default build (e).

## Relevant lessons
- L-002: AI rules enforced in code and tests (AC-7), one prompt for the whole set.
- L-003: hard negatives measured at full size first (Risks).
- L-005: every per-row choice gets its own stream.
- L-006: sample output is frozen (AC-5); no criterion here needs it to change.

## Slices
1. Theme library and full-size risk populations (templated); AC-1, AC-2.
2. Answer key at full size; difficulty measured and tuned; AC-3, AC-4 (templated).
3. Per-file AI coverage, natural keys, `write_text --batch --budget`; AC-6, AC-8.
4. Owner approves the budget; submit the batch; commit text; AC-4 (AI), AC-7; regenerate full golden; data model; AC-5.
