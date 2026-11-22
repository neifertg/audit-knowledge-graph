# Rounds 1-4: paired SQL and Cypher with agreement tests

```json plan
{
  "id": "017-rounds-1-4-paired-sql-and-cypher-with-ag",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-21",
  "objective": "O2",
  "areas": [
    "src/features/rounds/**",
    "tests/**",
    "docs/data-model.md",
    "akg/**"
  ],
  "timebox": "1.5 days. Past this, stop and re-plan or split.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`src/features/rounds/` is read",
      "then": "each of rounds 1-4 has one `.sql` and one `.cypher` file and an entry in a registry (`rounds.ROUNDS`) giving its number, question, result columns and expected verdict (1: SQL, 2: close, 3: graph, 4: graph).\n\n**Both engines see both sources the same way.** Neo4j already merges ERM and IA under one label (`Risk`, `Control`) with shared relationship types, and INV-10 means no edge crosses sources, so the Cypher needs no `source` filter. SQL gets the same merging from `views.sql`: temporary views (`risk`, `mitigates`, `exposed_to`, `against_risk`, `depends_on`, `requires`), each a `UNION ALL` of the two per-source tables. The runner creates them on each connection; they are not part of the store schema. They are shared setup, counted once and published beside the verdicts (36 lines, 6 unions), never charged to a round. Round SQL files must not name a per-source table (`*_erm`, `*_ia`), except `audit_tested_control_ia`, which has no ERM counterpart.\n\nThe queries are pinned as follows:\n1. *Open issues by business unit and rating.* Open means `closed_date` is NULL. An issue is attributed to every business unit that owns an auditable entity exposed to a risk the issue is against (issue, against, risk, exposed entity, owned by unit). Rows: (`business_unit_id`, `business_unit_name`, `rating`, `open_issues`), counting distinct issues. An issue can count in more than one unit.\n2. *High risks with stale coverage, on canonical items.* A canonical risk is High when any member (a `risk_maps_to_canonical` row) is rated High. It qualifies when no control mitigating any member was tested by an audit whose `end_date` is **on or after** the cutoff (inclusive). The cutoff is one query parameter (`:cutoff` in SQL, `$cutoff` in Cypher), never a literal, and the round's default is 2023-12-31 (24 months before window end 2025-12-31), held once in the registry. A never-tested control is stale, and every audit lies in the window (INV-5). Rows: (`canonical_risk_id`, `has_ia_member` Y/N). The flag is there because audits test IA controls only, so a canonical risk with no IA member is stale by construction; the page can then split the answer honestly.\n3. *Shared-system blast radius.* For each system, the distinct auditable entities reached through control depends on system, mitigates risk, exposed entity. Rows: the top 3 (`system_id`, `system_name`, `entities`), ordered by entities descending, then system name (E1's tie rule).\n4. *Every path from a regulation to a business unit.* Regulation, requires control, mitigates risk, exposed entity, owned by unit. Rows: (`regulation_id`, `business_unit_id`, `paths`), one per distinct pair, where `paths` counts the distinct (control, risk, entity) chains.\n\n**Query style**, for readability on the page (the verdict counts clauses, not lines, so layout cannot move it; AC-2):\n- each clause keyword starts its own line (SQL: `WITH` entries, `SELECT`, `FROM`, `JOIN` with its qualifier, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`, `LIMIT`, `UNION ALL`; Cypher: `MATCH`, `OPTIONAL MATCH`, `WHERE`, `WITH`, `RETURN`, `ORDER BY`, `LIMIT`, `UNION`);\n- keywords are matched as whole, case-insensitive words outside string literals, with `OPTIONAL MATCH`, `WITH RECURSIVE`, `LEFT JOIN`, `STARTS WITH` and `ENDS WITH` read as one token (the last two are operators, not clauses). In Cypher, a keyword inside `(...)` or `[...]` is part of an expression, not a clause (for example the `WHERE` in `any(m IN members WHERE ...)`);\n- no line exceeds 100 characters; comments sit on their own line and start with `--` or `//`;\n- no comma joins in SQL (`FROM a, b`).",
      "test": "rounds.test_rounds.RoundTests.test_ac1_registry_files_and_query_style (pure: every registered round has both files and its columns; no line over 100 characters; no line holds two clause keywords, with a pure case for each multi-word token above; no comma join; no per-source table in a round's SQL except audit_tested_control_ia)",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the measured verdict is computed for a pair of queries",
      "then": "`verdict.metrics(text, engine)` returns, ignoring comments and string literals:\n- `clauses`: whole-word clause keywords, the multi-word tokens of AC-1 as one, with Cypher keywords inside `(...)` or `[...]` excluded. The full sets (wider than AC-1's layout list, so child d's writes score under the same rule): SQL `WITH`, `WITH RECURSIVE`, `SELECT`, `FROM`, `JOIN`/`LEFT JOIN`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`, `LIMIT`, `UNION`/`UNION ALL`; Cypher `MATCH`, `OPTIONAL MATCH`, `WHERE`, `WITH`, `RETURN`, `ORDER BY`, `LIMIT`, `UNION`/`UNION ALL`, `CALL`, `UNWIND`, `CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`. Clauses, not lines, so wrapping cannot change a score (critique round 2, the major item).\n- `steps`: for SQL, every `FROM` or `JOIN` target in the whole statement, minus one. A target is a table, a view, a CTE name or a parenthesised subquery, each counting once, so a CTE and the same subquery written inline give the same steps (each further target is a join, wherever it sits); for Cypher, relationship patterns in any form (`-[...]->`, `<-[...]-`, `-[...]-`, `-->`, `<--`, `--`), including inside `EXISTS { }`.\n- `moving_parts`, counted symmetrically: for SQL, every `SELECT` beyond the first (each CTE, subquery or union branch), plus `RECURSIVE` and write or DDL statements (`CREATE`, `ALTER`, `DROP`, `INSERT`, `UPDATE`, `DELETE`); for Cypher, every `WITH` stage outside `(...)` and `[...]`, including one inside a `{ }` subquery (as SQL counts a `SELECT` inside a subquery), every subquery (`CALL {`, `EXISTS {`, `COUNT {`, `COLLECT {`) and `UNION`, plus write clauses (`CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`).\n\n`verdict.measured(sql_metrics, cypher_metrics)` scores each side as `clauses + steps + 5 * moving_parts`. It returns `SQL` when SQL's score times 1.25 is at most Cypher's, `graph` when Cypher's score times 1.25 is at most SQL's, and `close` otherwise. It is a pure function with no knowledge of any round, so child d reuses it unchanged (epic critique, item 6). `views.sql` is never scored.\n\n**Measured on the prototype queries** (in the pinned style, scratchpad prototype, 2026-11-21, with this exact rule): round 1 SQL 13 vs Cypher 7, `graph` (expected SQL); round 2 26 vs 21, `close`, 0.25 inside the boundary; round 3 11 vs 7, `graph`; round 4 10 vs 7, `graph`. Re-wrapping round 4's Cypher across more lines left its metrics unchanged. The built files' verdicts are recorded from the runner, not asserted to equal the expected ones; where they differ, the docs and later the page say so.",
      "test": "rounds.test_rounds.RoundTests.test_ac2_measured_verdict_rule (pure: hand-written snippets give known metrics for comma-free joins, a CTE, an IN (SELECT ...) subquery, EXISTS { }, CALL { }, UNION on each side, and bracket-less -->; a correlated EXISTS (SELECT ...) and a derived table count their joins, and a CTE and the same subquery inline give equal steps; UNWIND and a write clause count as clauses; a WITH inside CALL { } counts as a moving part; a query and the same query re-wrapped onto more lines give equal metrics; scores on each side of each 1.25 boundary and exactly on it give SQL, close and graph as stated; the same query written against a per-source UNION ALL and against a view differs only by the union's lines and moving parts, and views.sql is never scored)",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "rounds 1-4 run on the seed-42 SQLite store",
      "then": "each answer equals an **oracle**: an independent Python computation written in the test from the published and reconciled CSVs (not from SQLite), compared as sorted rows. A query returning everything therefore fails. **Scenario checks** (the answer key is read in the test only):\n- round 3's three systems equal `shared_system` exactly, and the oracle's third system has strictly more entities than its fourth;\n- round 2 contains the canonical risk of every `untested_high_risk` IA risk (containment, since the stale set is wider by definition), and its `has_ia_member` flags equal the oracle's;\n- round 4 reaches every regulation (data-model: every regulation reaches a business unit at full size).\n\n**Round 2's inclusive boundary is tested on real data, without editing any store:** take a High canonical risk the oracle marks fresh, and let D be the latest `end_date` among the audits that tested its members' controls. With `cutoff = D` it is out of the answer; with `cutoff = D + 1 day` it is in, and each answer equals the oracle run with the same cutoff. Seed-42 audits never end on the default cutoff, so this is the check of `>=` against `>`. AC-4 runs the same two cutoffs on Neo4j.\n\nThe pre-plan prototype gives, at seed 42, round 1: 61 rows over 121 open issues (21 counted in two units); round 2: 56 of 95 High canonical risks, 41 without an IA member; round 3: SYS-526 (41), SYS-254 (35), SYS-100 (33), with 23 for the fourth; round 4: 133 pairs over all 15 regulations, 773 paths. The docs quote the built module's figures, not these (L-012).",
      "test": "rounds.test_rounds.RoundTests.test_ac3_sqlite_answers_match_oracle_and_scenarios",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "rounds 1-4 run on Neo4j loaded from the same build",
      "then": "each round's Cypher rows equal its SQL rows exactly (**agreement**), after normalising values (integers as `int`, text as `str`) and sorting; round 3 compares its ordered top 3 as a list. Round 2 also agrees at AC-3's two boundary cutoffs (D and D + 1 day), so a `>` in the Cypher fails.\n\n**The guard.** The Neo4j runner refuses with `RoundsError` when the graph has no `LoadComplete` node, or when its checksum differs from `neo4j_store.reconciled_checksum(<dir>)` for the build being queried (not the committed golden file), naming which. That catches a failed load and a graph loaded from a different reconciled build. It does not catch a changed `akg.sqlite` or changed published CSVs (the checksum covers `reconciled/*.csv` only); the docs say so, and AC-5's disagreement test relies on that gap.\n\n**The refusal is tested read-only:** a copy of the build with one byte of one reconciled CSV changed is refused with an error naming the checksum, and the graph's `LoadComplete` checksum is unchanged afterwards. Uses 016's shared `graph()` fixture; skips without `NEO4J_URI` and fails with `AKG_REQUIRE_NEO4J=1`.",
      "test": "rounds.test_rounds.RoundTests.test_ac4_sql_and_cypher_agree_and_the_guard_refuses",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "`python -m akg rounds --out <dir>` runs, or `python -m akg build` reaches its fourth step",
      "then": "for each round it prints the round number, the SQLite row count, the measured verdict, and either the agreement result or \"Neo4j: not run\" when `NEO4J_URI` is unset. `build` runs the rounds after loading; `--no-load` and `--no-reconcile` skip them. The rounds run on the sample build too without error (answers may be small). The export (`rounds.json`) is child d's.\n\n**Exit codes and messages**, each tested:\n- `0`: every round ran on SQLite, and on Neo4j when configured, and all agree.\n- `1`, naming the round(s): both engines ran and a round disagrees.\n- `1`, with `error: ...` naming the reason: `<dir>/akg.sqlite` is missing (\"run `akg load`\"); the guard refused (AC-4); Neo4j is configured but unreachable (naming `NEO4J_URI`, as the loader does). Neo4j being configured and failing is never reported as \"not run\".\n\n**Disagreement is tested for real, not mocked:** a copy of the build whose `akg.sqlite` has one open issue closed (an `UPDATE`) gives a different round 1 on SQLite than on the unchanged graph, and `akg rounds` on that copy, with `NEO4J_*` opted in, exits 1 naming round 1. It only reads Neo4j, so the shared fixture stays valid. The unreachable case points `NEO4J_URI` at a closed port and needs no server.\n\n**The build step is observed directly:** one new `akg build --size sample` subprocess (a few seconds) asserts that the rounds' output follows the load line, and the existing `--no-load` and `--no-reconcile` sample builds in `tests/stores/test_sqlite.py` gain assertions that it is absent.\n\n**Suite cost (L-014):** the rounds run in under 1 s on SQLite at full size (prototype). The only build this change adds is that one sample build. The existing test builds that reach the load step are a handful of full and sample builds; the implementation counts them exactly with grep and records the count in the review.",
      "test": "rounds.test_rounds.RoundTests.test_ac5_cli_exit_codes_and_build_step (SQLite-only, missing-database and unreachable parts run without Neo4j; the disagreement and refusal parts need Neo4j)",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "docs/data-model.md and `src/features/rounds/README.md` are read",
      "then": "they give:\n- rounds 1-4's pinned rules (AC-1), including round 2's inclusive boundary;\n- the shared views and why SQL gets them (Neo4j's shared labels are the same merging);\n- the three checks, and what the Neo4j guard does not cover;\n- the measured-verdict rule with its constants;\n- each round's seed-42 figures and its expected and measured verdicts, taken from running the built module, saying where they differ and naming any round within 1 point of a boundary (round 2 in the prototype).\n\nThe round 2 entry says plainly how many of its canonical risks have no IA member and why they are stale by construction. The round 1 entry says an issue can count in more than one unit, and why (ERM exposure links reach every entity of the owning unit, 10-20% of them stale).",
      "test": "rounds.test_rounds.RoundTests.test_ac6_docs_describe_the_rounds (runs without Neo4j; checks the docs name each round's rule and quote the figures and verdicts the runner computes)",
      "status": "pending"
    }
  ],
  "epic": "003-e3-dual-stores-and-head-to-head-rounds",
  "child": "c"
}
```

## Why
E3 child c (O2). The page's central claim is a head-to-head comparison: the same planning question, asked in SQL and Cypher over the same facts, gives the same answer. This change builds the first four rounds, including the page's first story (shared-system blast radius), and proves each answer three ways: agreement, an independent oracle, and the planted scenario where there is one.

## Data impact
- **No entity, relationship or published or reconciled file changes.** Rounds only read `akg.sqlite` and the Neo4j graph. The SQL views are temporary, made per connection by the runner, and not added to the store schema.
- **Pipeline:** `akg build` gains step 4 (run the rounds) and a new `akg rounds --out` command, matching the epic's pipeline contract. Step 5 (the export) is child d's.
- **Invariants:** relies on INV-8 (the same facts, so agreement compares engines, not data), INV-10 (no cross-source edges, so neither engine filters by source) and INV-5 (audits within the window). INV-6 holds: the rounds never read the answer key; only the tests' scenario checks do.
- docs/data-model.md gains a rounds section (AC-6).

## Test plan
Tests go in `tests/rounds/test_rounds.py`. The SQLite side reuses the cached seed-42 build from `tests.stores.test_sqlite.loaded()`; the Neo4j side uses 016's `graph()` fixture, which reloads only when the checksum differs, and every Neo4j test in this change only reads. No new build. AC-1, AC-2 and AC-6 are pure; AC-3 and the SQLite parts of AC-5 run without Neo4j. The done-check is the full suite run twice, once plain and once under `with_neo4j`, and the criteria are marked from the `with_neo4j` run. Per L-017, the long run goes to a log file in the scratchpad that the reviewer reads.

**Evidence** (pre-plan prototype, 2026-11-21, seed 42, local Neo4j 5.26.33): the SQL and Cypher versions of all four rounds returned identical results (61, 56, the same top 3, and 133 pairs with 773 paths); round 3 equals `shared_system`; round 2 contains all 11 `untested_high_risk` risks' canonical risks. After the critiques, the SQL was rewritten over the shared views in the pinned style, round 2 took the cutoff as a parameter (still 56 rows), and the measured verdicts in AC-2 come from running the pinned clause-count rule on those files.

**Not tested here:** rounds 5-7, owner concentration and `rounds.json` (child d); CI (child e).

## Risks
- **The verdict could measure our schema, not the languages** (critique 1). The shared views give SQL the same ERM-plus-IA merging that Neo4j's labels give Cypher, and they are published as setup, not scored per round.
- **Size metrics are gameable** (critiques 1 and 2). The score counts clauses, not lines, so layout cannot move it; comma joins are banned; joins, subqueries and unions count the same way on both sides; the page publishes the rule with the verdicts.
- **Round 2 sits just inside `close`** (26 vs 21; 26.25 would tip it to `graph`): one more SQL clause flips it. The docs say so rather than tuning the threshold to move it.
- **Round 1's measured verdict (graph) contradicts its expected one (SQL).** That is the honest outcome the epic asked for: Cypher's implicit grouping saves the `GROUP BY` and two joins. Published, not tuned.
- **Round 2 looks alarming** (56 of 95 High risks stale) **because 41 are ERM-only and untestable by construction.** The `has_ia_member` flag and the docs make that visible instead of letting the page overstate it.
- **Slow test runs on this machine (L-017):** the round queries are sub-second; the cost is the existing Neo4j fixture, unchanged.

## Out of scope
- Rounds 5-7, the owner-concentration query and the export: child d.
- Speed comparisons (GOALS non-goal) and query plans or indexes.
- Making the views permanent in `schema.sql` (stores feature, outside these areas); temporary views are enough.
- Parked review minors from 015 and 016 (they stay in the parking lot).

## Relevant lessons
- **L-009** (completeness rule): round 3 is checked for exact equality with `shared_system`, plus the strict third-over-fourth rule; round 2's containment is the epic's stated rule, because the stale set is wider by definition.
- **L-012** (quote the built module): the prototype's figures and verdicts are re-measured by the runner, and the docs quote that.
- **L-014** (count the builds): no test adds a build; the new step adds under 1 s to each existing build that reaches the load step, counted exactly during implementation.
- **L-016** (fingerprints ripple): no fingerprinted file is touched (`train.py`, the reconciliation features), so `weights.json` and `scores.json` stay unchanged.
- **L-017** (low memory): the slow suite runs in the main session to a log file the reviewer reads.
- **L-007, L-008** (generator difficulty and shared phrases): not relevant; this change reads data and changes no text.

## Slices
1. The registry, views, the eight query files and the style test (AC-1).
2. The verdict module (AC-2).
3. The SQLite runner, oracles, scenario and boundary checks (AC-3).
4. The Neo4j runner, agreement and guard (AC-4).
5. CLI and build step (AC-5), then docs (AC-6).
