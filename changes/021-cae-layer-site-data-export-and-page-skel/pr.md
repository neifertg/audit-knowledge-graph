# CAE layer, site data export and page skeleton

Change `021-cae-layer-site-data-export-and-page-skel` · objective **O1**: A CAE grasps the value in about 60 seconds without technical background. Signal: 2-3 audit people known to the owner read only the top section and each restates the value correctly in one sentence (milestone 1 passes at 2 of 3).

## Why
E4 child a (O1). The top of the page is what a CAE reads in 60 seconds and what the reader test judges. This change builds it, the export behind the blast-radius graph, and the builder and tests that make every figure on the page traceable to a committed export.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `python -m src.features.site.export --out <build>` runs on a loaded seed-42 build | it writes the committed `src/features/site/data/site.json` (deterministic JSON, sorted keys, no paths or timings) holding:
- **the blast-radius subgraph** for round 3's top system, taken from `rounds.json`'s first round-3 row (SYS-526): nodes for the system, its dependent controls, the risks they mitigate, the auditable entities exposed and the business units owning them, each with `id`, `kind` and `label` (names from the published files, INV-9); edges system to control, control to risk, risk to entity, entity to unit. Pre-plan measurement: 1 system, 44 controls, 40 risks, 41 entities, 20 units (146 nodes) and 44 + 48 + 85 + 41 = 218 edges;
- **the measured symmetry table** (AC-2);
- **the story figures**, stored as explicit counts so every figure has a single-field source: for the blast radius `system_name`, `controls` (44), `controls_with_risks` (43: one depends on the system but mitigates no risk, and the graph shows it linked to the system only), `risks`, `entities`, `units`, and per-unit entity counts; for the repeat finding `controls` (6) and `issues` (14), from `rounds.json`'s round 6; for owner concentration the whole top tie group's names (P-1562 and P-9499 tie at 9 key controls and 7 units), `key_controls` and `units`.

Read-only on `akg.sqlite` (017's read-only connection and views); it never reads the answer key. A test computes the subgraph independently from the CSVs and requires node and edge sets equal; a currency test regenerates from the cached seed-42 build and requires the committed file byte for byte. | `site.test_site.SiteTests.test_ac1_site_export_subgraph_and_currency` | pass | PASS |
| AC-2 | the measured symmetry table is generated | 020's construct snippets move from `tests/rounds/test_rounds_5_7.py` into `src/features/rounds/symmetry.py` (`SNIPPETS`: construct name to (SQL text, Cypher text, disclosed flag)), plus a new row for recursion anchored on a table, SQL (8, 3, 1) against Cypher (2, 1, 1), which 020's review asked to pin; `symmetry.table()` runs `verdict.metrics` on them, and the site export writes its output. **020's test keeps its literal construct-to-triples dict** and now also checks: the construct names in `SNIPPETS` and in the literal dict match in both directions; `symmetry.table()` equals the literals; the committed `site.json` table equals the literals; every undisclosed construct's moving parts are equal on both sides (L-021). The rounds README names `symmetry.py`, and docs/data-model.md's pointer to the table moves from 020's `plan.md` to `symmetry.py` and `site.json`. | `rounds.test_rounds_5_7.Rounds57Tests.test_ac4_020_symmetry_table (updated) and site.test_site.SiteTests.test_ac1_site_export_subgraph_and_currency` | pass | PASS |
| AC-3 | `python -m src.features.site.build --out <dir>` renders the page | it writes `<dir>/index.html` from `src/features/site/template.html` with the standard library only (`string.Template` or equivalent), copies `site.css`, `site.js`, `site.json`, `rounds.json` and `scores.json` beside it, and never reads `akg.sqlite` or a build (only committed files), so it runs in CI and in the Pages workflow. **Every figure is rendered in Python into an element marked with its source** (`data-source="rounds.json:rounds[2].rows[0][2]"`, `"site.json:subgraph.units"`, `"derived:verdict_counts.graph"`) and, where formatted, a named formatter (`data-format`: `fraction`, `signed`, `rows_shown`, `count_word`), each a small function in `src/features/site/formatters.py` with its own unit test. **Derived figures** (the verdict counts, "six of seven differ", "rounds 1, 3 and 7", per-story counts) come from named functions in `src/features/site/derived.py`. A test parses the built page, resolves every `data-source` path against the files, applies the formatter, and requires the text equal; for every `derived:` figure it recomputes the value **independently** from `rounds.json` in the test, not by calling `derived.py`. | `site.test_site.SiteTests.test_ac3_every_marked_figure_matches_its_source` | pass | PASS |
| AC-4 | the built page and its JS are checked for typed figures | **visible text:** the test takes the rendered page's visible text (no `<script>`, `<style>` or attributes), removes every marked element, splits the rest into tokens, and fails on any token containing a digit that is not on an exact allow-list (`60`, `1.25`, `M1`, `M2`, `L1`); it also fails on number words (`one` to `twenty`, `dozen`, `half`) outside marked elements, matched as whole words. Round numbers, IDs and dates shown on the page are marked too. **JS** (`site.js`) holds **no digit character at all** (the parked rule, pinned in its strictest form): colours, sizes and layout spacing come from CSS custom properties in `site.css`, read with `getComputedStyle`; no `fetch`, `XMLHttpRequest` or `import(`; text is written into the page only from node `label` fields of the embedded data (`textContent` or `innerText` assignments must take `.data('label')` or `label`; no `innerHTML`). **The graph's data** is embedded once as `<script type="application/json" id="site-data">`, and the test requires it to equal `site.json`'s subgraph. The canvas shows only names; every number on the page is in the static HTML. | `site.test_site.SiteTests.test_ac4_no_typed_figures_and_js_carries_none` | pass | PASS |
| AC-5 | the top section's copy is checked | it has the approved copy (below): a test holds the copy's fixed text segments (the words between the figures) and requires each in the rendered top section, so an edit to the copy is an edit to the test. It also has these required statements, each tested: the data is **synthetic** and the descriptions **AI-written** (once, committed); owner concentration is **derived, not planted**; the graph **informs auditor judgment and does not score risk**; the comparison measures **how much query each language needs, not speed**. **No speed language** in the visible text, as whole words (`faster`, `slower`, `speed`, `speedup`, `latency`, `milliseconds`, `ms`), except inside the element marked `data-disclosure="no-speed-claims"`, which says no speed claims are made at demo scale. Every name shown (systems, people, units) comes from the data, so INV-9 holds by construction; the test reuses the generator's existing denied-name check (`generator.test_names`'s list of real institution and vendor names) on the rendered page's visible text. | `site.test_site.SiteTests.test_ac5_required_statements_and_no_speed_claims` | pass | PASS |
| AC-6 | the page skeleton is read | it has: the top section; empty, labelled sections with stable ids for child b (`#rounds`, `#operating-model`, `#appendix`); a `<meta name="viewport">`; light and dark themes from `prefers-color-scheme` plus a toggle; Cytoscape.js loaded from `https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.34.4/cytoscape.min.js` with its published SRI hash (`sha512-9oWrVcc9R1+KL87uqCWwsamtDPJknyeNh/xCFh5SHEsgvV7Icb5Vgungsyljhdeyt+LNKGC9bhwKKQ0C6TiPOw==`) and `crossorigin="anonymous"` (released 2026-10-15, the latest release over two weeks old; checked on cdnjs 2026-11-22) and no other external resource; the graph **collapsed by default** to the system and its 20 business units (146 nodes is too dense to read in 60 seconds), with a click on a unit expanding its controls, risks and entities; and a text table beside the graph listing each unit and its entity count (marked figures), which is also the screen-reader alternative. **The owner's visual check** on a local preview (`python -m http.server` in the built folder), light and dark, at 375 px with no horizontal scroll, and one unit expanded, is recorded in the review. | `site.test_site.SiteTests.test_ac6_skeleton_pins_and_sections, plus the owner's recorded visual check` | pass | PASS |
| AC-7 | the docs are read | `src/features/site/README.md` (via `capitan feature`) gives the builder, the export, the marking and formatter rules, the allow-list, how to preview locally, and how to add a figure; docs/data-model.md gains a note on the site export (what it holds, how it is generated and checked, that it never reads the answer key). | `site.test_site.SiteTests.test_ac7_docs` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/site/****: `src/features/site/__init__.py`, `src/features/site/build.py`, `src/features/site/data/site.json`, `src/features/site/derived.py`, `src/features/site/export.py`, `src/features/site/formatters.py`, `src/features/site/site.css`, `src/features/site/site.js`, `src/features/site/template.html`
3. **src/features/rounds/symmetry.py**: `src/features/rounds/symmetry.py`
4. **Tests**: `tests/rounds/test_rounds_5_7.py`, `tests/webpage/__init__.py`, `tests/webpage/test_site.py`

## Data impact
- **New committed export:** `src/features/site/data/site.json` (subgraph, symmetry table, story figures). Derived, regenerable, never reads the answer key.
- **Moved:** 020's snippets to `src/features/rounds/symmetry.py`; 020's literal figures stay in its test.
- No entity, store or invariant change.

## Risks
- **The graph reads badly even collapsed.** The owner's preview is the check; a fallback is a static unit chart from the same marked table.
- **The allow-list or number-word scan fights the copy.** The copy above was written against those rules; a new literal needs a reason in review.
- **The copy does not land with readers** (O1). That is what child c's reader test measures; this plan's copy is the owner's to edit before approval.

## Deliberately not in this PR
- The rounds, operating model and appendix sections' content (child b); Pages, the portfolio card and the reader test (child c).
- Any figure not in a committed export.

Parked for later:
- 2026-11-22 021 review minors: site.json's repeat-finding and owner key-control figures are checked only by the currency test, not independently (child b could add an oracle check); site.json is tracked inside a folder .gitignore ignores (data/), so a recreated or new file there needs git add -f (owner: consider a '!src/features/site/data/' exception in .gitignore, governance) (from 021-cae-layer-site-data-export-and-page-skel)

## Lessons recorded
- L-022 Passing locally is not proof: run the done-check on a fresh checkout

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `3d75eefa91cda473`
- Size: 13 code files, +3062 / -37 lines

## Note on test names
The plan names its tests `site.test_site...`. During the build the folder was renamed `tests/site` to `tests/webpage`, because Python's standard-library `site` module shadowed it under `unittest discover`; the same tests now run as `webpage.test_site...` (lesson L-022).
