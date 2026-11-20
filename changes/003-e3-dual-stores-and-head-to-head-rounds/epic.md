# E3 Dual stores and head-to-head rounds

```json plan
{
  "id": "003-e3-dual-stores-and-head-to-head-rounds",
  "tier": "epic",
  "status": "draft",
  "created": "2026-11-19",
  "objective": "O2",
  "children": [
    {
      "key": "a",
      "title": "SQLite schema and loader",
      "depends_on": []
    },
    {
      "key": "b",
      "title": "Neo4j loader with fact parity",
      "depends_on": ["a"]
    },
    {
      "key": "c",
      "title": "Seven head-to-head planning rounds",
      "depends_on": ["b"]
    },
    {
      "key": "d",
      "title": "CI with a Neo4j service container",
      "depends_on": ["b"]
    }
  ]
}
```

## Why
O2: the comparison is only credible if both engines hold the same facts and every round's SQL and Cypher return the same answer, proven by tests that CI runs on every push.

## Shape
- `src/features/stores/` (schema, loaders) and `src/features/rounds/` (paired `.sql`/`.cypher` per round). Depends on E2 (reconciled data).
- **a:** `stores/schema.sql` and a loader for generator plus reconciliation output.
- **b:** Neo4j loader (setup per research R3); a parity test that row counts reconcile with node and edge counts (INV-8).
- **c:** the 7 rounds: (1) open issues by unit and rating, SQL wins; (2) high risks with controls untested 3+ years, close; (3) shared-system blast radius, graph; (4) every path from a regulation to a business unit, graph; (5) add third-party vendors live, graph; (6) "why is this audit on the plan" path explanation, graph; (7) year-over-year finding trend, SQL wins. Each round: an agreement test, plus lines of code, join count and readability notes exported for the page. No speed claims.
- **d:** a GitHub Actions job with a Neo4j service container that runs the full test suite, including the Neo4j tests. No secrets.

## Out of scope
- Scaling benchmark and centrality analysis: M2.
- Neo4j Graph Data Science plugin: not needed for M1.

## Relevant lessons
- None yet (new project).

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard ...).
Children with no unmet depends_on can run in parallel, one branch/worktree each.
