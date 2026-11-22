# Verdict rule: count Cypher writes once, as SQL's

Change `020-verdict-rule-count-cypher-writes-once-as` · objective **O2**: A data scientist finds every claim credible and reproducible. Signal: one command reproduces every number on the page from a fresh clone; CI is green; every SQL-vs-Cypher round has a test proving both return the same answer; the page makes no claim without a test or a cited method.

## Why
O2. A data scientist reading the page will check whether the scoring rule treats both languages alike. 018 made it symmetric by owner decision, but its review found one leftover: a Cypher write is charged as a clause and a moving part, a SQL write only as a moving part. Fixing it keeps "symmetric" true on the page before E4 publishes, and it changes no verdict.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `verdict.metrics` scores a Cypher text with write clauses (`CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`) | each write counts once, as a moving part, and not also as a clause, as a SQL `CREATE` or `INSERT` already does (owner decision 2026-11-21: make the rule symmetric; this is the asymmetry 018's review found and parked). `UNWIND` and `CALL` stay clauses (they read or scope, like SQL's `SELECT` and `FROM`). Every other count is unchanged. **The layout check keeps the writes:** a separate `CYPHER_LAYOUT` list (the scored clauses plus the writes) drives `clauses_per_line`, as `SQL_LAYOUT` already adds `JOIN`, so a line holding `MERGE ... SET` still fails the one-clause-per-line style rule; a pure assertion checks it. The pure tests: 017's `CALL { WITH row MERGE ... SET ... }` snippet goes from 6 clauses to 4 with 4 moving parts unchanged; a new case pairs a SQL `CREATE TABLE` plus `INSERT` with a Cypher `UNWIND` plus `MERGE` plus `CREATE` and checks that each write adds exactly one moving part and no clause on its side. | `rounds.test_rounds_5_7.Rounds57Tests.test_ac5_symmetric_verdict_rule (updated; new write-symmetry case; a MERGE-and-SET line counts 2 in clauses_per_line) and rounds.test_rounds.RoundTests.test_ac2_measured_verdict_rule (updated snippet)` | pass | PASS |
| AC-2 | the rounds are re-measured and the export regenerated | only round 5 changes: SQL 29 vs Cypher **41** (was 46), measured `SQL` (unchanged), margin **+4.75** (was +9.75), with Cypher's metrics 5 clauses, 6 steps, 6 moving parts (pre-plan measurement, 2026-11-21). Rounds 1-4, 6, 7 and owner concentration keep every figure. The committed `src/features/rounds/rounds.json` is regenerated with both engines and its currency test passes; 018's expected-figures table in `test_ac5` changes only round 5's entry. | `rounds.test_rounds_5_7.Rounds57Tests.test_ac4a_export_is_current and test_ac5_symmetric_verdict_rule` | pass | PASS |
| AC-3 | docs/data-model.md and the rounds README are read | round 5's entry gives the new figures; the verdict-rule text says writes count once, as a moving part, on both sides (now true) and gives the measured symmetry table below with its stated claim (moving parts follow one rule on both sides; clauses and steps measure what each language writes) and the disclosed differences (`OPTIONAL MATCH` pays a clause; filtering after an aggregate costs Cypher a moving part that SQL's `HAVING` does not, in rounds 2 and 6; upserts). The same wording reaches every place the rule is published: docs/data-model.md, the rounds README, the `verdict.py` docstring and `export.RULE['counting']`, which goes into `rounds.json` for the page. The docs tests check round 5's figures against the runner as before, and a test checks that `export.RULE['counting']` says writes count once and names the disclosed differences, including the aggregate filter. The table itself is pinned by `test_ac4_020_symmetry_table`. | `rounds.test_rounds_5_7.Rounds57Tests.test_ac7_docs_describe_rounds_5_7_and_the_export, rounds.test_rounds.RoundTests.test_ac6_docs_describe_the_rounds, a new rounds.test_rounds_5_7.Rounds57Tests.test_ac3_020_published_rule_text, and a new rounds.test_rounds_5_7.Rounds57Tests.test_ac4_020_symmetry_table (pure: every row's snippets and measured triples)` | pass | PASS |

## Review in this order

1. **Data model and schema** (most expensive to get wrong): `docs/data-model.md`
2. **src/features/rounds/****: `src/features/rounds/export.py`, `src/features/rounds/rounds.json`, `src/features/rounds/verdict.py`
3. **Tests**: `tests/rounds/test_rounds.py`, `tests/rounds/test_rounds_5_7.py`

## Data impact
None. No entity or store change. Only round 5's Cypher score and margin in `rounds.json` and the docs.

## Risks
- **Changing a published rule again.** The page is not live yet, so nothing published changes; the docs record the change and why.
- **A missed or mis-stated construct.** Two critique rounds found hand-counted cells wrong; the table is now generated from the code and pinned by a test.

## Deliberately not in this PR
- `OPTIONAL MATCH` (kept by owner decision); weighting changes; the other parked 018 minors.

Parked for later:
- 2026-11-22 020 review minors: plan links the write-symmetry and layout assertions to test_ac5 but they live in test_ac3_020_published_rule_text; no test pins the table-anchored recursion figure SQL (8, 3, 1); docs point to the symmetry table in plan.md instead of reproducing it (E4 should publish it); Cypher upsert (1, 0, 4) comes from ON MATCH scored as a clause, a keyword-matcher quirk (disclosed, unused) (from 020-verdict-rule-count-cypher-writes-once-as)

## Lessons recorded
- L-021 Generate a published comparison table from the code and pin it with a test; never hand-count it

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `270c8aa01c119e09`
- Size: 5 code files, +97 / -22 lines
