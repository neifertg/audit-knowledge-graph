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
      "then": "it has the approved copy below (revision 2026-11-22, the owner's choice after a brainstorm): **the headline** 'See the audit risks that sit between your risk register and your audit records.'; directly under it, **a list of three risks** marked `data-statement=\"three-risks\"`, the first and third with their figures rendered and marked (the blast radius's business units; the owner-concentration tie group's size, key controls and units) and the second, the repeat finding, carrying no figure; then a one-line pointer to the explainer (AC-3), marked `data-statement=\"kg-pointer\"`; then the synthetic-data note (marked `data-disclosure=\"synthetic\"`, reworded); then 021's three story cards and the judgment line, unchanged. **Removed from the top section:** the long intro paragraph ('A synthetic US regional bank keeps its risks...'), the earlier draft's 'In short' paragraph, and the comparison teaser, which **moves to open the `#rounds` section** as 'Graph or SQL?' with the wording below and its no-speed disclosure. The tie group's size is rendered by a new formatter `count_of_cap` (the length of a list as a capitalised number word, unit-tested). The test `COPY` list is updated; a test checks the list of three risks is the first element after the `<h1>`, and that 'Graph or SQL?' sits inside `#rounds`, not `#top`.",
      "test": "webpage.test_site.SiteTests.test_ac5_required_statements_and_no_speed_claims (COPY updated), test_ac1_025_three_risks_first, test_ac1_025_teaser_in_rounds, test_ac3_formatters (count_of_cap)",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the whole built page is checked",
      "then": "all 021 and 022 rules still hold, unchanged: every marked figure matches its source; no digit outside the allow-list and no number word outside marked elements (the new copy uses neither); no speed word outside a disclosure; `site.js` unchanged; one external resource. **The owner's visual check** of the built page on a local preview, top section only, is recorded in the review.",
      "test": "webpage.test_site.SiteTests (all), plus the owner's recorded check",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the `#rounds` section opens",
      "then": "it begins with the explainer **'What is a knowledge graph?'** (copy below, the owner's request 2026-11-22, placed here by the owner's choice), marked `data-statement=\"kg-explainer\"`, before 'Graph or SQL?': what a relational database and a knowledge graph each store, a one-line text diagram of one chain (system, control, risk, auditable entity, business unit) captioned as the direction a failure reaches, not the stored link direction, and the fair-to-SQL statement that both hold the same facts, that the graph writes a chain as a path and SQL as joins, and that the example question comes out close (round 3). No figure, no speed word. A test checks the explainer comes first in `#rounds`, before 'Graph or SQL?', and its fixed text is in `COPY`; the top section's pointer links to it (`href=\"#what-is-a-knowledge-graph\"`).",
      "test": "webpage.test_site.SiteTests.test_ac3_025_explainer_opens_rounds",
      "status": "pending"
    }
  ],
  "revised": "2026-11-22",
  "approved": "2026-11-22",
  "approved_hash": "df22d233dcdc2267"
}
```

## Why
O1. Before any reader saw the page, the owner read only its top section and summed it up as "data stored in a knowledge graph offers audit and risk insights that a typical SQL database cannot achieve" (recorded as a pilot in `research/o1-reader-test/results.md`; it does not count as a reader). That misses the page's point, connecting ERM and Internal Audit records to surface planning risks, and draws a conclusion the page does not make. The owner chose to sharpen the top section before spending the reader pool (2026-11-22). The pass rule, fixed in 023, is not changed: this edits the page, not the test.

## Copy (the owner's choice, 2026-11-22)
`[x]` is a rendered figure. Revision 2026-11-22: the owner, previewing the first draft, asked for a top section that cuts to the heart faster and more simply; after a brainstorm the owner chose the outcome as the headline with three one-line risks, the teaser moved out of the top section, and the long intro and the 'In short' paragraph dropped. The first bullet says 'A single' because 'One' would be an unmarked number word. The third bullet says what the data shows (two people each own nine key controls reaching seven units; 'reaching', because the units are reached through the controls' risks), not that all key controls rest with them. After the critique (2026-11-22): the explainer no longer calls chain questions 'natural' for the graph (its example is round 3, measured close, and now says so), the diagram is captioned as the direction of reach (three of its four stored links run the other way), and the node list names every node in the diagram. Scanned against 021's rules before this revision: no digit outside the allow-list, no number word, no speed word outside the disclosure.

**The top section:**
> **See the audit risks that sit between your risk register and your audit records.**
> - A single system failure that reaches [20] business units.
> - The same control failing again, filed under a new title.
> - [Two] people each holding [9] key controls reaching [7] business units.
>
> New to knowledge graphs? A short explanation opens the rounds below.
>
> *Synthetic data: a fictional US regional bank; descriptions AI-written ahead of time; no real institution, person or vendor.*
>
> (021's three story cards, unchanged, then: *The graph informs auditor judgment; it does not score risk or set the audit plan.*)

**Opening the `#rounds` section, first the explainer** (new, the owner's request):
> **What is a knowledge graph?** A relational database keeps facts in tables and connects them only when a query joins those tables. A knowledge graph stores the connections themselves: each system, control, risk, issue, auditable entity and business unit is a node, and each relationship, such as "this control mitigates that risk" or "this control depends on that system", is a stored link you can follow. Both hold the same facts here. A question that follows a chain of links, such as "what does this system's failure reach?", is written in the graph as a path and in SQL as a series of joins. The rounds below compare how much query each needs; for that question, both come out close.
>
> How a system failure reaches a business unit: system → control → risk → auditable entity → business unit

**Then the teaser** (moved from the top section):
> **Graph or SQL?** Both answer the same [seven] planning questions over the same facts, and their answers are proved equal. What differs is how much query each needs, scored by a published rule: SQL wins [once], the graph [three times], and [three] are close. *[disclosure: The difference is how much query each needs, not speed: no speed claims are made at demo scale.]*

## Before the reader script goes out (preconditions, in change 024)
1. This change is merged and **deployed**: main's Pages workflow still lacks 024's retry, so the first deploy attempt may fail as before; then re-run **all** jobs of that pages run.
2. **The owner re-confirms the live page** (light, dark, phone), because 024's AC-3 requires the confirmation for the build the readers see, and the build changes.
3. **Change 024 re-records** that build (the pages run and commit) in `docs/pages.md` and `results.md`, replacing `7d9c32e`, and notes in `results.md` that the top section was revised after the owner's pilot (change 025) with the pass rule unchanged.

## Data impact
None.

## Test plan
`tests/webpage/test_site.py`: the `COPY` list updated; new tests that the list of three risks is the first element after the headline (`test_ac1_025_three_risks_first`), that the teaser sits in `#rounds` (`test_ac1_025_teaser_in_rounds`), and that the explainer opens `#rounds` before the teaser, its text is in `COPY`, and the pointer's `href="#what-is-a-knowledge-graph"` resolves to an element with that `id` (`test_ac3_025_explainer_opens_rounds`); `count_of_cap` unit-tested in `test_ac3_formatters`. The obsolete `test_ac1_025_in_short_first` on the branch is removed with the 'In short' paragraph. The full suite on a fresh checkout (L-022). After the merge, the page redeploys; change 024 then records the new build as the readers' build before the script goes out.

## Risks
- **Teaching to the test.** The headline and the three risks say what the page is for in plain words; the pass rule was written in 023 before any answer and is unchanged. A page whose purpose a reader cannot restate is the failure O1 measures, so stating the purpose plainly is the fix, not a workaround.
- **The disclosure moves.** The no-speed disclosure stays a marked element in the teaser; the speed-word test still scopes to it.

## Out of scope
- The reader test itself (change 024, which waits for this change's deploy).
- Any other section.

## Relevant lessons
- **L-021, L-012:** figures stay rendered and marked; the new copy types none.
- **L-022:** the fresh-checkout run before review.
