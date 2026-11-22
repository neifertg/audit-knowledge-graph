# E4 Page v1 and publish

```json plan
{
  "id": "004-e4-page-v1-and-publish",
  "tier": "epic",
  "status": "draft",
  "created": "2026-11-19",
  "revised": "2026-11-22",
  "objective": "O1",
  "children": [
    {
      "key": "a",
      "title": "CAE layer, site data export and page skeleton",
      "depends_on": []
    },
    {
      "key": "b",
      "title": "Rounds, operating model and technical appendix",
      "depends_on": ["a"]
    },
    {
      "key": "c",
      "title": "Publish on GitHub Pages, portfolio card and the O1 reader test",
      "depends_on": ["b"]
    }
  ]
}
```

## Why
O1 first, O2 second: one scroll that gives a CAE the value in 60 seconds and gives a data scientist the depth to trust it. This is what hiring audiences actually see (O5). It also completes M1, whose done conditions are all on this page: it is live, CI is green (done in E3), reconciliation precision and recall are shown, and 2 of 3 readers pass the O1 test.

## What E3 changed (revision 2026-11-22)
This epic was drafted before E3. E3's results change what the page says:
- **The comparison's honest headline.** Under the symmetric rule (owner decisions in 018 and 020), the seven rounds measure SQL once (round 5, a new third-party register), graph three times (rounds 1, 6, 7) and close three times (rounds 2, 3, 4); six of seven differ from the verdicts expected before the queries were written. Much of the usual "graph advantage" turns out to be a schema advantage: once SQL has views merging ERM and IA, fixed-depth questions come out close. The page says this plainly, and says where a graph should clearly win but M1 cannot show it yet (variable-depth questions, exploration, scale, changing questions).
- **Owner concentration is derived, not planted** (E3). The top layer shows two planted stories (shared-system blast radius, repeat finding in disguise) and owner concentration labelled as a derived supporting finding.
- **The repository already exists** (E3 child e, public, CI green). Child c only turns on Pages; nothing is created.
- **The measured verdict is shown beside the expected one** for every round, with the scores, the margin from the 1.25 line, the rounds within one point named (1, 3 and 7), the measured symmetry table reproduced on the page (020's parked note), and the disclosed exceptions (filtering after an aggregate; upserts; `OPTIONAL MATCH` pays a clause).

## Shape
`src/features/site/` (with its feature README): an HTML template, CSS, a little JS, and a **site builder in Python** (`python -m src.features.site.build --out <dir>`, standard library only) that renders the page. Rules for every child:
- **Figures are rendered in Python, not in the browser.** The builder fills the template from committed exports (`src/features/rounds/rounds.json`, `src/features/reconciliation/scores.json`, and child a's site-data export), so every figure is in the static HTML. Each rendered figure sits in an element marked with the export field it came from (`data-source="rounds.json:rounds[4].scores.sql"`, for example) and, where it is combined or formatted, a named formatter (`data-format="fraction"` for "33/33", `"signed"` for "+4.75", `"rows_shown"` for "20 of 61"); the formatters are a few small functions shared by the builder and the test, and each has its own unit test. A test checks every marked figure equals its source through its formatter. **Derived figures are marked too:** the headline counts ("SQL once, graph three times, close three times", "six of seven differ", "rounds 1, 3 and 7 within one point", and any count written in words) are rendered by the builder from `rounds.json` into marked elements, and the test recomputes each from `rounds.json` independently of the builder.
- **No figure is typed anywhere** (template, builder or JS): a test takes the **rendered page's visible text**, removes every marked element, and allows only a short listed set of literal numbers in what remains (such as `60` seconds, `1.25`, `375` px, `M1`, `M2`); any other digit run fails it. This covers a number typed in the builder as well as in the template, and ignores CDN pins, integrity hashes and CSS values, which are not visible text. **JS** is limited to interaction (the graph, the theme switch): a test checks it does not fetch (`fetch`, `XMLHttpRequest`, `import(`) and holds no string literal containing a digit, so no figure can pass through it. (Critique rounds 1 and 2.)
- **The measured symmetry table has a source:** 020's construct snippets move from the test into `src/features/rounds/symmetry.py`, and the site-data export runs `verdict.metrics` on them. **020's test keeps its literal construct-to-triples dict** (it does not loop over the generated table, which would only check the code against itself): it checks the construct names match in both directions, that `symmetry.py`'s live output and the committed export both equal the literals, and that every undisclosed construct's moving parts are equal on both sides (L-021).
- **CDN libraries pinned to exact versions** (Cytoscape.js for the graph); no other external calls. Light and dark themes; works at phone width (no horizontal scroll at 375 px); a text table beside the graph for screen readers and for tests.
- **Claims follow GOALS and O2:** synthetic data, said up front, with the AI-written text disclosed; no real institution, person or vendor names (INV-9); no speed claims at demo scale; no vendor endorsement; the graph informs auditor judgment and does not score risk. **A claim with no test or cited method is labelled "expected, not measured in M1"** (where a graph should win at variable depth or at scale, which is M2's benchmark question; the effort estimate, given with its basis in this project's own change log), and the required-statements test checks each label. The same test fails on speed or performance language in the visible text (`faster`, `slower`, `speed`, `performance`, `ms`, `seconds to run` and the like) outside an element labelled "expected, not measured in M1".
- **Truncated results say so:** `rounds.json` keeps up to 20 rows per round, so a round with more (rounds 1 and 4) shows "20 of N rows" and links to the full export and to how to reproduce it.
- **Tests** run with the standard library only (no browser automation: no package is approved for it). They parse the rendered HTML, check every marked figure against its export, check the template's allowed numbers, check the data files' currency, and check the copy's required statements and labels. Visual checks (themes, phone width, the graph) are done by the owner on a local preview of the built page and recorded in each child's review.
- docs/data-model.md gains a note on the site-data export (what it holds, how it is generated and checked).

**a. CAE layer, site data export and page skeleton (1.5 days).** Areas: `src/features/site/**`, `src/features/rounds/symmetry.py`, `src/features/rounds/README.md`, `tests/**`, `docs/**`.
- The top section a CAE reads in about 60 seconds: a headline, one paragraph on the problem (risk between tables; ERM and IA as separate populations), and the stories, each with one line of business impact:
  1. *Shared-system blast radius* (round 3; planted): one clickable graph from the top system through its dependent controls and the risks they mitigate to the auditable entities exposed;
  2. *Repeat finding in disguise* (round 6; planted): the same control failing in different years under different titles, found through links and dates;
  3. *Owner concentration* (supporting query; **derived, not planted**, and labelled so).
- **Site data export:** `python -m src.features.site.export` writes the committed data the page needs beyond `rounds.json` and `scores.json`: the blast-radius subgraph for round 3's top system (from `akg.sqlite`) and the measured symmetry table (above). It is deterministic and checked current by a test against the cached seed-42 build; the graph's node and edge counts must equal an independent computation from the CSVs.
- The site builder, the template with the allowed-numbers rule, and the page skeleton: sections for b's content, themes, layout, the CDN pins.

**b. Rounds, operating model and technical appendix (2 days).** Areas: as a.
- **The seven rounds** side by side from `rounds.json`: question, both queries, scores, margin, measured and expected verdicts, the three checks, and round 7's top riser; the verdict rule, the measured symmetry table and the disclosed exceptions; the shared views as published setup.
- **The operating model:** when a graph earns its place beside a GRC system and when good SQL views are enough (from the measured results above); pros and cons; keys for success; a maintenance table (what changes when the taxonomy, a source system or the reconciliation changes); an effort estimate stated as an estimate.
- **The technical appendix:** the data model; the generator's design (synthetic, seeded, AI text generated once); reconciliation precision and recall from `scores.json` with its four caveats (an M1 done condition); test and CI results (link to the CI runs); limitations; how to reproduce from a fresh clone.

**c. Publish, portfolio card and the O1 reader test (1 day plus the readers' time).** Areas: `src/features/site/**`, `tests/**`, `docs/**`, `research/**`, plus governance files the owner commits.
- **Pages, by a GitHub Actions workflow** (the branch-and-folder setting serves only the root or `/docs`, which does not fit this layout). The workflow, drafted by the agent and committed by the owner through `allow-governance` as in E3 child e, runs only after the `tests` workflow succeeds on main (`workflow_run` on `tests.yml` with a success condition, so a red suite never deploys), runs the site builder on the committed exports and deploys its output directory, which holds the page and every data file it links to. Nothing generated is committed. The owner reviews the built page on a local preview and confirms before turning Pages on. Done when the live URL serves the page and its linked data files; the live check is recorded after the deploy, not asserted by a test in the run that deploys it (L-020).
- **Portfolio card:** a card on the owner's `risk-analytics-portfolio` linking to the page. That is another repository: the owner makes the change, or explicitly asks the agent to, in c.
- **The O1 reader test** (GOALS): 2-3 audit people the owner knows read only the top section and restate the value in one sentence; M1 passes at 2 of 3. The owner runs it; the agent prepares a one-page script and a results template; results are recorded without names in `research/o1-reader-test/`. **If fewer than 2 of 3 pass,** the agent proposes a revision of the top section from what the readers said, it goes through a small change, and the test is re-run with readers who have not seen the page; M1 is not done until it passes, and after a second miss the owner decides how to proceed.

## Out of scope
- Live GraphRAG chat and the AWS production-architecture diagram: parked.
- Documents and the vector layer, the scaling benchmark and centrality: M2.
- The template kit (O4): M3.
- Changing the verdict rule or any round: E3 is closed; the page reports it.

## Relevant lessons
- **L-001:** the Pages workflow and anything the owner runs come as copy-paste blocks.
- **L-012 and L-021:** every figure on the page is generated from a committed export and checked by a test, never typed.
- **L-018:** the page's claims (the headline above) were measured before this revision.
- **L-020:** a test that runs in CI must not require evidence of its own run (relevant to c's live-URL check).
- **L-017:** long local runs log to the scratchpad; reviewers read the logs.

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard --epic 004-e4-page-v1-and-publish --child <key>).
