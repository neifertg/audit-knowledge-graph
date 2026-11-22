VERDICT: REVISE
Round 2. Every round-1 item is answered:
- (1) The CI environment leak is now AC-5, with the `akg_env()` fix, a regression test and a rehearsal. I confirmed the leak in `tests/generator/helpers.py:18` and in the probe at `tests/stores/test_neo4j.py:258-262`. The proposed fix keeps the probe's `FAIL` leg working, because that leg adds the variable itself.
- (2) AC-1's audit now covers every commit on main. `git rev-list main --count` is 216 today.
- (3) AC-3 has the goldens rule: never regenerate, stop and report.
- (4) N is now the local count on the same commit.
- (5) The review lists each file touched outside `tests/` and `docs/`.
- (6) Main's first run is a post-merge check.
- (7) The double run is accepted in Risks.

I also checked how the gate treats the block B files. `.github/workflows/tests.yml` and `.gitignore` are classed as governance, not code (`capitan/cli.py` `gate_eval`). The new workflow is an added file and needs no token. The changed `.gitignore` does, and block B runs `allow-governance` for it. Neither file counts against `areas`.

1. [major] The AC-5 rehearsal cannot pass as written. AC-5: "**Rehearsal before block B:** the full local suite runs under `with_neo4j` with `AKG_REQUIRE_NEO4J=1` exported ... and passes with no skips". The Test plan says the AC-2 and AC-4 tests "fail until block B lands, by design". They read `.github/workflows/tests.yml` and `.gitignore`, which only the owner commits, in block B. So the rehearsal runs before those files exist and has at least two failures. Its "passes" condition can never be met. An agent would then either mark AC-5 against the wording or move the rehearsal to after block B. Block B ends with the push, so that would be after the first CI run, which defeats the rehearsal's purpose. -> Pick one and write it into the plan:
   - (a) The rehearsal passes except for exactly `test_ac2_...` and `test_ac4_...`, each failing only because a file is missing, and the log shows this.
   - (b) Split block B: the owner commits the workflow and `.gitignore`, the agent runs the rehearsal on that commit (full pass, no skips), then a block B2 pushes.

   (b) also gives AC-3 its "local count on the same commit" for free.
2. [minor] The readiness step drops the error it is waiting on. `except Exception as error: time.sleep(2)` never prints `error`. If Neo4j never comes up, the log says only "Neo4j did not become ready in 120 s", with nothing to tell a wrong password from a refused connection or a crashed container. That is the one failure this step exists to diagnose on the first run. -> Keep the last exception and include it in the `SystemExit` message. The service container's own logs also help, but they appear only in the job's cleanup section.
3. [minor] The skip guard runs the same pattern over the whole `tee` log: `grep -qE "skipped=[0-9]+" test-output.txt`. Any test that echoes a nested unittest summary, or prints a captured subprocess's output on failure, would trip it. I found no test that does this today (`tests/` raises `SkipTest` in one place only, `test_neo4j.py:35`). -> Optional: match only the final summary line (`^(OK|FAILED) .*skipped=`), and have the AC-2 test assert that form.

Not checked:
- Whether `cypher-shell` is on `PATH` inside `neo4j:5.26.33-community`, so the health check works. I believe it is, but only the first run shows it.
- Whether the Docker Hub tag still resolves.
- Linux-only behaviour of the suite, its wall time on a runner, and floating-point drift in the goldens. The plan rightly leaves these to the first run (AC-3).

I did not run the tests (L-017). From the repository I confirmed:
- the repo name is still free (`gh repo view` finds no repository);
- there is no git remote;
- `requirements.txt` has no Windows-only pins;
- every existing test folder has an `__init__.py`, so the new `tests/ci/` needs one too for the `ci.test_workflow...` IDs to resolve;
- the workflow has no `secrets.` reference.
