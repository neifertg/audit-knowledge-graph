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
      "depends_on": [
        "a"
      ]
    },
    {
      "key": "c",
      "title": "Rounds 1-4: paired SQL and Cypher with agreement tests",
      "depends_on": [
        "b"
      ]
    },
    {
      "key": "d",
      "title": "Rounds 5-7 and the rounds export",
      "depends_on": [
        "c"
      ]
    },
    {
      "key": "e",
      "title": "GitHub repo and CI with a Neo4j service container",
      "depends_on": [
        "b"
      ]
    }
  ]
}
```

## Why
O2: the comparison is only credible if both engines hold the same facts and every round's SQL and Cypher return the same answer, proven by tests that CI runs on every push.

## Shape
Two feature folders: `src/features/stores/` (schema, loaders) and `src/features/rounds/` (one `.sql` and one `.cypher` per round, plus the runner). It depends on:
- E1's published files;
- E2's `<out>/reconciled/` (canonical risks and controls, maps-to files, `ia_maps_to_erm`, the review queue);
- research R3 (`research/r3-neo4j-local-and-ci-setup/decision.md`, GO 2026-11-21).

**Loading contract.** `python -m akg load --out <dir>` loads a built and reconciled directory into a SQLite file (`<out>/akg.sqlite`) and, when `NEO4J_URI` is set, into Neo4j. It loads the published entity and relationship files and the reconciled layer, **never the answer key** (the stores hold what a bank would hold; tests read the answer key only to check that rounds find planted scenarios). The load is idempotent: each load clears its store first. `akg build` does not load: Neo4j needs a running server, and the SQLite file is a derived artifact, so neither is part of any golden.

**Neo4j environment (R3).**
- Neo4j 5.26.33 LTS Community and `neo4j==6.4.1`, pinned in `requirements.txt` in child b.
- Connection comes from `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD`. Locally a helper bridges them at run time from `~/.claude/secrets.yaml` (`databases.akg_neo4j`), never copied into the repo.
- Every test that needs Neo4j skips when `NEO4J_URI` is unset. In CI it is always set, so those tests always run there.

**Children:**
- **a. SQLite schema and loader (1 day).** Areas: `src/features/stores/**`, `tests/**`, `docs/data-model.md`, `akg/**`.
  - `stores/schema.sql`: one table per entity file and per relationship file, plus the reconciled layer. Primary and foreign keys follow the data dictionary, and sources stay separate as published.
  - The loader and the `akg load` command (SQLite part).
  - Tests: every CSV row lands exactly once; foreign keys hold; reloading is idempotent; the answer key is never loaded.
- **b. Neo4j loader with fact parity (1 day).** Areas: as a, plus `requirements.txt`.
  - Graph model: one label per entity, with a `source` property on taxonomy nodes, risks and controls; one relationship type per relationship file, named after it. The reconciled layer adds `CanonicalRisk` and `CanonicalControl` nodes, `MAPS_TO` edges and `IA_MAPS_TO_ERM`.
  - Batched `UNWIND` loading with uniqueness constraints (R3: about 2 s for 1,000 nodes).
  - The INV-8 parity test: every table's row count equals its label's node count or its relationship type's edge count, and one sample of properties matches per type.
  - The local env helper, and pinning `neo4j==6.4.1`.
- **c. Rounds 1-4 (1.5 days).** Areas: `src/features/rounds/**`, `tests/**`, `docs/data-model.md`. Each round is one `.sql` and one `.cypher` file answering the same question, with an agreement test: both return the same rows, normalised and sorted. Where E1 planted a scenario, a test also checks the answer finds it, reading `answer_key/scenarios.csv` in the test only.
  1. Open issues by business unit and rating (expected verdict: SQL).
  2. High risks whose controls have **stale coverage**: never tested in the 3-year window, or last tested more than 24 months before the window ends (E1's definition). It runs on canonical risks and controls, because audits test only IA controls and ERM-only items are untested by construction. Checked against `untested_high_risk` (expected verdict: close).
  3. Shared-system blast radius: the 3 systems whose dependent controls reach the most auditable entities. Checked against `shared_system` (expected verdict: graph).
  4. Every path from a regulation to a business unit (expected verdict: graph).
- **d. Rounds 5-7 and the rounds export (1.5 days).** Areas: as c.
  5. Add third-party vendors live. A deterministic vendor overlay, drawn from E1's fictional vendor list (`names/vendors.txt`, INV-9), with vendors supplying systems. It is added at run time to both stores, showing what each needs (a new table plus a join table and query changes, against new nodes and edges with an unchanged schema). The answer is the auditable entities newly exposed through a vendor (expected verdict: graph).
  6. "Why is this audit on the plan": the path from a planned audit to its high risks, controls and findings (expected verdict: graph).
  7. Year-over-year finding trend by ERM L1, counted like `rising_category` (regulator, self-identified and 2nd-line issues on the published ERM taxonomy; IA issues excluded). Checked against `rising_category` (expected verdict: SQL).

  The export: `src/features/rounds/rounds.json` for E4, holding each round's question, both queries, lines of code, join or hop count, a readability note, the expected verdict and the agreement result. A test keeps it current. No speed claims (GOALS non-goal).
- **e. GitHub repo and CI with a Neo4j service container (1 day).** Areas: `tests/**`, `docs/**`, plus governance files the owner commits.
  - The owner creates the public GitHub repo and pushes main, from one copy-paste block (R3: there is no remote yet).
  - A GitHub Actions workflow (in `.github/`, governance, owner-committed through allow-governance from a copy-paste block). It runs the full suite on push and pull request, with a `neo4j:5.26.33-community` service container, a readiness wait and `NEO4J_*` env set, and no secrets.
  - Done when the first runs are green with the Neo4j tests actually running, not skipped.

**Test-suite time** (L-014): child a's plan counts every build a store test adds, and store tests reuse the cached seed-42 build.

## Out of scope
- Scaling benchmark and centrality analysis: M2.
- Neo4j Graph Data Science plugin: not needed for M1.

## Relevant lessons
- L-006 (frozen goldens): loading never writes into generator or reconciled output; stores are derived and not golden.
- L-012 (quote the built module): round results and counts come from running the queries, recorded in the export.
- L-014 (count the builds a step adds): store and round tests reuse the cached build; Neo4j tests skip locally without `NEO4J_URI`.
- L-001 (owner commands are copy-paste blocks): repo creation and the governance workflow commit in child e.

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard ...).
Children with no unmet depends_on can run in parallel, one branch/worktree each.
