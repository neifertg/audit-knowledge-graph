# Full-size AI text in one batch

```json plan
{
  "id": "010-full-size-ai-text-in-one-batch",
  "tier": "standard",
  "status": "in-progress",
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
      "then": "the budget is cumulative and fails closed. research/r2-synthetic-text-realism/cost_log.md (path resolved from the module, committed now with an empty table) holds one row per batch (`| batch_id | files | items | estimated_usd | actual_usd | status |`). Before any API call the script writes a `submitting` row with the estimate; after the API accepts the batch it records the batch ID (status `submitted`); collection updates the row to actual cost (status `collected`). Spend counts actual cost where collected and the estimate for `submitting` and `submitted` rows; a missing log, an unparseable row or an unknown status refuses the run. The estimate is per file: items x measured per-item usage at batch prices x 1.25, re-taken from actual usage after the first collection; `max_tokens` is 450 per request, so even a worst-case full pass (every response at the cap) costs about $8.2, under the $10 cap. A run is refused, before reading secrets.yaml or creating any API client, when spend plus estimate exceeds the budget. Offline tests (the API client is passed in, a fake standing in for the one external boundary): the same $5 estimate is refused with a $6 `submitted` row, refused with a $6 `collected` row, and accepted with the empty log; an unparseable row and an unknown status are refused; a successful submission writes `submitting` then `submitted`; collection writes `collected` with actual cost",
      "test": "generator.test_batch.BatchTests.test_ac1_over_budget_refused_before_any_client and generator.test_batch.BatchTests.test_ac1_submission_and_collection_log_cost",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "batch results are collected (offline test: a recorded fake batch result file, no network)",
      "then": "batch requests set no `fallbacks`, `stream` or `speed` (the Batches API rejects them); each request's custom ID is a hash of its internal key (unique, allowed characters and length); results are matched by custom ID, never by order (the fake results file is shuffled); an unknown or missing custom ID is reported by name; results that are `errored`, `expired` or `canceled`, or succeed with stop_reason `refusal` or `max_tokens`, count as failures for AC-3's single resubmission; the tests feed one failing input per result type (errored, expired, canceled, refusal, max_tokens) and assert each becomes a failure",
      "test": "generator.test_batch.BatchTests.test_ac2_results_matched_by_custom_id_not_order",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "a batch result is checked before it is stored",
      "then": "a batch result is stored only if it passes every per-item rule: no system its draft lacks (write_text.added_systems); ERM control descriptions are one sentence of at most 30 words; full-size issue descriptions begin with their draft's opening words, which the full-size prompt instructs explicitly (the four openings stay varied, 009 AC-4 a); no deny-list name; no capitalized word outside the name lists and allow-list (005 AC-4). The tests feed one failing result per rule and assert each is rejected. A failing item is resubmitted once, with the same prompt version and the failure stated, in a second batch; an item that fails twice is not stored and the script prints its key and reason. The block is mechanical: without its text the AI-text full build fails on the missing key, so AC-5 cannot pass until the owner chooses (keep templated text for that file, a hand edit checked by the same rules, or revise the plan). Each full-size entry's input hash includes the full-size prompt version (a hash of the system prompt, voices and the opening instruction), so text from two prompt versions is detected as stale; the sample keeps its original prompt and its existing hashes, so the frozen sample build and golden do not change; any prompt change means regenerating the whole set (L-002), which is a second complete pass and needs a fresh owner approval",
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
      "then": "full size defaults to AI text, and every description at default counts comes from the committed AI text; `--count` overrides at full size (whose new items have no AI text) build with `--text templated`, and drift tests that compare an override with the default build compare templated with templated (009 AC-7, 006 AC-6); 006's guard is removed and its AC-9 test retired; the difficulty and leakage tests of 007 (AC-1, AC-4, AC-5), 008 (AC-1, AC-4, AC-5) and 009 (AC-4) pass on the AI-text full build with bands unchanged; the cue measurements docs/data-model.md publishes (control citation lookups, the repeat-finding finding-sentence cue) are computed by helpers in tests/generator/difficulty.py, recorded in tests/golden/cue_figures.json and quoted in docs/data-model.md, and a named test fails when the build's figures differ from the recorded ones by more than 0.01, or when docs/data-model.md does not quote each recorded figure (so the published numbers can never go stale silently); the full golden is regenerated for AI text; the sample golden is unchanged; the whole suite passes (done = full suite); `sample-pack --size full` shows templated and AI descriptions side by side under the full-size introduction, with no text-choice prompt (007 AC-7's no-AI-column assertion is updated accordingly)",
      "test": "generator.test_risks, generator.test_controls and generator.test_issues run on the default (AI-text) full build; generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and test_ac5_full_build_matches_full_golden; generator.test_batch.BatchTests.test_ac5_published_cue_figures_match_the_build; generator.test_sample_pack.SamplePackTests.test_ac7_full_size_pack_describes_full_size",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "the build or the tests run",
      "then": "the build never imports `anthropic` or touches the network, at sample size and at full size with AI text; the batch code takes its API client as a parameter and only the command-line entry creates a real one; a runtime check runs the batch tests in a subprocess and asserts `anthropic` is not in sys.modules afterwards",
      "test": "generator.test_offline.OfflineTests.test_ac5_build_is_offline_and_never_imports_anthropic (extended to full size) and generator.test_batch.BatchTests.test_ac6_tests_never_import_anthropic",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "f",
  "approved": "2026-11-20",
  "approved_hash": "fbe4f82f909f3fe3",
  "in_progress": "2026-11-20"
}
```

## Why
E2 publishes reconciliation accuracy on the AI-text build (epic revision 1), and R2 chose AI-written text because templated frames are a cue a matcher could exploit. This change writes all 1,274 full-size descriptions once, through the Message Batches API, under the owner's budget, and proves the difficulty bands still hold on the text E2 will actually see.

## Data impact
- **Budget.** Owner approved up to **$10** on 2026-11-20 (R2 decision.md), counted cumulatively in `cost_log.md`. Measured cost is about $0.0039 per item at batch prices (from 6 sample calls; IA controls have longer drafts, so the estimate is re-taken from actual usage after the first collection), about $5 per full pass of 1,274 items. The cap covers one full pass and the resubmission of failures (same prompt). Any prompt change means regenerating the whole set (L-002), a second complete pass, which needs a fresh owner approval. The script refuses any run that would cross the cap.
- **Model and prompt.** claude-opus-5-5, low effort, the same rules as the sample (L-002), with the voices per file, plus one full-size instruction: issue descriptions begin with their draft's opening words, so AI text keeps the four openings varied (009 AC-4 a). The full-size prompt has its own version in the full-size hashes; the sample keeps its original prompt and hashes.
- **Worst case.** `max_tokens` 450 bounds a full pass at about $8.2 even if every response hits the cap; truncated responses count as failures and get the one resubmission.
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
