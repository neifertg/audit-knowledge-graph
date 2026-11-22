# GitHub repo and CI with a Neo4j service container

```json plan
{
  "id": "019-github-repo-and-ci-with-a-neo4j-service",
  "tier": "standard",
  "status": "approved",
  "created": "2026-11-21",
  "objective": "O2",
  "areas": [
    "tests/**",
    "docs/**",
    "README.md",
    "src/**",
    "akg/**"
  ],
  "timebox": "1 day. Past this, stop and re-plan or split.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "the owner runs copy-paste block A after approval",
      "then": "a **public** GitHub repository `neifertg/audit-knowledge-graph` exists (visibility public, per GOALS; the owner confirms it when running the block) with `main` pushed and matching the local `main`. Before the block is handed over, the agent re-runs the pre-push audit over **every commit on main** (pushing publishes the whole history), not just the current tree, and reports it: no file version in any commit matches a secret pattern (`sk-ant-`, an assigned `api_key` or `password` literal, a private key header), every author and committer email is the GitHub noreply address, and no blob in history exceeds 50 MB. Run on 2026-11-21 over 216 commits: zero matches for every pattern, the largest blob 0.60 MB (`ai_text_full.jsonl`), one email (`...@users.noreply.github.com`).",
      "test": "check: the audit (`git rev-list main | xargs git grep -I -l -E <pattern>` per pattern; `git rev-list --objects main | git cat-file --batch-check` for sizes; `git log main --format=%ae%n%ce`) is re-run and quoted before block A; then `gh repo view neifertg/audit-knowledge-graph --json visibility,defaultBranchRef` gives PUBLIC and main, and `git rev-parse main origin/main` match",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the workflow `.github/workflows/tests.yml` is read (drafted as `changes/019-.../proposed/tests.yml`; the owner copies it into `.github/` and commits it on the change branch in block B, under `capitan allow-governance`)",
      "then": "it runs the **full** suite on every push and pull request, on `ubuntu-latest`, with Python 3.12 and the pinned `requirements.txt`. It has:\n- a `neo4j:5.26.33-community` service container (the R3 pin; the tag was confirmed on Docker Hub, HTTP 200, 2026-11-21) with a `cypher-shell` health check and capped memory (heap 1 GB, page cache 512 MB);\n- a readiness step that retries a driver connection for up to 120 s and, if Neo4j never comes up, fails with the last connection error (so a wrong password, a refused connection and a crashed container are told apart);\n- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` set to a throwaway literal for the job-local container, and `AKG_REQUIRE_NEO4J=1`;\n- **no secrets**: no `secrets.` reference anywhere (AGENTS: CI jobs on pull requests never get secrets);\n- `permissions: contents: read`, a 45-minute timeout and per-ref concurrency;\n- a final step that fails if the unittest summary line (`OK (...)` or `FAILED (...)`) reports any skipped test, so the job cannot go green with the Neo4j tests skipped.\n\nA test reads the committed workflow as text (no YAML library: `pyyaml` is approved only for one-off secrets scripts) and asserts each of these.",
      "test": "ci.test_workflow.WorkflowTests.test_ac2_workflow_runs_every_test_with_a_real_neo4j",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "block B pushes the change branch and the workflow runs on it",
      "then": "the run is **green**, the log shows `Ran N tests` with N equal to the local suite's count on the same commit (100 before this change, at least 102 after it) and `OK` with no `skipped=`, and the readiness step shows Neo4j came up. The run's URL, wall time and test count are recorded in docs/ci.md and the review.\n\n**Failures that happen only in CI** (Linux paths, ordering or timing, or the CI environment itself) are fixed in this change, with a regression test where one is possible. The review lists every file touched outside `tests/` and `docs/` and the CI failure each fixes; the local suite (plain and under `with_neo4j`) stays green.\n\n**Except goldens:** if a golden checksum or committed figure (the reconciled goldens, `scores.json`, `cue_figures.json`, `weights.json`'s fingerprint, `rounds.json`) differs on Linux, for example through numpy or scikit-learn floating point, it is **never regenerated to make CI pass**. The agent stops, shows the difference and reports to the owner, because it would change INV-7's meaning (byte-identical output per seed).",
      "test": "check: `gh run list --branch change/019-github-repo-and-ci-with-a-neo4j-service --workflow tests` shows a completed success; `gh run view <id> --log` contains `Ran <N> tests` (N = the local count on that commit) and `OK` without `skipped=`",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "a newcomer reads the repository",
      "then": "a short top-level `README.md` says what the project is (one paragraph), how to install, build and test (the commands from AGENTS.md), how to run the Neo4j tests locally (`with_neo4j`) and in CI, and shows the `tests` workflow badge; `docs/ci.md` gives the workflow's design (service container, readiness, the skip guard, no secrets), the measured first-run wall time, and how to reproduce CI locally. `.gitignore` gains `data/` (the default build folder, so an `akg build` never leaves an untracked bank in the tree), committed by the owner in block B with the workflow.",
      "test": "ci.test_workflow.WorkflowTests.test_ac4_readme_ci_doc_and_gitignore",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the suite runs with CI's environment (`NEO4J_*` set and `AKG_REQUIRE_NEO4J=1` for the whole job)",
      "then": "it passes. Found by the critique: `tests/generator/helpers.akg_env()` strips `NEO4J_*` from test subprocesses but passes `AKG_REQUIRE_NEO4J` through, so in CI the skip probe in `test_neo4j.test_ac4_pipeline_env_helper_skip_and_require` would print FAIL where it expects SKIP. `akg_env(neo4j=False)` now strips `AKG_REQUIRE_NEO4J` too (a subprocess that cannot reach Neo4j cannot be required to); `akg_env(neo4j=True)` keeps both. A regression test sets `AKG_REQUIRE_NEO4J=1` in the test process and checks that `akg_env()` drops it and `akg_env(neo4j=True)` keeps it. **Rehearsal between blocks B1 and B2:** on the commit the owner makes in block B1 (workflow and `.gitignore` in place, nothing pushed yet), the full local suite runs under `with_neo4j` with `AKG_REQUIRE_NEO4J=1` exported, logged to the scratchpad, and passes with no skips; its `Ran N tests` is the N that AC-3 expects from CI on the same commit. Only then is block B2 handed over.",
      "test": "ci.test_workflow.WorkflowTests.test_ac5_ci_environment_reaches_no_test_subprocess, plus the logged CI-environment rehearsal run",
      "status": "pending"
    }
  ],
  "epic": "003-e3-dual-stores-and-head-to-head-rounds",
  "child": "e",
  "approved": "2026-11-21",
  "approved_hash": "42c18bfe4b989e4a"
}
```

## Why
E3 child e (O2). "Every SQL-vs-Cypher round has a test proving both return the same answer" is only credible to a data scientist if a public CI runs those tests, against a real Neo4j, on every push. Until now they ran only on the owner's laptop. This change creates the public repository and makes CI the proof.

## Data impact
None. No entity, relationship or invariant changes. INV-8 (parity) and the rounds' agreement tests start running in CI. `.gitignore` gains `data/`.

## Owner steps (copy-paste, after approval)
The agent gives each as one complete PowerShell block when its turn comes (L-001; never an editor-opening git command).
- **Block A (after approval):** the pre-push audit result is shown first; then `gh repo create audit-knowledge-graph --public --source . --remote origin --description "..."` and `git push -u origin main`. No workflow runs yet, except capitan's existing PR-only gate.
- **Block B1 (after the agent's branch work is committed):** on `change/019-...`, run `python -m capitan allow-governance`, copy `changes/019-.../proposed/tests.yml` to `.github/workflows/tests.yml`, append `data/` to `.gitignore`, and commit both with `-m`. No push.
- **Rehearsal (agent):** the AC-5 CI-environment run on that commit; any failure is fixed on the branch before going on.
- **Block B2:** `git push -u origin change/019-...`. The push starts the first CI run, on the commit the rehearsal passed.
- **After finish:** the merge (relay or owner) and `git push origin main`, which runs CI on main. Pushing is the owner's call; the agent asks before pushing anything. The README badge shows main's status, so it is red or absent until that push; the agent watches main's first run and reports it (a post-merge check, outside the criteria, since it can only happen after finish).

## Test plan
`tests/ci/test_workflow.py` checks the workflow text (AC-2) and the README, CI doc and `.gitignore` (AC-4); they fail until block B lands, by design. AC-1 and AC-3 are checks against GitHub, run with `gh` and quoted in the review. The done-check stays the full local suite, plain and under `with_neo4j` (L-017: logged to the scratchpad), plus the green CI run.

**Evidence gathered before this plan (2026-11-21):** no git remote; `gh` 2.82.1 logged in as `neifertg`; the repo name is free; the Neo4j image tag exists; every commit uses the noreply email; no tracked file matches a secret pattern; every generated file pins LF line endings (`newline="\n"`), so the goldens should match on Linux; the tests' Windows references are in messages only or already branch on the platform.

## Risks
- **CI-only failures** on the first run (the suite has only ever run on Windows, and never with `AKG_REQUIRE_NEO4J=1` set for the whole run). The critique found one before any run (AC-5); the local CI-environment rehearsal catches that class early, and the first run itself catches Linux-only ones. Fixes are in scope (`src/**`, `akg/**`, `tests/**`, widened from the epic's `tests/**` and `docs/**` for exactly this) but only for what CI reveals, each listed in the review; anything larger is parked and the plan revised (rule 3).
- **Floating-point goldens on Linux:** the reconciled goldens, `scores.json`, `cue_figures.json` and the weights fingerprint come from numpy and scikit-learn arithmetic, which can differ by platform. The plan's evidence covers line endings only. Rule (AC-3): never regenerate a golden to make CI pass; stop and report to the owner.
- **Two runs per push on a branch with an open PR** (the `push` and `pull_request` triggers both fire). This project merges locally without PRs, so it rarely happens; `pull_request` stays so an outside contributor's fork PR still runs the suite.
- **Neo4j start-up or memory in the runner:** health check plus a 120 s readiness loop; heap and page cache capped. GitHub's public runners have 16 GB RAM, so the local slowdowns (L-017) should not recur, but the first run's wall time is recorded either way.
- **Making the repo public is outward-facing and hard to undo.** The pre-push audit runs and is shown before block A, and the owner runs the block.
- **CI time:** the local suite took 227 s plain and 400-970 s under Neo4j on a memory-starved laptop; the 45-minute timeout leaves wide margin.
- **capitan's PR gate** (`capitan.yml`) only runs on pull requests; this project merges locally, so pushes to main are covered by the new workflow, not the gate. Branch protection is out of scope.

## Out of scope
- GitHub Pages (E4 child c turns it on); E4's epic revision (parked).
- Branch protection and required checks; pinning actions to commit SHAs; a Windows CI job.
- The parked 018 finding on Cypher write clauses (before E4 publishes).

## Relevant lessons
- **L-001** (owner commands are copy-paste blocks): blocks A and B, full PowerShell, `-m` only.
- **L-014** (count the builds): CI runs the suite once; no test adds a build.
- **L-017** (low memory): local runs log to the scratchpad; CI runs on a 16 GB runner.
- **L-018 and L-019** (measure before approval): the facts CI depends on (image tag, line endings, noreply email, secret scan) were checked before this plan, not assumed.

## Slices
1. Tests for the workflow text and docs (AC-2, AC-4), README and docs/ci.md; the `akg_env` fix and its test, then the CI-environment rehearsal (AC-5).
2. Block A: pre-push audit, repo created, main pushed (AC-1).
3. Block B1: workflow and `.gitignore` committed on the branch; the CI-environment rehearsal on that commit (AC-5); block B2 pushes the branch; first run watched (AC-3); fix any CI-only failure. `tests/ci/` gets an `__init__.py` like the other test folders.
4. Review, finish; the owner merges and pushes main.
