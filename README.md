# Audit knowledge graph

## The brief

A synthetic US regional bank keeps its risks in the ERM register and in Internal Audit's risk and control matrices. Both lists were reconciled into a single framework, loaded into SQLite and Neo4j, and asked the same planning questions. The public page is that brief:

**https://neifertg.github.io/audit-knowledge-graph/**

The scoring rule, both queries and the inventory are on the [methods page](https://neifertg.github.io/audit-knowledge-graph/methods.html). How the page is published: [docs/pages.md](docs/pages.md).

[![tests](https://github.com/neifertg/audit-knowledge-graph/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/neifertg/audit-knowledge-graph/actions/workflows/tests.yml)

Synthetic data throughout. Descriptions were written by a model ahead of time and committed. Names and companies are invented. This is not any employer's data.

The warehouse, repeat-finding, stale-coverage, and Credit-increase examples are planted test cases used to check the queries; the ownership tie was not planted.

**Cover the shared warehouse across units.** Ylvara Data Warehouse is the shared system that reaches the most auditable entities. If it fails, 44 controls that depend on it are affected; between them they protect risks in 41 auditable entities across 20 business units. Schedule the coverage as a review of that system across units. The page draws the dependency.

**Escalate the repeat-control findings.** 6 controls failed in different years under different titles: 14 issues with different titles, linked through the control and the dates. Escalate the group.

**Review concentrated ownership.** Dorothea Sandoval and Greer Kowalczyk each own 9 key controls whose risks reach 7 business units. That tie was computed from the data; it was not planted. Schedule a key-person review of that ownership.

**Fourth-party vendor exposure.** With a register of which vendors rely on which others, 17 auditable entities are exposed to Ivelle Financial Technology. It is the vendor the most others rely on, directly or further out, with ties broken by name. 5 perform a process that runs on a system that vendor supplies. 12 appear only through another vendor's reliance.

**High risks with stale coverage.** 56 reconciled risks (the 'canonical' items that group the ERM and Internal Audit records for the same risk) include a high-rated member and had no mitigating control tested by an audit ending on or after 2023-12-31, 24 months before the end of the data window. 41 of the 56 have no Internal Audit member, and because audits here test only IA controls, those 41 are untested by construction. The remaining 15 are the coverage candidates.

**Findings by ERM category.** Regulator, self-identified and second-line issues (Internal Audit issues excluded), counted by top-level ERM category and by year. The largest increase, measured as 2025 minus 2023, is Credit, which rose from 8 issues in 2023 to 10 in 2024 and 13 in 2025. The other categories were flat or down, and each year's total was 42.

**Does a graph beat SQL?** Asked 7 planning questions in both, with the same facts and answers proved equal. SQL wins 1, the graph 3, and 3 are close. That comparison is query size, not speed.

**What was merged, and what is waiting.** Auto-merge uses a training-bank precision target of 0.95. Merged precision is 33/33 for risks and 68/68 for controls. Merged recall is 33/103 for risks and 68/245 for controls. If a reviewer resolves the queue correctly, recall would be 101/103 for risks and 240/245 for controls. The review queue holds 482 pairs. The matcher's thresholds are deliberately conservative, so most true matches wait in the review queue rather than being merged silently.

The graph informs auditor judgment; it does not score risk or set the audit plan.

## How to read these numbers

- Every figure above is taken from the committed results for seed 42. `python -m akg build` reproduces them. On the page, each figure is marked with the file it came from.
- "SQL" and "graph" compare how much query each language writes, not how fast it runs. No speed or scale claim is made. Rounds 1, 3 and 7 sit within a point of the decision line, so a single extra clause would change their verdict.
- The matcher auto-merges only at the training precision above. High merged precision and low merged recall are the setting that was chosen. The review queue is the rest, for a person to decide.
- The bank, the people and the vendors are fictional. The graph does not score risk or write the plan.

## Reproduce

Python 3.12:

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # Linux/macOS: .venv/bin/pip
python -m akg build                                # generate -> reconcile -> load -> rounds -> rounds.json, into data/
python -m unittest discover -s tests               # the full suite
```

The build never calls an API: the AI-written descriptions were generated once and are committed.

## Neo4j

The Neo4j tests skip unless `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD` are set; with `AKG_REQUIRE_NEO4J=1` a skip becomes a failure. Point them only at a database dedicated to this project, because a load replaces its contents. Locally (Neo4j 5.26 Community, see `research/r3-neo4j-local-and-ci-setup/decision.md`), the owner's helper bridges the connection from `~/.claude/secrets.yaml`:

```
python -m src.features.stores.with_neo4j -m unittest discover -s tests
```

CI runs every test, Neo4j included, on every push and pull request, against a Neo4j service container and with no secrets: see [docs/ci.md](docs/ci.md).

## Where things are

- `GOALS.md`: objectives, current milestone, non-goals.
- `docs/data-model.md`: entities, invariants, the reconciliation and the rounds, with measured figures.
- `src/features/`: `generator`, `reconciliation`, `stores`, `rounds`, `site` (each with its own README). The public brief is `src/features/site/template.html`; the methods page is `src/features/site/methods.html`.
- `src/features/rounds/rounds.json`: every round's queries, scores, verdicts and checks, as published.
