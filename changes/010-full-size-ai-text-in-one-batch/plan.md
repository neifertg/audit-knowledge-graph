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
      "then": "the budget is cumulative: it refuses, before reading secrets.yaml or creating any API client, when spend already logged in research/r2-synthetic-text-realism/cost_log.md plus this run's estimate (per file: items x measured per-item usage at batch prices; re-estimated from actual usage after the first collection) exceeds the budget, and prints both figures; with room it submits one Message Batch, records the batch ID, and on collection appends actual tokens and cost to cost_log.md. Tested offline with a fake client standing in for the external API (the one boundary we mock): refusal touches neither secrets nor client; submission records the batch ID; collection appends the log line",
      "test": "generator.test_batch.BatchTests.test_ac1_over_budget_refused_before_any_client and generator.test_batch.BatchTests.test_ac1_submission_and_collection_log_cost",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "batch results are collected (offline test: a recorded fake batch result file, no network)",
      "then": "batch requests set no `fallbacks`, `stream` or `speed` (the Batches API rejects them); each request's custom ID is a hash of its internal key (unique, allowed characters and length); results are matched by custom ID, never by order (the fake results file is shuffled); an unknown or missing custom ID is reported by name; results that are `errored`, `expired` or `canceled`, or succeed with stop_reason `refusal` or `max_tokens`, count as failures for AC-3's single resubmission",
      "test": "generator.test_batch.BatchTests.test_ac2_results_matched_by_custom_id_not_order",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "a batch result is checked before it is stored",
      "then": "a batch result is stored only if it passes every per-item rule: no system its draft lacks (write_text.added_systems); ERM control descriptions are one sentence of at most 30 words; issue descriptions begin with their draft's opening words (the four openings stay varied, 009 AC-4 a); no deny-list name; no capitalized word outside the name lists and allow-list (005 AC-4). A failing item is resubmitted once in a second batch with the failure stated; an item that fails twice is not stored and the script prints its key and reason. The block is mechanical: without its text the AI-text full build fails on the missing key, so AC-5 cannot pass until the owner chooses (keep templated text for that file, a hand edit checked by the same rules, or revise the plan)",
      "test": "generator.test_batch.BatchTests.test_ac3_rules_resubmit_once_then_block",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the full-size AI text is committed",
      "then": "the full-size AI text lives in src/features/generator/text/ai_text_full.jsonl, apart from the sample file; every full-size text item has an entry whose input hash matches; the committed file passes the AC-3 rules; and, at full size as at sample size, a copy with one entry removed or one hash altered fails the build naming the key, and one extra key fails `check-text --size full` naming it, while the sample's check-text still passes on its own file",
      "test": "generator.test_batch.BatchTests.test_ac4_full_text_complete_current_and_clean",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "`python -m akg build` runs (full size, now defaulting to AI text)",
      "then": "full size defaults to AI text, and every description at default counts comes from the committed AI text; `--count` overrides at full size (whose new items have no AI text) build with `--text templated`, and the tests that use them say so; 006's guard is removed and its AC-9 test retired; the difficulty and leakage tests of 007 (AC-1, AC-4, AC-5), 008 (AC-1, AC-4, AC-5) and 009 (AC-4) pass on the AI-text full build with bands unchanged; the cue measurements docs/data-model.md publishes (control citation lookups, the repeat-finding finding-sentence cue) are re-measured on AI text and updated; the full golden is regenerated for AI text; the sample golden is unchanged; the whole suite passes (done = full suite)",
      "test": "generator.test_risks, generator.test_controls and generator.test_issues run on the default (AI-text) full build; generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and test_ac5_full_build_matches_full_golden",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "the build or the tests run",
      "then": "the build never imports `anthropic` or touches the network, at sample size and at full size with AI text, and no test module imports `anthropic` (the batch tests use a fake client)",
      "test": "generator.test_offline.OfflineTests.test_ac5_build_is_offline_and_never_imports_anthropic (extended to full size) and generator.test_batch.BatchTests.test_ac6_tests_never_import_anthropic",
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
- **Budget.** Owner approved up to **$10** on 2026-11-20 (R2 decision.md), counted cumulatively in `cost_log.md`. Measured cost is about $0.0039 per item at batch prices (from 6 sample calls; IA controls have longer drafts, so the estimate is re-taken from actual usage after the first collection), about $5 per full pass of 1,274 items. The cap covers one full pass, the resubmission of failures, and regenerating one or two files after a prompt revision; it does **not** cover a second complete pass, which would need a fresh owner approval. The script refuses any run that would cross the cap.
- **Model and prompt.** claude-opus-5-5, low effort, the same rules as the sample (L-002), with the voices per file. Issue descriptions keep their four openings as the draft's first words so AI text does not homogenize them (009 AC-4 a).
- **Storage.** `text/ai_text_full.jsonl` beside the sample's `ai_text.jsonl`; keys are the internal keys (risk instance, control key, natural issue key), never positional; each entry carries its input hash.
- **Default text.** Full size now defaults to `--text ai`; 006's guard and its AC-9 test are retired; sample is unchanged.
- **docs/data-model.md** records the full-size AI text, the budget and actual cost, and that E2's numbers come from this build.

## Test plan
- Done check: `.venv\Scripts\python -m unittest discover -s tests -v`; the whole suite passes and every named test is `ok`. Help text and comments that say full size is templated are updated.
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
