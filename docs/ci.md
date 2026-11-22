# CI

`.github/workflows/tests.yml` (E3 child e, change 019) runs the **full** test suite on every push and pull request, on `ubuntu-latest` with Python 3.12 and the pinned `requirements.txt`, against a real Neo4j.

## Design

- **A Neo4j service container:** `neo4j:5.26.33-community`, the research R3 pin, with heap capped at 1 GB and page cache at 512 MB. It lives only for the job.
- **Neo4j readiness:** a `cypher-shell` health check on the container, then a readiness step that retries a driver connection for up to 120 s and, if Neo4j never comes up, fails with the last connection error (so a wrong password, a refused connection and a crashed container are told apart).
- **No secrets.** The Neo4j password is a throwaway literal for the job-local container; the workflow references no `secrets.` at all, so pull requests from forks run the same suite safely.
- **No skips.** `AKG_REQUIRE_NEO4J=1` turns every Neo4j skip into a failure, and a last step fails the job if the unittest summary line reports anything `skipped`. Test subprocesses get neither `NEO4J_*` nor `AKG_REQUIRE_NEO4J` unless a test opts in (`tests/generator/helpers.akg_env`), so builds inside tests never touch the shared graph.
- `permissions: contents: read`, a 45-minute timeout, and one run per ref at a time.

## First run

(Recorded after the first green run on the change branch: run URL, wall time, test count.)

## Reproduce CI locally

With a local Neo4j running (R3), export CI's environment and run the suite the way CI does:

```
$env:AKG_REQUIRE_NEO4J = "1"
.venv\Scripts\python -m src.features.stores.with_neo4j -m unittest discover -s tests
```

A summary line of `OK` with no `skipped=` is what CI requires.
