# Full-size AI text in one batch

```json plan
{
  "id": "010-full-size-ai-text-in-one-batch",
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
  "timebox": "1 working day of build time (the epic's figure), not counting batch turnaround (up to 24 hours) or owner decisions. Past this, stop and re-plan with `capitan revise`; never drop criteria silently.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`write_text --size full --batch --budget <USD>` is asked to generate text whose estimated cost exceeds the budget",
      "then": "it refuses before creating any API client and prints the estimate (items x measured per-item usage at batch prices, doubled to cover one resubmission); with a sufficient budget it submits one Message Batch, records the batch ID, and on collection logs actual tokens and cost to research/r2-synthetic-text-realism/cost_log.md",
      "test": "generator.test_batch.BatchTests.test_ac1_over_budget_refused_before_any_client",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "batch results are collected (offline test: a recorded fake batch result file, no network)",
      "then": "each request's custom ID is a hash of its internal key (unique, matching the API's allowed characters and length), results are matched to items by custom ID, never by order (the fake file is shuffled), and an unknown or missing custom ID is reported by name",
      "test": "generator.test_batch.BatchTests.test_ac2_results_matched_by_custom_id_not_order",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "a batch result is checked before it is stored",
      "then": "it must pass every per-item rule: no system its draft lacks (write_text.added_systems), ERM control descriptions are one sentence of at most 30 words, no deny-list name, and no capitalized word outside the name lists and allow-list (005 AC-4); a failing item is resubmitted once in a second batch with the failure stated; an item that fails twice is not stored, the commit is blocked, and the script prints the key and reason for the owner (whose options are: keep templated text for that file, accept a hand edit reviewed against the same rules, or revise the plan)",
      "test": "generator.test_batch.BatchTests.test_ac3_rules_resubmit_once_then_block",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the full-size AI text is committed",
      "then": "it lives in src/features/generator/text/ai_text_full.jsonl, apart from the sample file; every full-size text item has an entry whose input hash matches; `check-text --size full` and `check-text` (sample) each find no orphan keys in their own file; the committed full-size text passes the AC-3 rules (test reads the file)",
      "test": "generator.test_batch.BatchTests.test_ac4_full_text_complete_current_and_clean",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "`python -m akg build` runs (full size, now defaulting to AI text)",
      "then": "every description at full size comes from the committed AI text; 006's full-size guard is removed and its AC-9 test retired; the difficulty and leakage tests of 007 (AC-1, AC-4, AC-5), 008 (AC-1, AC-4, AC-5) and 009 (AC-4) pass on the AI-text full build with their bands unchanged; the full golden is regenerated for AI text and the sample golden is unchanged",
      "test": "generator.test_risks, generator.test_controls and generator.test_issues run on the default (AI-text) full build; generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and test_ac5_full_build_matches_full_golden",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "the build or the tests run",
      "then": "they never import `anthropic` or touch the network at either size (005 AC-5 extended to full size with AI text)",
      "test": "generator.test_offline.OfflineTests.test_ac5_build_is_offline_and_never_imports_anthropic",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "f"
}
```

## Why
E2 publishes reconciliation accuracy on the AI-text build (epic revision 1), and R2 chose AI-written text because templated frames are a cue a matcher could exploit. This change writes all 1,274 full-size descriptions once, through the Message Batches API, under the owner's budget, and proves the difficulty bands still hold on the text E2 will actually see.

## Data impact
- **Budget.** Owner approved up to **$10** on 2026-11-20 (R2 decision.md). Measured cost is about $0.0039 per item at batch prices, about $4.97 per full pass of 1,274 items; the cap covers one full prompt revision plus resubmissions. The script refuses to submit over the cap; a second prompt revision beyond it needs a fresh owner approval.
- **Model and prompt.** claude-opus-5-5, low effort, the same rules as the sample (L-002), with the voices per file. Issue descriptions keep their four openings as the draft's first words so AI text does not homogenize them (009 AC-4 a).
- **Storage.** `text/ai_text_full.jsonl` beside the sample's `ai_text.jsonl`; keys are the internal keys (risk instance, control key, natural issue key), never positional; each entry carries its input hash.
- **Default text.** Full size now defaults to `--text ai`; 006's guard and its AC-9 test are retired; sample is unchanged.
- **docs/data-model.md** records the full-size AI text, the budget and actual cost, and that E2's numbers come from this build.

## Test plan
- Done check: `.venv\Scripts\python -m unittest discover -s tests -v`; every named test `ok`.
- Batch mechanics are tested offline with a recorded fake results file (shuffled), never the network.
- The paid run happens once, by hand, after approval; its log is committed.
- Not tested: E2's matcher itself.

## Risks
- **AI text makes matching easier** (L-002, L-008): bands re-run on AI text (AC-5); if a file fails after one prompt revision, the owner decides (keep templated for that file, or revise the epic).
- **Batch turnaround or partial failures**: progress saved per collection; resubmission once; nothing stored that fails the rules.
- **Budget overrun**: estimate before submit, refuse over cap, log actuals.

## Out of scope
- Seed robustness of scenario targets (parked from 009); E2's matcher and published numbers (E2).

## Relevant lessons
- L-002: every rule enforced in code and re-checked on the committed file.
- L-008: the exact-phrase lookups from 007-009 re-run on AI text inside the existing tests.
- L-005: the batch script adds no random draws to the build.

## Slices
1. Batch mode in write_text (estimate, budget refusal, hashed custom IDs, collection by ID, rules, resubmission), with offline tests; AC-1, AC-2, AC-3, AC-6.
2. Owner-approved paid run; commit text and cost log; AC-4.
3. Flip full default to AI text, retire the guard, re-run every band, regenerate full golden, data model; AC-5.
