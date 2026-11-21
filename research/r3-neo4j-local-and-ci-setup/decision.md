# Research: R3 Neo4j local and CI setup

Objective: O2
Question: Does Neo4j Desktop on Windows (bundled Java; local Java 11 is too old for Neo4j 5) work with the Python `neo4j` driver, and does a Neo4j 5 Community service container in GitHub Actions run the agreement tests reliably?
Timebox: half a day. Past this, decide with what you have.

## Findings
Run on 2026-11-21.

**Starting point.** This machine had no Neo4j Desktop, no Docker and no Neo4j listening on 7687. Its Java is 11.0.13, too old for Neo4j 5, which needs 17 or 21. The repository also has **no GitHub remote**: nothing has been pushed, so neither CI nor GitHub Pages can run yet. The existing `.github/workflows/capitan.yml` runs only on pull requests and has no test step.

**Versions, from Neo4j's official documentation:**
- The Python driver 6.x "supports connection to Neo4j instances version 4.4.x, 5.x, 2025.x, and 2026.x" (https://neo4j.com/docs/python-manual/current/install/).
- The supported-versions article lists **5.26 LTS** (December 2024 to June 6, 2028) as working with drivers 6.x, 5.x and 4.4 (https://support.neo4j.com/s/article/115013134648-Neo4j-Supported-Versions/).
- 5.26 LTS runs on "Java SE 17 and Java SE 21" (https://neo4j.com/docs/operations-manual/current/installation/requirements/, table 7).
- The newest 5.26 patch on dist.neo4j.org is **5.26.33**.

**Local setup (owner's choice: a portable install, not Neo4j Desktop):**
- The Neo4j Community 5.26.33 Windows zip and Eclipse Temurin JDK 21.0.13.1+2 were unpacked into `%LOCALAPPDATA%\akg-neo4j\`, outside the repo. Both SHA-256 checksums matched the published values. Nothing was installed system-wide.
- A generated password is stored in `~/.claude/secrets.yaml` under `databases.akg_neo4j` (`uri`, `username`, `password`), following the global secrets convention. It was set with `neo4j-admin dbms set-initial-password` and never printed.
- The server is started with `JAVA_HOME` pointing to the bundled JDK and `bin\neo4j.bat console`. It reported "Bolt enabled on localhost:7687" and "Started" within about 20 s.
- `neo4j==6.4.1` (the latest; an approved package) was installed into `.venv` for the experiment. It is not yet pinned in `requirements.txt`; E3's first Neo4j child pins it.
- **Result:** the driver connected and reported `Neo4j Kernel 5.26.33 community`. A batched `UNWIND` load of the seed-42 risks, controls and mitigates edges (1,024 nodes, 938 edges, with uniqueness constraints) took 2.1 s, and the counts matched the CSV rows exactly. That is the parity INV-8 needs.

**CI** (not run: there is no remote yet):
- Docker Hub has `neo4j:5.26.33-community` (and `5.26.33`, `5.26`, `5.26-community`), checked through the Docker Hub tags API. Pinning `5.26.33-community` matches the local server exactly.
- The documented container settings are `NEO4J_AUTH=neo4j/<password>` and port 7687. A CI-only password in the workflow file is acceptable: it is a throwaway container on a pull-request runner, and project rules forbid secrets on pull-request jobs anyway.
- Two constraints for the plan:
  - The workflow lives in `.github/`, a governance folder, so the owner commits it (allow-governance), and the agent gives a copy-paste block.
  - The repo must exist on GitHub first (owner's choice: created at E3's CI child).
- Reliability in Actions is therefore unproven until that child runs. That child must include a readiness wait on the service, a health check or a driver retry, because Neo4j takes about 20 s to start.

## Decision
Decision: GO
Why: Neo4j 5.26 LTS with the Python driver 6.x works on this Windows machine through the portable install, and a realistic batched load gives exact counts in about 2 s. The same server version exists as an official Docker image for CI.
Next:
- E3's plan pins Neo4j 5.26.33 (local zip and CI image) and `neo4j==6.4.1`.
- The tests read `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD`, as AGENTS.md says. Locally these are bridged from `secrets.yaml` (`databases.akg_neo4j`) at run time, never copied into the repo, and Neo4j tests skip when `NEO4J_URI` is unset.
- E3's CI child creates the GitHub repo (an owner copy-paste block), adds the test workflow (governance, owner-committed), and proves service-container reliability on its first runs.
- To start the local server again:

  ```
  $env:JAVA_HOME="$env:LOCALAPPDATA\akg-neo4j\jdk-21.0.13.1+2"
  & "$env:LOCALAPPDATA\akg-neo4j\neo4j-community-5.26.33\bin\neo4j.bat" console
  ```
