# Verdict rule: count Cypher writes once, as SQL's

```json plan
{
  "id": "020-verdict-rule-count-cypher-writes-once-as",
  "tier": "standard",
  "status": "done",
  "created": "2026-11-21",
  "objective": "O2",
  "areas": [
    "src/features/rounds/**",
    "tests/**",
    "docs/data-model.md"
  ],
  "timebox": "3 hours. Past this, stop and re-plan.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`verdict.metrics` scores a Cypher text with write clauses (`CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`)",
      "then": "each write counts once, as a moving part, and not also as a clause, as a SQL `CREATE` or `INSERT` already does (owner decision 2026-11-21: make the rule symmetric; this is the asymmetry 018's review found and parked). `UNWIND` and `CALL` stay clauses (they read or scope, like SQL's `SELECT` and `FROM`). Every other count is unchanged. **The layout check keeps the writes:** a separate `CYPHER_LAYOUT` list (the scored clauses plus the writes) drives `clauses_per_line`, as `SQL_LAYOUT` already adds `JOIN`, so a line holding `MERGE ... SET` still fails the one-clause-per-line style rule; a pure assertion checks it. The pure tests: 017's `CALL { WITH row MERGE ... SET ... }` snippet goes from 6 clauses to 4 with 4 moving parts unchanged; a new case pairs a SQL `CREATE TABLE` plus `INSERT` with a Cypher `UNWIND` plus `MERGE` plus `CREATE` and checks that each write adds exactly one moving part and no clause on its side.",
      "test": "rounds.test_rounds_5_7.Rounds57Tests.test_ac5_symmetric_verdict_rule (updated; new write-symmetry case; a MERGE-and-SET line counts 2 in clauses_per_line) and rounds.test_rounds.RoundTests.test_ac2_measured_verdict_rule (updated snippet)",
      "status": "pass"
    },
    {
      "id": "AC-2",
      "when": "the rounds are re-measured and the export regenerated",
      "then": "only round 5 changes: SQL 29 vs Cypher **41** (was 46), measured `SQL` (unchanged), margin **+4.75** (was +9.75), with Cypher's metrics 5 clauses, 6 steps, 6 moving parts (pre-plan measurement, 2026-11-21). Rounds 1-4, 6, 7 and owner concentration keep every figure. The committed `src/features/rounds/rounds.json` is regenerated with both engines and its currency test passes; 018's expected-figures table in `test_ac5` changes only round 5's entry.",
      "test": "rounds.test_rounds_5_7.Rounds57Tests.test_ac4a_export_is_current and test_ac5_symmetric_verdict_rule",
      "status": "pass"
    },
    {
      "id": "AC-3",
      "when": "docs/data-model.md and the rounds README are read",
      "then": "round 5's entry gives the new figures; the verdict-rule text says writes count once, as a moving part, on both sides (now true) and gives the measured symmetry table below with its stated claim (moving parts follow one rule on both sides; clauses and steps measure what each language writes) and the disclosed differences (`OPTIONAL MATCH` pays a clause; filtering after an aggregate costs Cypher a moving part that SQL's `HAVING` does not, in rounds 2 and 6; upserts). The same wording reaches every place the rule is published: docs/data-model.md, the rounds README, the `verdict.py` docstring and `export.RULE['counting']`, which goes into `rounds.json` for the page. The docs tests check round 5's figures against the runner as before, and a test checks that `export.RULE['counting']` says writes count once and names the disclosed differences, including the aggregate filter. The table itself is pinned by `test_ac4_020_symmetry_table`.",
      "test": "rounds.test_rounds_5_7.Rounds57Tests.test_ac7_docs_describe_rounds_5_7_and_the_export, rounds.test_rounds.RoundTests.test_ac6_docs_describe_the_rounds, a new rounds.test_rounds_5_7.Rounds57Tests.test_ac3_020_published_rule_text, and a new rounds.test_rounds_5_7.Rounds57Tests.test_ac4_020_symmetry_table (pure: every row's snippets and measured triples)",
      "status": "pass"
    }
  ],
  "approved": "2026-11-21",
  "approved_hash": "295e7d845df97ffe",
  "in_progress": "2026-11-21",
  "done": "2026-11-22"
}
```

## Why
O2. A data scientist reading the page will check whether the scoring rule treats both languages alike. 018 made it symmetric by owner decision, but its review found one leftover: a Cypher write is charged as a clause and a moving part, a SQL write only as a moving part. Fixing it keeps "symmetric" true on the page before E4 publishes, and it changes no verdict.

## Symmetry table (L-019)
**What the rule claims, measured rather than asserted.** Each row is a minimal SQL snippet and the Cypher snippet that asks the same thing, with the (clauses, steps, moving parts) that `verdict.metrics` gives after this change (computed 2026-11-21, not hand-counted). A pure test, `rounds.test_rounds_5_7.Rounds57Tests.test_ac4_020_symmetry_table`, holds these snippets and asserts every cell, so the published table cannot drift from the code.

| Construct (snippet) | SQL | Cypher | Moving parts |
|---|---|---|---|
| Read: a filter and a projection | (3, 0, 0) | (3, 0, 0) | same |
| Join or hop: one join / one relationship | (2, 1, 0) | (2, 1, 0) | same |
| Fixed-length path: two joins / `*2` | (2, 2, 0) | (2, 2, 0) | same |
| Recursion: a recursive CTE anchored on a literal (`SELECT :v`) with one join / `*0..` (anchored on a table instead, SQL measures (8, 3, 1)) | (7, 2, 1) | (2, 1, 1) | same |
| Stage: a CTE / a `WITH` stage | (5, 1, 1) | (3, 0, 1) | same |
| Subquery: `IN (SELECT ...)` / `EXISTS { MATCH ... }` | (5, 1, 1) | (4, 1, 1) | same |
| Union: two branches | (5, 1, 1) | (5, 0, 1) | same |
| Write: `INSERT ... VALUES` / `MERGE` | (0, 0, 1) | (0, 0, 1) | same (**this change**: Cypher's write was also a clause) |
| Setup: `CREATE TABLE` + `INSERT` / `UNWIND` + `MERGE` + `CREATE` edge | (0, 0, 2) | (1, 1, 2) | same |
| Optional: `LEFT JOIN` / `OPTIONAL MATCH` | (2, 1, 0) | (3, 1, 0) | same; Cypher pays a clause (disclosed, owner decision in 018) |
| Filter after an aggregate (rounds 2 and 6): `GROUP BY ... HAVING` / `WITH` aggregate, then `WHERE` | (4, 0, 0) | (4, 0, 1) | **differs, disclosed** (owner decision 2026-11-21): Cypher's filter needs a `WITH` stage, 5 points more |
| Upsert (no round uses one): `INSERT ... ON CONFLICT DO UPDATE` / `MERGE ... ON CREATE SET ... ON MATCH SET` | (0, 0, 2) | (1, 0, 4) | **differs, disclosed** |
| `SELECT` inside a write (no round uses one): `INSERT ... SELECT` / `MATCH` + `CREATE` | (2, 0, 1) | (1, 0, 1) | same |

**So the published claim is:** moving parts (stages, subqueries, recursion, unions, writes) follow one rule on both sides, with two disclosed exceptions: filtering after an aggregate (SQL's `HAVING` against Cypher's `WITH` stage, which costs Cypher 5 points in rounds 2 and 6; owner decision 2026-11-21 to disclose it, not change the rule) and upserts (no round uses one); **clauses and steps measure what each language writes.** SQL pays a step for every table it names, including a CTE name or a union branch's table, where Cypher reuses a bound variable; SQL writes `SELECT` and `FROM` where Cypher writes `MATCH`. Those differences are the measurement, not a double charge, and the docs say so in these words rather than calling every metric symmetric.

## Data impact
None. No entity or store change. Only round 5's Cypher score and margin in `rounds.json` and the docs.

## Test plan
The two rounds test modules under `with_neo4j` (about a minute), then the full suite plain and under `with_neo4j`, logged to the scratchpad (L-017). CI runs again when main is pushed.

## Risks
- **Changing a published rule again.** The page is not live yet, so nothing published changes; the docs record the change and why.
- **A missed or mis-stated construct.** Two critique rounds found hand-counted cells wrong; the table is now generated from the code and pinned by a test.

## Out of scope
- `OPTIONAL MATCH` (kept by owner decision); weighting changes; the other parked 018 minors.

## Relevant lessons
- **L-018:** the new figures were measured before this plan.
- **L-019:** the symmetry table above, checked against the code in review.
- **L-012:** the docs quote the runner's figures.
