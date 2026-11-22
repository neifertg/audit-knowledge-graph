# Audit knowledge graph

**The page:** https://neifertg.github.io/audit-knowledge-graph/ (how it is published: [docs/pages.md](docs/pages.md))

[![tests](https://github.com/neifertg/audit-knowledge-graph/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/neifertg/audit-knowledge-graph/actions/workflows/tests.yml)

A synthetic US regional bank's Enterprise Risk Management and Internal Audit data, generated with two separate risk taxonomies, reconciled into one framework, and loaded into SQLite and Neo4j side by side. Seven audit-planning questions are then asked in both SQL and Cypher, and every answer is proved three ways: the two engines agree, an independent Python computation agrees, and the planted scenario is found. Everything is synthetic and every number is reproducible from a fresh clone.

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
- `src/features/`: `generator`, `reconciliation`, `stores`, `rounds` (each with its own README).
- `src/features/rounds/rounds.json`: every round's queries, scores, verdicts and checks, as published.
