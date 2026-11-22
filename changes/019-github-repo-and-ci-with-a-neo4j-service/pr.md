# GitHub repo and CI with a Neo4j service container

Change `019-github-repo-and-ci-with-a-neo4j-service` · objective **O2**: A data scientist finds every claim credible and reproducible. Signal: one command reproduces every number on the page from a fresh clone; CI is green; every SQL-vs-Cypher round has a test proving both return the same answer; the page makes no claim without a test or a cited method.

## Why
E3 child e (O2). "Every SQL-vs-Cypher round has a test proving both return the same answer" is only credible to a data scientist if a public CI runs those tests, against a real Neo4j, on every push. Until now they ran only on the owner's laptop. This change creates the public repository and makes CI the proof.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | the owner runs copy-paste block A after approval | a **public** GitHub repository `neifertg/audit-knowledge-graph` exists (visibility public, per GOALS; the owner confirms it when running the block) with `main` pushed and matching the local `main`. Before the block is handed over, the agent re-runs the pre-push audit over **every commit on main** (pushing publishes the whole history), not just the current tree, and reports it: no file version in any commit matches a secret pattern (`sk-ant-`, an assigned `api_key` or `password` literal, a private key header), every author and committer email is the GitHub noreply address, and no blob in history exceeds 50 MB. Run on 2026-11-21 over 216 commits: zero matches for every pattern, the largest blob 0.60 MB (`ai_text_full.jsonl`), one email (`...@users.noreply.github.com`). | `check: the audit (`git rev-list main | xargs git grep -I -l -E <pattern>` per pattern; `git rev-list --objects main | git cat-file --batch-check` for sizes; `git log main --format=%ae%n%ce`) is re-run and quoted before block A; then `gh repo view neifertg/audit-knowledge-graph --json visibility,defaultBranchRef` gives PUBLIC and main, and `git rev-parse main origin/main` match` | pass | PASS |
| AC-2 | the workflow `.github/workflows/tests.yml` is read (drafted as `changes/019-.../proposed/tests.yml`; the owner copies it into `.github/` and commits it on the change branch in block B, under `capitan allow-governance`) | it runs the **full** suite on every push and pull request, on `ubuntu-latest`, with Python 3.12 and the pinned `requirements.txt`. It has:
- a `neo4j:5.26.33-community` service container (the R3 pin; the tag was confirmed on Docker Hub, HTTP 200, 2026-11-21) with a `cypher-shell` health check and capped memory (heap 1 GB, page cache 512 MB);
- a readiness step that retries a driver connection for up to 120 s and, if Neo4j never comes up, fails with the last connection error (so a wrong password, a refused connection and a crashed container are told apart);
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` set to a throwaway literal for the job-local container, and `AKG_REQUIRE_NEO4J=1`;
- **no secrets**: no `secrets.` reference anywhere (AGENTS: CI jobs on pull requests never get secrets);
- `permissions: contents: read`, a 45-minute timeout and per-ref concurrency;
- a final step that fails if the unittest summary line (`OK (...)` or `FAILED (...)`) reports any skipped test, so the job cannot go green with the Neo4j tests skipped.

A test reads the committed workflow as text (no YAML library: `pyyaml` is approved only for one-off secrets scripts) and asserts each of these. | `ci.test_workflow.WorkflowTests.test_ac2_workflow_runs_every_test_with_a_real_neo4j` | pass | PASS |
| AC-3 | block B pushes the change branch and the workflow runs on it | the run is **green**, the log shows `Ran N tests` with N equal to the local suite's count on the same commit (100 before this change, at least 102 after it) and `OK` with no `skipped=`, and the readiness step shows Neo4j came up. The run's URL, wall time and test count are recorded in docs/ci.md and the review.

**Failures that happen only in CI** (Linux paths, ordering or timing, or the CI environment itself) are fixed in this change, with a regression test where one is possible. The review lists every file touched outside `tests/` and `docs/` and the CI failure each fixes; the local suite (plain and under `with_neo4j`) stays green.

**Except goldens:** if a golden checksum or committed figure (the reconciled goldens, `scores.json`, `cue_figures.json`, `weights.json`'s fingerprint, `rounds.json`) differs on Linux, for example through numpy or scikit-learn floating point, it is **never regenerated to make CI pass**. The agent stops, shows the difference and reports to the owner, because it would change INV-7's meaning (byte-identical output per seed). | `check: `gh run list --branch change/019-github-repo-and-ci-with-a-neo4j-service --workflow tests` shows a completed success; `gh run view <id> --log` contains `Ran <N> tests` (N = the local count on that commit) and `OK` without `skipped=`` | pass | PASS |
| AC-4 | a newcomer reads the repository | a short top-level `README.md` says what the project is (one paragraph), how to install, build and test (the commands from AGENTS.md), how to run the Neo4j tests locally (`with_neo4j`) and in CI, and shows the `tests` workflow badge; `docs/ci.md` gives the workflow's design (service container, readiness, the skip guard, no secrets), the measured first-run wall time, and how to reproduce CI locally. `.gitignore` gains `data/` (the default build folder, so an `akg build` never leaves an untracked bank in the tree), committed by the owner in block B with the workflow. | `ci.test_workflow.WorkflowTests.test_ac4_readme_ci_doc_and_gitignore` | pass | PASS |
| AC-5 | the suite runs with CI's environment (`NEO4J_*` set and `AKG_REQUIRE_NEO4J=1` for the whole job) | it passes. Found by the critique: `tests/generator/helpers.akg_env()` strips `NEO4J_*` from test subprocesses but passes `AKG_REQUIRE_NEO4J` through, so in CI the skip probe in `test_neo4j.test_ac4_pipeline_env_helper_skip_and_require` would print FAIL where it expects SKIP. `akg_env(neo4j=False)` now strips `AKG_REQUIRE_NEO4J` too (a subprocess that cannot reach Neo4j cannot be required to); `akg_env(neo4j=True)` keeps both. A regression test sets `AKG_REQUIRE_NEO4J=1` in the test process and checks that `akg_env()` drops it and `akg_env(neo4j=True)` keeps it. **Rehearsal between blocks B1 and B2:** on the commit the owner makes in block B1 (workflow and `.gitignore` in place, nothing pushed yet), the full local suite runs under `with_neo4j` with `AKG_REQUIRE_NEO4J=1` exported, logged to the scratchpad, and passes with no skips; its `Ran N tests` is the N that AC-3 expects from CI on the same commit. Only then is block B2 handed over. | `ci.test_workflow.WorkflowTests.test_ac5_ci_environment_reaches_no_test_subprocess, plus the logged CI-environment rehearsal run` | pass | PASS |

## Review in this order

1. **Tests**: `tests/ci/__init__.py`, `tests/ci/test_workflow.py`, `tests/generator/helpers.py`

## Governance files changed (review these first)
These change the rules capitan and the agents follow:
- `.github/workflows/tests.yml`
- `.gitignore`

## Data impact
None. No entity, relationship or invariant changes. INV-8 (parity) and the rounds' agreement tests start running in CI. `.gitignore` gains `data/`.

## Risks
- **CI-only failures** on the first run (the suite has only ever run on Windows, and never with `AKG_REQUIRE_NEO4J=1` set for the whole run). The critique found one before any run (AC-5); the local CI-environment rehearsal catches that class early, and the first run itself catches Linux-only ones. Fixes are in scope (`src/**`, `akg/**`, `tests/**`, widened from the epic's `tests/**` and `docs/**` for exactly this) but only for what CI reveals, each listed in the review; anything larger is parked and the plan revised (rule 3).
- **Floating-point goldens on Linux:** the reconciled goldens, `scores.json`, `cue_figures.json` and the weights fingerprint come from numpy and scikit-learn arithmetic, which can differ by platform. The plan's evidence covers line endings only. Rule (AC-3): never regenerate a golden to make CI pass; stop and report to the owner.
- **Two runs per push on a branch with an open PR** (the `push` and `pull_request` triggers both fire). This project merges locally without PRs, so it rarely happens; `pull_request` stays so an outside contributor's fork PR still runs the suite.
- **Neo4j start-up or memory in the runner:** health check plus a 120 s readiness loop; heap and page cache capped. GitHub's public runners have 16 GB RAM, so the local slowdowns (L-017) should not recur, but the first run's wall time is recorded either way.
- **Making the repo public is outward-facing and hard to undo.** The pre-push audit runs and is shown before block A, and the owner runs the block.
- **CI time:** the local suite took 227 s plain and 400-970 s under Neo4j on a memory-starved laptop; the 45-minute timeout leaves wide margin.
- **capitan's PR gate** (`capitan.yml`) only runs on pull requests; this project merges locally, so pushes to main are covered by the new workflow, not the gate. Branch protection is out of scope.

## Deliberately not in this PR
- GitHub Pages (E4 child c turns it on); E4's epic revision (parked).
- Branch protection and required checks; pinning actions to commit SHAs; a Windows CI job.
- The parked 018 finding on Cypher write clauses (before E4 publishes).

Parked for later:
- 2026-11-21 019 review minors: the AC-4 CI-doc test checks only the First run heading (now that a run exists it could require an actions/runs/<n> URL); its phrase checks are case-sensitive, which failed a commit over wording (match case-insensitively) (from 019-github-repo-and-ci-with-a-neo4j-service)

## Lessons recorded
- L-020 A test that runs in CI must not require evidence of its own CI run

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `12800e9f54046688`
- Size: 3 code files, +73 / -2 lines
