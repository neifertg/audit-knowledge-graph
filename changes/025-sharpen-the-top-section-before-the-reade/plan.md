# Finish the brief before the reader test

```json plan
{
  "id": "025-sharpen-the-top-section-before-the-reade",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-22",
  "objective": "O1",
  "areas": [
    "src/features/site/**",
    "tests/**"
  ],
  "timebox": "Half a day. Past this, stop and re-plan.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "the brief's top section (`index.html`, `#top`, above 'For the audit plan') is read",
      "then": "it is the owner's brief from PRs #1 and #2 with its repetition removed (copy below): the H1 and the three-paragraph executive summary **unchanged** (they mirror the README); the second intro paragraph ('A synthetic US regional bank keeps its risks...') **removed**; the synthetic note and the planted-cases note **merged into one note** (marked `data-disclosure=\"synthetic\"`) that keeps what the summary does not already say: model-written descriptions, invented names, that the year-over-year riser is planted too (its name rendered from `derived:featured.yoy_name`, never typed), and that the planted cases are there to check the queries; then a one-line pointer to the explainer (AC-2), marked `data-statement=\"kg-pointer\"`, linking `#what-is-a-knowledge-graph`. A test on `index.html` only (the methods page keeps its own note) checks the order (H1, summary, note, pointer, 'For the audit plan'), that the removed paragraph and the old notes' text are gone from `index.html`, that `index.html` has exactly one element marked `data-disclosure=\"synthetic\"`, and that the riser's name in the note is a marked figure. The test `COPY` list is updated.",
      "test": "webpage.test_site.SiteTests.test_ac5_required_statements_and_no_speed_claims (COPY updated), test_ac1_025_top_trimmed",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the brief's 'Supporting evidence' group is read",
      "then": "it opens with the explainer **'What is a knowledge graph?'** (copy below; the owner's request of 2026-11-22, moved from the old `#rounds`, which now lives on `methods.html`), with `id=\"what-is-a-knowledge-graph\"` and `data-statement=\"kg-explainer\"`, directly before the SQL comparison story, whose heading changes from 'Does a graph beat SQL?' to **'Graph or SQL?'** (body unchanged). **Fair to SQL** (critique 2026-11-23): it says the relational store keeps each relationship as a row in a link table and the graph as an edge, that both stores here hold exactly the same links, and that the difference is how a query is written (a series of joins versus a path); it never says a relational database lacks the connections. The node list says 'such as'. No figure, digit, number word or speed word; the diagram is captioned as the direction a failure reaches. Tests: the explainer comes after 'Supporting evidence' and before the comparison story; the pointer's target id exists; 'Does a graph beat SQL?' appears nowhere on `index.html`; the explainer contains 'link table' and does not contain 'only when'; and its fixed 'both come out close' is held by asserting that round 3 is measured `close` **and** that round 3 is the blast-radius question (its first row's system is `site.json`'s `blast_radius.system_id`).",
      "test": "webpage.test_site.SiteTests.test_ac2_025_explainer_before_comparison",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the whole build is checked",
      "then": "all existing site tests still pass unchanged apart from `COPY`: every marked figure matches its source; no digit outside the allow-list and no number word outside marked elements; no speed word outside a disclosure; one external resource. **The branch starts from main's code** (critique 2026-11-23): after merging main into `change/025`, run `git checkout main -- src tests docs` and confirm `git diff main -- src tests docs` is empty before the first edit, so the earlier build (`count_of_cap`, the three-risks CSS, the removed `.lede` rule that `methods.html` still uses) is gone. At the end, `git diff --stat main -- src tests docs` lists only `src/features/site/template.html`, `src/features/site/site.css`, `src/features/site/README.md` and `tests/webpage/test_site.py`; that output is recorded in the review as the evidence that `site.js`, `methods.html`, `formatters.py` and the exports are untouched. **The owner's visual check** of the local preview (top section and 'Supporting evidence') is recorded in the review.",
      "test": "webpage.test_site.SiteTests (all), the recorded `git diff --stat main`, plus the owner's recorded check",
      "status": "pending"
    }
  ],
  "revised": "2026-11-23"
}
```

## Why
O1. Before any reader saw the page, the owner read only its top section and summed it up as "data stored in a knowledge graph offers audit and risk insights that a typical SQL database cannot achieve" (a pilot in `research/o1-reader-test/results.md`; it does not count). The owner then rewrote the page as an audit-planning brief (PRs #1 and #2, merged 2026-11-23, outside a capitan change), which superseded this change's earlier build. Reviewing those PRs found three things left to finish before the reader test: the top section repeats itself (a second intro paragraph and two notes restate the summary), there is no explanation of what a knowledge graph is (asked for on 2026-11-22), and the comparison is still headed 'Does a graph beat SQL?', the framing the pilot picked up. The owner chose to revise 025 to finish the brief (2026-11-23). The reader test's pass rule, fixed in 023, is not changed.

## Copy (revision 2026-11-23)
`[x]` is a rendered figure (`[Credit]` is `derived:featured.yoy_name`). Critique fixes of 2026-11-23: the explainer now describes the relational store's link tables (it no longer implies SQL lacks the connections), the node list says 'such as', the riser's name is rendered, and 'used to check the queries' is kept. Scanned against 021's rules: no digit outside the allow-list, no number word, no speed word outside a disclosure.

**The top section** (H1 and executive summary unchanged; then):
> *Synthetic data throughout: descriptions written by a model ahead of time and committed; names and companies invented. The [Credit] increase in the year-over-year findings is also a planted test case; the planted cases are there to check the queries.*
>
> New to knowledge graphs? A short explanation opens the supporting evidence below.

**Removed:** "A synthetic US regional bank keeps its risks in the ERM register and in Internal Audit's risk and control matrices. Both lists were reconciled into a single framework, then loaded into a relational database and a graph." and the two notes it replaces ("Synthetic data throughout. Descriptions were written by a model... This is not any employer's data." and "The warehouse, repeat-finding, stale-coverage, and Credit-increase examples are planted test cases...; the ownership tie was not planted."). Each fact they carried is still on the page: the summary says the bank is synthetic, names are invented, it is not any employer's data, which three examples are planted and that the ownership tie is not; the merged note adds the model-written text and the Credit increase.

**Opening 'Supporting evidence', the explainer:**
> **What is a knowledge graph?** A knowledge graph stores facts as nodes and the links between them: things such as systems, controls, risks, issues, auditable entities and business units are nodes, and each relationship, such as "this control mitigates that risk" or "this control depends on that system", is a link you can follow from node to node. A relational database can hold the same facts in tables, with each relationship as a row in a link table. Here, both stores hold exactly the same links. What differs is how a query is written: a question that follows a chain of links, such as "what does this system's failure reach?", is a path in the graph and a series of joins in SQL. The comparison below counts how much query each needs; for that question, both come out close.
>
> How a system failure reaches a business unit: system → control → risk → auditable entity → business unit

**Then the comparison story**, heading only changed: **Graph or SQL?** (body as merged in PR #1).

## Before the reader script goes out (preconditions, in change 024)
1. This change is merged and **deployed** (main's Pages workflow still lacks 024's retry; if the first deploy attempt fails, re-run **all** jobs of that pages run).
2. **The owner re-confirms the live page** (light, dark, phone): 024's AC-3 requires it for the build the readers see.
3. **Change 024 re-records** that build in `docs/pages.md` and `results.md`, replacing `7d9c32e`, noting that the page was rewritten as a brief (PRs #1, #2) and finished in 025 after the owner's pilot, with the pass rule unchanged.

## Data impact
None.

## Test plan
`tests/webpage/test_site.py`: `COPY` updated (removed paragraph and notes out; merged note, pointer, explainer and new heading in); `test_ac1_025_top_trimmed` (order, removals, a single synthetic disclosure); `test_ac2_025_explainer_before_comparison` (placement, pointer target id exists, no figure/digit/number word/speed word in the explainer, 'link table' present and 'only when' absent, round 3 measured `close` and is the blast-radius question, no 'Does a graph beat SQL?'). `src/features/site/README.md` gets a line on the explainer and the merged note. The branch reset and the final `git diff --stat main` (AC-3). The full suite on a fresh checkout (L-022).

## Risks
- **Teaching to the test.** The edit removes repetition and adds an explanation; it states nothing the page did not already show. The pass rule is unchanged.
- **Losing a disclosure in the merge.** Each fact from the removed notes is listed above with where it still appears; the copy test holds them.
- **Drift from the README.** The executive summary is untouched, so the README test still holds; the README's own body is out of scope.

## Out of scope
- `methods.html`, the executive summary's wording, the root README (already rewritten on main in 2215d61, which removed its old notes and renamed its comparison heading).
- Restoring the expected verdicts or the 'expected, not measured' claims on `methods.html` (raised in the review of PRs #1 and #2; the owner's call, separately).
- The reader test itself (change 024).

## Relevant lessons
- **L-021, L-012:** figures stay rendered and marked; the new copy types none.
- **L-022:** the fresh-checkout run before review.
- **L-023:** every folded-in item above is a named check.
