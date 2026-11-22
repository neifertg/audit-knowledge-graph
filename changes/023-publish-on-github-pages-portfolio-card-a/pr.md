# Publish on GitHub Pages, portfolio card and the O1 reader test

Change `023-publish-on-github-pages-portfolio-card-a` · objective **O1**: A CAE grasps the value in about 60 seconds without technical background. Signal: 2-3 audit people known to the owner read only the top section and each restates the value correctly in one sentence (milestone 1 passes at 2 of 3).

## Why
E4 child c (O1). It makes publishing safe and ready: 022's open findings fixed, a Pages workflow that can only deploy a tested commit that is still current, the docs, and a fair reader test prepared. **Going live is the owner's merge of this change** (block C turns Pages on before main is pushed). Critique round 1 showed the post-deploy steps cannot be criteria here, because they can only happen after this change is merged and capitan finishes only a change whose criteria all pass; so **a follow-up standard change, 024**, carries them: the live check (the deployed commit equals main; a fresh-worktree build of it equals the live page byte for byte in all six files, with one retry for the Pages cache), the portfolio card committed in `risk-analytics-portfolio`, and the reader-test answers and decision. The epic's closing revision will record this split.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | 022's parked review findings are fixed, each as a named test written before its fix (L-023) | the four are closed before anything goes public:
- `test_ac1_023_round5_split_adds_up`: for each side, round 5's query score plus its setup score from `site.json`'s `round5_split` equals that side's score in `rounds.json` (read from the file, not typed);
- `test_ac1_023_owner_scenario_through_formatter`: owner concentration's scenario cell is a marked element rendered by a formatter (a new `scenario_supporting` formatter, unit-tested, giving 'derived (supporting query)'), so the builder types no prose into a figure cell;
- `test_ac1_023_project_titles`: the `project` block's titles equal the first heading line of each closed epic's `epic.md`;
- `test_ac1_023_each_close_rule_nonempty`: each close-round rule (SQL steps no more than Cypher's; Cypher needing more moving parts) picks out at least one round.

This list is the checklist the review ticks. | `webpage.test_site.SiteTests.test_ac1_023_round5_split_adds_up, test_ac1_023_owner_scenario_through_formatter, test_ac1_023_project_titles, test_ac1_023_each_close_rule_nonempty` | pass | PASS |
| AC-2 | the Pages workflow `.github/workflows/pages.yml` is read (drafted as `changes/023-.../proposed/pages.yml`; the owner commits it in block B1) | it deploys only a tested commit that is still main's head: triggered by `workflow_run` on `tests`, `types: [completed]`, `branches: [main]`; the job runs only if the run's `conclusion` is `success` and its `event` is `push`; it checks out `workflow_run.head_sha`; a guard step compares that SHA with main's current head (`git ls-remote origin refs/heads/main`) and every later step runs only when they match, so re-running an older green run cannot put an older page over the current one; it builds with `python -m src.features.site.build --out _site` (standard library only, no `pip install`) and deploys with `actions/configure-pages@v6`, `actions/upload-pages-artifact@v5` (path `_site`) and `actions/deploy-pages@v5`; permissions `contents: read`, `pages: write`, `id-token: write`; the `github-pages` environment; `concurrency: pages`, not cancelled; no `secrets.` reference. **The test** strips comment lines before matching, matches whole lines (not phrases a comment could carry), checks each guarded step carries the guard condition, and asserts the committed file equals `proposed/pages.yml` byte for byte. | `ci.test_workflow.WorkflowTests.test_ac2_023_pages_workflow_deploys_only_current_tested_head` | pass | PASS |
| AC-3 | the reader test is prepared | `capitan research "O1 reader test"` starts `research/o1-reader-test/` (so `capitan tidy` tracks it to a `decision.md`), holding `script.md` and `results.md`. **The script** gives what to send (the live URL, to read only the top section, stopping at the heading 'The rounds', for about a minute), the one question ('In one sentence, what does this show, and why would an audit leader care?'), **three readers** (GOALS' signal is 2 of 3), and **the pass rule, fixed before any answer**: a sentence passes when it says both (a) that records from two teams or systems (ERM and Internal Audit, or risk and control records, or tables) are connected or reconciled, or that risk is found across them, and (b) a planning benefit (finding shared-system exposure, repeat findings, concentrated ownership, or better audit coverage). The script gives two worked passing and two worked failing sentences. **Judging:** the owner and the agent each judge every answer against the rule, independently; where they differ, the stricter reading stands, and both judgments are recorded. **The template** (`results.md`): Reader A, B, C by role only, the date, the sentence verbatim, both judgments and the reason. | `ci.test_workflow.WorkflowTests.test_ac3_023_reader_test_prepared (script holds the question, the stop point, three readers, the rule's two parts, two passing and two failing examples, the judging rule; the template holds the fields)` | pass | PASS |
| AC-4 | the docs are read | `docs/pages.md` gives how the page is built and deployed, the gate (tests first, then the exact commit, only while it is main's head), how to turn Pages on, and how to check the live page against a local build of the deployed commit; its 'Live check' section is filled by change 024, and no test here requires it (L-020). `README.md` names the live address (`https://neifertg.github.io/audit-knowledge-graph/`) and `docs/pages.md`; the site README names the Pages workflow. The portfolio card is drafted in `changes/023-.../proposed/portfolio-card.md`, in the existing cards' shape, figure-free, placed first under 'Projects' (newest first; the owner may move it), without a demo GIF (deliberate for now: the live page is the demo). | `ci.test_workflow.WorkflowTests.test_ac4_023_pages_docs` | pass | PASS |

## Review in this order

1. **src/features/site/****: `src/features/site/build.py`, `src/features/site/formatters.py`
2. **Tests**: `tests/ci/test_workflow.py`, `tests/webpage/test_site.py`

## Governance files changed (review these first)
These change the rules capitan and the agents follow:
- `.github/workflows/pages.yml`
- `.gitignore`

## Data impact
None. `.gitignore` gains `!src/features/site/data/` (owner, governance), so the committed site data stays tracked without `git add -f`.

## Risks
- **Going live is outward-facing and the owner's call.** It happens only through block C, after review, local preview and a green suite; only a tested, current commit can deploy.
- **The first deploy fails** (permissions or the environment's branch policy). The run's log says why; 024 starts with it, and nothing is live until a deploy passes.
- **The reader test's rule is unfair to plain wording.** Fixed before answers, with examples, two judges and the stricter reading on ties.

## Deliberately not in this PR
- The live check, the portfolio card commit and the reader answers (change 024).
- A custom domain; analytics on the page (none: it loads nothing but the pinned Cytoscape).
- M1's milestone close (after 024).

Parked for later:
- 2026-11-22 023 review minors for 024: the Pages guard should fail red, not green, when git ls-remote fails (set -o pipefail or check head is non-empty; governance file, owner commits); test the portfolio card draft and state its placement; decision.md in research/o1-reader-test is still the template until the reader results (from 023-publish-on-github-pages-portfolio-card-a)

## Lessons recorded
- L-024 Gate a workflow_run deploy on the tested commit still being main's head, in its own job

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `bb5a3cfaebf002a3`
- Size: 4 code files, +92 / -2 lines

## Note on AC-2's wording
The plan says a guard *step* gates every later step. The build uses a guard *job* (no environment) and a deploy job gated on its output, folded in from critique round 2 so that a refused deploy records no deployment. They behave the same way for every case the plan names.
