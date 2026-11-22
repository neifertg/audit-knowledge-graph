VERDICT: READY

Round 4 critique. Round-3 items (all minor, all in AC-2):
- 1 (clause keyword sets): answered. AC-2 now lists the full sets. The Cypher set includes `CALL`, `UNWIND` and the writes (`CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`). It says the sets are wider than AC-1's layout list, so child d's writes score under the same rule. I checked both sets against the prototype's `SQL_CLAUSES` and `CY_CLAUSES` in `metrics2.py` and they match exactly. The AC-2 test now names "UNWIND and a write clause count as clauses".
- 2 (`WITH` inside `{ }`): answered. A `WITH` inside a `{ }` subquery counts as a moving part, the same way SQL counts a `SELECT` inside a subquery. This matches the prototype, whose `top_level()` does not blank braces. The test names the `CALL { }` case. It also fits the clause rule, which excludes only `(...)` and `[...]`.
- 3 (CTE vs inline derived table): answered. A target is now "a table, a view, a CTE name or a parenthesised subquery, each counting once". Worked through for round 2's shape: the CTE form has targets audit-chain + `risk_maps_to_canonical` + `risk` + `fresh`, and the inline form swaps `fresh` for `(SELECT ...)`. The step counts are equal, and the moving parts are equal too (one extra `SELECT` either way). The test names "a CTE and the same subquery inline give equal steps".

No new issues from the edits:
- The steps rule moved away from the prototype in one place. The prototype's regex `(?:FROM|JOIN)\s+\w+` does not count `FROM (`, and the plan's rule does. I checked whether this moves the "measured with this exact rule" figures. None of the eight prototype query files has a derived table: the only `(` that opens a subquery is round 2's `WITH fresh AS (`, which is a CTE. So R1 13/7, R2 26/21, R3 11/7 and R4 10/7 still hold under the revised rule. Round 2 stays 0.25 inside `close`, as Risks and AC-6 already say.
- Counting symmetry still holds. In SQL, `UNION` is a clause and the extra `SELECT` is a moving part. In Cypher, `UNION` is a clause and also a moving part. That is the settled design from round 2, not re-raised.

Not checked: I did not query Neo4j or run the test suite (L-017). I did not re-run `metrics2.py`; my check of the figures rests on reading the prototype files for derived tables, plus round 3's run of the script.
