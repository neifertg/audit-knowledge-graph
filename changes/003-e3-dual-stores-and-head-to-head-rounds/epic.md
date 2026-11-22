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
      "title": "Rounds 5-7, owner concentration and the rounds export",
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
  ],
  "revised": "2026-11-21"
}
```

## Why
O2: the comparison is only credible if both engines hold the same facts and every round's SQL and Cypher return the same answer, proven by tests that CI runs on every push.

## Shape
Two feature folders: `src/features/stores/` (schema, loaders) and `src/features/rounds/` (one `.sql` and one `.cypher` per round, plus the runner). It depends on:
- E1's published files;
- E2's `<out>/reconciled/` (canonical risks and controls, maps-to files, `ia_maps_to_erm`, the review queue);
- research R3 (`research/r3-neo4j-local-and-ci-setup/decision.md`, GO 2026-11-21).

**Pipeline contract (AGENTS.md's Build row).** `python -m akg build` runs, in order:
1. generate;
2. reconcile;
3. load: SQLite always, into `<out>/akg.sqlite`; Neo4j when `NEO4J_URI` is set;
4. run the rounds;
5. export `<out>/rounds.json`.

`--no-reconcile` stops after step 1 (generator tests). `--no-load` stops after step 2 (reconciliation tests). `python -m akg load --out <dir>` and `python -m akg rounds --out <dir>` run steps 3 and 4-5 on an existing build.

Rules:
- **Never the answer key.** Loading reads the published files and `reconciled/`. The stores hold what a bank would hold; tests read the answer key only to check planted scenarios.
- **Idempotent.** Each load clears its store first.
- **Not golden.** The SQLite file and the Neo4j store are derived, so neither is part of any golden.
- **Rounds without Neo4j.** Without `NEO4J_URI`, the rounds run on SQLite only, and the export marks each round's Neo4j side "not run".
- **The committed export.** `src/features/rounds/rounds.json` is the copy E4 reads. It is regenerated with both engines by `python -m src.features.rounds.export` and checked current by a test that runs when Neo4j is available.

**Neo4j environment (R3).**
- Neo4j 5.26.33 LTS Community and `neo4j==6.4.1`, pinned in `requirements.txt` in child b.
- Connection comes from `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD`. Locally a helper bridges them at run time from `~/.claude/secrets.yaml` (`databases.akg_neo4j`), never copied into the repo.
- Every Neo4j test skips when `NEO4J_URI` is unset, **unless `AKG_REQUIRE_NEO4J=1`**, which turns the skip into a failure. CI sets it, so CI cannot go green with the Neo4j tests skipped.
- Tests run sequentially, and the Neo4j store is one shared fixture loaded once per test run from the cached seed-42 build. Two test runs must not share one local server at the same time; the loader takes a lock node and refuses a concurrent load.

**Store parity (INV-8)**, per published file, with the mapping table in docs/data-model.md:
- Every entity file maps to a label, filtered by `source` for per-source files (taxonomy nodes, risks, controls share one label with a `source` property), and its row count equals that node count.
- Every relationship file maps to a relationship type, filtered the same way, and its row count equals that edge count.
- `ia_maps_to_erm` rows with a target become `IA_MAPS_TO_ERM` edges. `unmapped` rows become a `mapping: 'unmapped'` property on the IA node; their SQLite column is NULL, so no foreign key breaks. Mapped edges plus unmapped flags equal the rows.
- Review-queue rows become `REVIEW_CANDIDATE` edges carrying `kind`, `logit`, `reason` and `drivers`.
- One sampled row per file has matching properties in both stores.

**Verdicts are measured, not assumed.** Each round's "expected verdict" below is a hypothesis written before the queries exist. The export also carries a **measured verdict** from a rule child c's plan pins: lines of code, joins against hops, and the moving parts each engine needs (recursive CTEs, new tables, schema changes). *(Superseded, see the revision: clauses rather than lines, and made symmetric in 018 by owner decision.)* The page publishes the measured verdict. Where it differs from the expected one, the page says so; that is part of the honest comparison.

**Every round is checked three ways:**
1. *Agreement:* the SQL and Cypher answers are identical rows, after normalising and sorting.
2. *Oracle:* the answer equals an independent Python computation from the CSVs, written in the test, so a query that returns everything cannot pass.
3. *Scenario:* where E1 planted a scenario, the answer finds exactly it (the scenario file is read in the test only).

**Children:**
- **a. SQLite schema and loader (1 day).** Areas: `src/features/stores/**`, `tests/**`, `docs/data-model.md`, `akg/**`.
  - `stores/schema.sql`: one table per entity file and per relationship file, plus the reconciled layer (including the review queue). Primary and foreign keys follow the data dictionary.
  - The loader, the `load` step of `akg build`, `akg load`, and the `--no-load` flag. The reconciliation test helpers move to `--no-load`.
  - Tests: every CSV row lands exactly once; foreign keys hold; reloading is idempotent; the answer key is never loaded.
- **b. Neo4j loader with fact parity (1 day).** Areas: as a, plus `requirements.txt`.
  - Graph model: one label per entity, with a `source` property on per-source types; one relationship type per relationship file; `CanonicalRisk` and `CanonicalControl` nodes, `MAPS_TO`, `IA_MAPS_TO_ERM` and `REVIEW_CANDIDATE`.
  - Batched `UNWIND` loading with uniqueness constraints and a load lock. The lock node carries a timestamp, a lock older than 10 minutes is treated as stale and replaced, and the lock is excluded from parity counts.
  - The INV-8 parity test above; the env helper; `AKG_REQUIRE_NEO4J`; pinning `neo4j==6.4.1`.
- **c. Rounds 1-4 (1.5 days).** Areas: `src/features/rounds/**`, `tests/**`, `docs/data-model.md`, `akg/**`. Each round is one `.sql`, one `.cypher` and the three checks. Exact attribution and path rules are pinned in c's plan.
  1. *Open issues by business unit and rating* (expected verdict: SQL). An issue is attributed to the business units that own the auditable entities exposed to the risk it is against.
  2. *High risks with stale coverage,* on canonical items (expected verdict: close).
     - A canonical risk is High when any of its member source risks is rated High.
     - A control has stale coverage when it was never tested in the window (2023-01-01 to 2025-12-31, E1's audit years), or last tested more than 24 months before 2025-12-31.
     - A canonical risk qualifies when it is High and none of the controls mitigating its members was tested in time.
     - The oracle gives the exact set. The scenario check is containment, because the stale set is wider by definition: every `untested_high_risk` IA risk's canonical risk is in the answer.
  3. *Shared-system blast radius* (expected verdict: graph): the 3 systems whose dependent controls reach the most auditable entities, through control, mitigates, risk and exposed entity, over both sources. It must equal `shared_system`, with E1's tie rule. This is the page's first story.
  4. *Every path from a regulation to a business unit* (expected verdict: graph): regulation, requires control, mitigates risk, exposed entity, owned by business unit. The answer is the distinct (regulation, business unit) pairs with their path counts.
- **d. Rounds 5-7, the supporting query and the export (1.5 days).** Areas: as c.
  5. *A third-party register arrives* (expected verdict: graph).
     - The new data: `system.csv` already names each system's vendor. Round 5 adds what is new, a deterministic overlay of **fourth-party dependencies** (vendor relies on vendor), drawn from E1's fictional vendor list (`names/vendors.txt`, INV-9).
     - The question: which auditable entities are exposed to a given critical vendor, directly through its systems or through a chain of fourth parties? The answer marks which are newly exposed through fourth parties only, against the direct-only baseline.
     - Effort: SQL needs a new table and a recursive CTE; the graph needs new nodes and edges and a variable-length path.
     - Isolation: both stores apply the overlay inside an explicit transaction (SQLite opens it with `BEGIN`, since Python's sqlite3 otherwise commits DDL) and roll it back. A test checks that both stores' counts and INV-8 parity are identical before and after round 5. *(Superseded, see the revision: a TEMP table on a read-only connection inside `BEGIN` ... `ROLLBACK`, and a full Neo4j snapshot plus the SQLite file's hash compared before and after, on success and on failure.)* The vendor asked about and the overlay's construction are pinned in d's plan.
  6. *Repeat finding in disguise* (expected verdict: close; in SQL it is one join and a group by year; replaces "why is this audit on the plan", which had no forward-plan data; owner decision 2026-11-21): IA controls with issues in two or more years under different titles, and their issue groups. It must equal the planted `repeat_finding` groups exactly; E1 guarantees that the listed groups are all such controls. This is the page's second story.
  7. *Year-over-year finding trend by ERM L1* (expected verdict: SQL), counted like `rising_category`: regulator, self-identified and 2nd-line issues on the published ERM taxonomy, with IA issues excluded. The top riser (the largest 2023-to-2025 increase in issues opened, with E1's thresholds) must equal `rising_category`. "Tested" in round 2 uses the audit's end date; c's plan pins both rules exactly.

  *Supporting query (not a scored round):* **owner concentration**. For each person, it counts the key controls (`key_control = Y`, both sources) they own and the distinct business units those controls' risks reach (control, mitigates risk, exposed entity, owning unit). It ranks by key controls, then business units, then person ID, so ties are broken deterministically. It has agreement and oracle checks. This is the page's third story; it is derived, not a planted scenario, and the page must say so (E4 needs a matching revision).

  *The export:* `rounds.json`. For each round it holds:
  - the question and both queries;
  - lines of code, and the join or hop count *(as built: lines plus the full metrics, scores and margin per side; see the revision)*;
  - a readability note and the expected verdict;
  - the result: row count and up to 20 rows;
  - the agreement, oracle and scenario outcomes;
  - the engines run, the expected and measured verdicts;
  - and, once for the file, the seed, the build's reconciled-golden checksum and the weights fingerprint.

  The supporting query's result is included too. No speed claims (GOALS non-goal).
- **e. GitHub repo and CI with a Neo4j service container (1 day).** Areas: `tests/**`, `docs/**`, plus governance files the owner commits.
  - The owner confirms visibility (public, per GOALS), then creates the repo and pushes main from one copy-paste block. This child creates the repo; E4's publishing child then only turns on Pages (E4 needs a matching revision before its children are planned).
  - A GitHub Actions workflow (in `.github/`, governance, owner-committed through allow-governance from a copy-paste block). It runs the full suite on push and pull request, with:
    - a `neo4j:5.26.33-community` service container and a readiness wait;
    - the `NEO4J_*` env and `AKG_REQUIRE_NEO4J=1`;
    - no secrets.
  - Done when the first runs are green and the Neo4j tests ran, not skipped.

**Test-suite time** (L-014): child a's plan counts every build a store test adds, and store tests reuse the cached seed-42 build.

## Revision 2026-11-21: what the children built (closing E3)
All five children are done: a (015), b (016), c (017), d (018) and e (019). Where they diverged from the shape above, the owner decided at each child's approval or in the conversation recorded in its plan. This section records the divergences and the results:
- **SQLite store** (015) as planned: `schema.sql` is generated from the two data dictionaries; 10,034 rows load in about 1.4 s at seed 42.
- **Neo4j store** (016). The graph is derived from the schema metadata and loaded from `akg.sqlite` (not the CSVs), so both stores come from the same typed rows: 2,821 nodes and 7,495 edges in about 10 s. A `LoadComplete` node holds the reconciled checksum, and the rounds refuse a graph without it or with another build's checksum. The guard does not detect a changed `akg.sqlite` or changed published CSVs (the checksum covers `reconciled/*.csv` only; stated in docs/data-model.md, and 017's disagreement test relies on it). The load lock covers loading only, so **concurrent local test runs on one server are unsupported** (stated in the stores README); CI runs one job per container.
- **Shared SQL views** (017, from its critique; not in the shape above). `views.sql` merges the ERM and IA tables of each kind as eight temporary views, the analogue of Neo4j's shared labels, so a verdict compares languages, not the one-table-per-source schema. They are shared setup, published once and never scored.
- **The measured-verdict rule** (017, then 018). 017 pinned `clauses + steps + 5 * moving_parts` with a 1.25 margin, counting clauses rather than lines so layout cannot move a score. **Owner decision (2026-11-21, during 018's critique): make it symmetric** — a SQL join counts once, a Cypher `*n` counts n hops, recursion counts once per side, a round with setup is scored as setup plus query. Rounds 1-4 were re-measured, and the export publishes each round's margin from the line. A remaining asymmetry was found in 018's review and parked (see below).
- **Round 5** (018). The register is `fourth_party.csv`, 8 generated rows from the fictional vendor list (`random.Random('fourth-party-v1')`); the vendor asked about is the one most vendors rely on (Ivelle Financial Technology); direct exposure is the operational path (entity, process, system, vendor). Isolation uses a TEMP table on a read-only SQLite connection inside `BEGIN` ... `ROLLBACK`, rather than a transaction on the store, and one rolled-back Neo4j transaction with no schema change; Neo4j keeps the new label and type names in its token store, while all data is unchanged, tested on success and on failure.
- **Round 7's top riser** is derived in Python from the agreed rows (largest 2025 minus 2023 increase), not by a query.
- **The export** (018). Scenario outcomes are claims naming the test that verifies them, because only tests read the answer key; `oracle.py` (moved from the tests) reports the oracle check for real. The export has no timings and no paths. The committed `src/features/rounds/rounds.json` is regenerated by `python -m src.features.rounds.export` with Neo4j configured.
- **Results at seed 42** (SQL vs Cypher score, measured verdict, expected verdict): round 1, 9 vs 7, `graph` (SQL); round 2, 21 vs 21, `close` (close); round 3, 8 vs 7, `close` (graph); round 4, 7 vs 7, `close` (graph); round 5, 29 vs 46, `SQL` (graph); round 6, 17 vs 12, `graph` (close); round 7, 10 vs 8, `graph` exactly on the line (SQL); owner concentration, 10 vs 9, `close`. **Six of the seven measured verdicts differ from the expected ones**; rounds 1, 3 and 7 are within one point of the line. Every scenario check holds: round 3 equals `shared_system`, round 2 contains every `untested_high_risk`, round 6 equals the planted `repeat_finding` groups, round 7's riser is `rising_category` (Credit, 8 to 13).
- **Owner concentration is derived, not planted** (as the epic said), and the export marks it supporting.
- **The repository and CI** (019). `neifertg/audit-knowledge-graph` is public; the history was audited before the first push (no secret patterns in any commit, one noreply email, largest blob 0.6 MB). `.github/workflows/tests.yml` runs all 103 tests on every push and pull request against a `neo4j:5.26.33-community` service container, with no secrets and `AKG_REQUIRE_NEO4J=1`, and fails on any skip. The first runs were green in about 4 minutes, with no Linux-only failure and no golden drift: on the change branch (https://github.com/neifertg/audit-knowledge-graph/actions/runs/44981150868, suite 170 s) and on main after the merge (https://github.com/neifertg/audit-knowledge-graph/actions/runs/44982451692, suite 176 s, job 4 min 7 s). `docs/ci.md` records the first; the main run is recorded here. A CI-environment leak (`akg_env` passed `AKG_REQUIRE_NEO4J` to test subprocesses) was found by the critique and fixed before the first run. A short top-level README and `docs/ci.md` were added; `data/` is ignored.
- **Test-suite time:** 103 tests; locally 227-421 s plain (018's and 019's logged runs) and 500-970 s under Neo4j on the owner's 7.6 GB laptop (L-017), 170-176 s in CI.
- **Before E4 publishes** (parked, ROADMAP): the verdict rule still charges a Cypher write clause as a clause and a moving part, while SQL's write counts once (round 5's Cypher side would be 41, not 46; the verdict stays `SQL`); fix it or disclose it beside the `OPTIONAL MATCH` note, and correct docs/data-model.md's line saying "writes and DDL count on both sides", which overstates the symmetry until then. E4's epic revision is also parked: owner concentration is derived, the repository already exists (E4 child c only turns on Pages), and the page shows measured verdicts beside expected ones.
- **Parked from the children's reviews** (ROADMAP): clearer errors and guard cases in the loaders, a stale `akg.sqlite` left beside new CSVs after a failed build (015), `akg rounds` exiting 0 on a failed oracle check, two rare Cypher path-length forms, the export finding round 5 by position, round 5's Cypher setup failing on a system with no vendor (none at seed 42), and the CI doc test's checks.
- **Resolved by this epic** (still listed in ROADMAP's parking lot from 2026-11-19): round 2 uses E1's stale-coverage definition (017); round 2 runs on canonical items (017); round 5 brings its fourth parties from the existing fictional vendor list, so E1 needed no new list (018).
- L-016 to L-020 (from E3's children): grep every copy of a fingerprint before editing its source; reviewers must not wait on long runs on a low-memory machine; measure a published metric on the prototypes before approval; audit a scoring rule's symmetry as a table of constructs; a CI test must not require evidence of its own run.

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
