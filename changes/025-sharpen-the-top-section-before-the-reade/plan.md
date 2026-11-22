# Sharpen the top section before the reader test

```json plan
{
  "id": "025-sharpen-the-top-section-before-the-reade",
  "tier": "standard",
  "status": "approved",
  "created": "2026-11-22",
  "objective": "O1",
  "areas": [
    "src/features/site/**",
    "tests/**",
    "docs/**"
  ],
  "timebox": "Half a day. Past this, stop and re-plan.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "the built page's top section is read",
      "then": "it has the approved copy below: an **'In short'** paragraph directly under the headline that says what is connected (the ERM register and Internal Audit's records) and what an audit leader gets from it (the three risks the stories show, for planning); and the comparison teaser renamed **'Graph or SQL?'** and reworded so it reads as a comparison of how much query each needs, with the same answers proved equal, not as a verdict on which is better. Every other sentence of 021's copy is unchanged. The 'In short' paragraph is marked `data-statement=\"in-short\"`. 021's `COPY` list in the tests is updated to the new fixed text, and a test checks the 'In short' paragraph is the first element after the `<h1>`.",
      "test": "webpage.test_site.SiteTests.test_ac5_required_statements_and_no_speed_claims (COPY updated) and test_ac1_025_in_short_first",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the whole built page is checked",
      "then": "all 021 and 022 rules still hold, unchanged: every marked figure matches its source; no digit outside the allow-list and no number word outside marked elements (the new copy uses neither); no speed word outside a disclosure; `site.js` unchanged; one external resource. **The owner's visual check** of the built page on a local preview, top section only, is recorded in the review.",
      "test": "webpage.test_site.SiteTests (all), plus the owner's recorded check",
      "status": "pending"
    }
  ],
  "approved": "2026-11-22",
  "approved_hash": "e27592f4b82d654d"
}
```

## Why
O1. Before any reader saw the page, the owner read only its top section and summed it up as "data stored in a knowledge graph offers audit and risk insights that a typical SQL database cannot achieve" (recorded as a pilot in `research/o1-reader-test/results.md`; it does not count as a reader). That misses the page's point, connecting ERM and Internal Audit records to surface planning risks, and draws a conclusion the page does not make. The owner chose to sharpen the top section before spending the reader pool (2026-11-22). The pass rule, fixed in 023, is not changed: this edits the page, not the test.

## Copy (draft for the owner to edit at approval)
`[x]` is a rendered figure. Revised after critique round 1: the teaser uses verdict language ('wins'), because Cypher's score is lower in four rounds (1, 3, 6, 7) and round 3 is close only by the 1.25 line; the disclosure keeps 021's wording (the score is not line length); 'In short' makes the linked records its subject, because the repeat-finding story uses Internal Audit's records alone, and says 'in different years', as the story does. Scanned against 021's rules before this plan: no digit outside the allow-list, no number word, no speed word outside the disclosure.

**New, directly under the headline:**
> **In short:** linking risks, controls, systems and issues, in the ERM register and Internal Audit's records alike, shows an audit leader risks that no table shows on its own: a shared system that many business units depend on, the same control failing in different years under different titles, and key controls concentrated in a few hands. That is what audit planning can target.

**The teaser, reworded** (was "Does a graph beat SQL?"):
> **Graph or SQL?** Both answer the same [seven] planning questions over the same facts, and their answers are proved equal. What differs is how much query each needs, scored by a published rule: SQL wins [once], the graph [three times], and [three] are close. *[disclosure: The difference is how much query each needs, not speed: no speed claims are made at demo scale.]* [Details below.]

Everything else in the top section is 021's approved copy, unchanged.

## Before the reader script goes out (preconditions, in change 024)
1. This change is merged and **deployed**: main's Pages workflow still lacks 024's retry, so the first deploy attempt may fail as before; then re-run **all** jobs of that pages run.
2. **The owner re-confirms the live page** (light, dark, phone), because 024's AC-3 requires the confirmation for the build the readers see, and the build changes.
3. **Change 024 re-records** that build (the pages run and commit) in `docs/pages.md` and `results.md`, replacing `7d9c32e`, and notes in `results.md` that the top section was revised after the owner's pilot (change 025) with the pass rule unchanged.

## Data impact
None.

## Test plan
`tests/webpage/test_site.py`: the `COPY` list updated; a new test that the 'In short' paragraph is the first paragraph after the headline and before the first story. The full suite on a fresh checkout (L-022). After the merge, the page redeploys; change 024 then records the new build as the readers' build before the script goes out.

## Risks
- **Teaching to the test.** The 'In short' sentence says what the page is for in plain words; the pass rule was written in 023 before any answer and is unchanged. A page whose purpose a reader cannot restate is the failure O1 measures, so stating the purpose plainly is the fix, not a workaround.
- **The disclosure moves.** The no-speed disclosure stays a marked element in the teaser; the speed-word test still scopes to it.

## Out of scope
- The reader test itself (change 024, which waits for this change's deploy).
- Any other section.

## Relevant lessons
- **L-021, L-012:** figures stay rendered and marked; the new copy types none.
- **L-022:** the fresh-checkout run before review.
