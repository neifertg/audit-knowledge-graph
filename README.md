# Audit knowledge graph

## Executive summary

A reconciled map of risks, controls, owners, issues, audits, and systems lets second-line risk and third-line internal audit follow how the ERM register and Internal Audit's matrices connect. This project loads that map into a graph and into SQL and asks the same planning questions in both. The answers match. A graph can make some of those multi-step paths shorter to write; a spreadsheet, a GRC query, or SQL can return the same facts. The comparison here is query size, not ease of use or speed.

On a synthetic US regional bank (invented names; not any employer's data): 56 reconciled risks that include a high-rated member had no mitigating control tested by an audit ending on or after 2023-12-31, 24 months before the end of the data window. 41 have no Internal Audit member and are untested by construction; the other 15 are coverage candidates. 6 controls failed in different years under different titles: 14 issues, linked through the control and the dates. If Ylvara Data Warehouse fails, 44 controls that depend on it are affected; between them they protect risks in 41 auditable entities across 20 business units, which argues for a cross-unit review of that system. Dorothea Sandoval and Greer Kowalczyk each own 9 key controls whose risks reach 7 business units; that tie was computed from the data, not planted.

The warehouse, repeat-finding, and stale-coverage examples are planted. The graph took a smaller query in three rounds, SQL in one, and three were close. One synthetic bank, one generator, small samples. The graph informs auditor judgment; it does not score risk or set the audit plan.

[https://neifertg.github.io/audit-knowledge-graph/](https://neifertg.github.io/audit-knowledge-graph/)

## The brief

The [public page](https://neifertg.github.io/audit-knowledge-graph/) has each finding below with the figures behind it, and it draws the warehouse dependency as a graph you can click through. The data sits in SQLite and in Neo4j. The [methods page](https://neifertg.github.io/audit-knowledge-graph/methods.html) has the scoring rule, both queries for every round and the data inventory. [docs/pages.md](docs/pages.md) explains how the page is published.

[![tests](https://github.com/neifertg/audit-knowledge-graph/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/neifertg/audit-knowledge-graph/actions/workflows/tests.yml)

A model wrote the descriptions in the data once, ahead of time, and they are committed. The Credit increase below is one of the planted test cases too; the queries are checked against all of them.

### Cover the shared warehouse across units

Ylvara Data Warehouse reaches more auditable entities than any other shared system. If it fails, 44 controls that depend on it are affected, and those controls protect risks in 41 auditable entities across 20 business units. Plan the coverage as one review of the system across those units, not as a review owned by one of them.

### Escalate the repeat-control findings

6 controls failed in different years: 14 issues with different titles, linked through the control and the dates. Treat them as one escalating group.

### Review concentrated ownership

Dorothea Sandoval and Greer Kowalczyk each own 9 key controls whose risks reach 7 business units. Nobody planted this tie; it came out of the data. It calls for a key-person review.

### Fourth-party vendor exposure

A register of which vendors rely on which others puts 17 auditable entities in reach of Ivelle Financial Technology, the vendor that the most others rely on, directly or further out (ties broken by name). 5 of them perform a process that runs on a system Ivelle supplies. The other 12 are exposed only through another vendor's reliance.

### High risks with stale coverage

56 reconciled risks include a high-rated member and had no mitigating control tested by an audit ending on or after 2023-12-31, 24 months before the end of the data window. (A reconciled risk is the canonical item that groups the ERM and Internal Audit records for the same risk.) 41 of the 56 have no Internal Audit member, and audits here test only IA controls, so those 41 could never have been tested. The other 15 are the coverage candidates.

### Findings by ERM category

Counting regulator, self-identified and second-line issues by top-level ERM category and year (Internal Audit's own issues left out), Credit rose the most from 2023 to 2025: 8 issues in 2023, 10 in 2024 and 13 in 2025. The other categories were flat or down, and each year's total was 42.

### Graph or SQL

Both answered the same 7 planning questions over the same facts, and their answers were checked equal. On query size, SQL wins 1, the graph 3, and 3 are close. The comparison measures how much query each needs, not how fast it runs.

### What was merged, and what is waiting

The matcher merges a pair on its own only above a training-bank precision target of 0.95. Merged precision is 33/33 for risks and 68/68 for controls; merged recall is 33/103 for risks and 68/245 for controls. If a reviewer resolves the queue correctly, recall rises to 101/103 for risks and 240/245 for controls. The 482 pairs in the review queue wait for a person, which is where most true matches end up under these conservative thresholds.

## How to read these numbers

- Every figure comes from the committed results for seed 42, and `python -m akg build` reproduces them. On the page, each figure is marked with the file it came from.
- The rounds compare how much query each language writes. Nothing here measures speed or scale. Rounds 1, 3 and 7 sit within a point of the decision line, so one more clause would flip their verdict.
- The thresholds favour precision over recall on purpose: what the matcher does not merge goes to the review queue for a person to decide.

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
