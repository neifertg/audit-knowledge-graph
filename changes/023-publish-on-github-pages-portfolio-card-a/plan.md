# Publish on GitHub Pages, portfolio card and the O1 reader test

```json plan
{
  "id": "023-publish-on-github-pages-portfolio-card-a",
  "tier": "standard",
  "status": "done",
  "created": "2026-11-22",
  "objective": "O1",
  "areas": [
    "src/features/site/**",
    "tests/**",
    "docs/**",
    "research/**",
    "README.md"
  ],
  "timebox": "1 day. Past this, stop and re-plan.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "022's parked review findings are fixed, each as a named test written before its fix (L-023)",
      "then": "the four are closed before anything goes public:\n- `test_ac1_023_round5_split_adds_up`: for each side, round 5's query score plus its setup score from `site.json`'s `round5_split` equals that side's score in `rounds.json` (read from the file, not typed);\n- `test_ac1_023_owner_scenario_through_formatter`: owner concentration's scenario cell is a marked element rendered by a formatter (a new `scenario_supporting` formatter, unit-tested, giving 'derived (supporting query)'), so the builder types no prose into a figure cell;\n- `test_ac1_023_project_titles`: the `project` block's titles equal the first heading line of each closed epic's `epic.md`;\n- `test_ac1_023_each_close_rule_nonempty`: each close-round rule (SQL steps no more than Cypher's; Cypher needing more moving parts) picks out at least one round.\n\nThis list is the checklist the review ticks.",
      "test": "webpage.test_site.SiteTests.test_ac1_023_round5_split_adds_up, test_ac1_023_owner_scenario_through_formatter, test_ac1_023_project_titles, test_ac1_023_each_close_rule_nonempty",
      "status": "pass"
    },
    {
      "id": "AC-2",
      "when": "the Pages workflow `.github/workflows/pages.yml` is read (drafted as `changes/023-.../proposed/pages.yml`; the owner commits it in block B1)",
      "then": "it deploys only a tested commit that is still main's head: triggered by `workflow_run` on `tests`, `types: [completed]`, `branches: [main]`; the job runs only if the run's `conclusion` is `success` and its `event` is `push`; it checks out `workflow_run.head_sha`; a guard step compares that SHA with main's current head (`git ls-remote origin refs/heads/main`) and every later step runs only when they match, so re-running an older green run cannot put an older page over the current one; it builds with `python -m src.features.site.build --out _site` (standard library only, no `pip install`) and deploys with `actions/configure-pages@v6`, `actions/upload-pages-artifact@v5` (path `_site`) and `actions/deploy-pages@v5`; permissions `contents: read`, `pages: write`, `id-token: write`; the `github-pages` environment; `concurrency: pages`, not cancelled; no `secrets.` reference. **The test** strips comment lines before matching, matches whole lines (not phrases a comment could carry), checks each guarded step carries the guard condition, and asserts the committed file equals `proposed/pages.yml` byte for byte.",
      "test": "ci.test_workflow.WorkflowTests.test_ac2_023_pages_workflow_deploys_only_current_tested_head",
      "status": "pass"
    },
    {
      "id": "AC-3",
      "when": "the reader test is prepared",
      "then": "`capitan research \"O1 reader test\"` starts `research/o1-reader-test/` (so `capitan tidy` tracks it to a `decision.md`), holding `script.md` and `results.md`. **The script** gives what to send (the live URL, to read only the top section, stopping at the heading 'The rounds', for about a minute), the one question ('In one sentence, what does this show, and why would an audit leader care?'), **three readers** (GOALS' signal is 2 of 3), and **the pass rule, fixed before any answer**: a sentence passes when it says both (a) that records from two teams or systems (ERM and Internal Audit, or risk and control records, or tables) are connected or reconciled, or that risk is found across them, and (b) a planning benefit (finding shared-system exposure, repeat findings, concentrated ownership, or better audit coverage). The script gives two worked passing and two worked failing sentences. **Judging:** the owner and the agent each judge every answer against the rule, independently; where they differ, the stricter reading stands, and both judgments are recorded. **The template** (`results.md`): Reader A, B, C by role only, the date, the sentence verbatim, both judgments and the reason.",
      "test": "ci.test_workflow.WorkflowTests.test_ac3_023_reader_test_prepared (script holds the question, the stop point, three readers, the rule's two parts, two passing and two failing examples, the judging rule; the template holds the fields)",
      "status": "pass"
    },
    {
      "id": "AC-4",
      "when": "the docs are read",
      "then": "`docs/pages.md` gives how the page is built and deployed, the gate (tests first, then the exact commit, only while it is main's head), how to turn Pages on, and how to check the live page against a local build of the deployed commit; its 'Live check' section is filled by change 024, and no test here requires it (L-020). `README.md` names the live address (`https://neifertg.github.io/audit-knowledge-graph/`) and `docs/pages.md`; the site README names the Pages workflow. The portfolio card is drafted in `changes/023-.../proposed/portfolio-card.md`, in the existing cards' shape, figure-free, placed first under 'Projects' (newest first; the owner may move it), without a demo GIF (deliberate for now: the live page is the demo).",
      "test": "ci.test_workflow.WorkflowTests.test_ac4_023_pages_docs",
      "status": "pass"
    }
  ],
  "epic": "004-e4-page-v1-and-publish",
  "child": "c",
  "approved": "2026-11-22",
  "approved_hash": "07c3e51eeea38b77",
  "in_progress": "2026-11-22",
  "done": "2026-11-22"
}
```

## Why
E4 child c (O1). It makes publishing safe and ready: 022's open findings fixed, a Pages workflow that can only deploy a tested commit that is still current, the docs, and a fair reader test prepared. **Going live is the owner's merge of this change** (block C turns Pages on before main is pushed). Critique round 1 showed the post-deploy steps cannot be criteria here, because they can only happen after this change is merged and capitan finishes only a change whose criteria all pass; so **a follow-up standard change, 024**, carries them: the live check (the deployed commit equals main; a fresh-worktree build of it equals the live page byte for byte in all six files, with one retry for the Pages cache), the portfolio card committed in `risk-analytics-portfolio`, and the reader-test answers and decision. The epic's closing revision will record this split.

## Owner steps (complete blocks given in turn; L-001)
- **B1** (after the agent's branch work), on the change branch, one `capitan allow-governance` for both governance files:

  ```
  cd "C:\Users\Seth Neifert\Documents\GitHub\audit-knowledge-graph"
  git switch change/023-publish-on-github-pages-portfolio-card-a
  .venv\Scripts\python -m capitan allow-governance
  Copy-Item changes\023-publish-on-github-pages-portfolio-card-a\proposed\pages.yml .github\workflows\pages.yml
  Add-Content -Path .gitignore -Value "!src/features/site/data/" -Encoding ascii
  git add .github/workflows/pages.yml .gitignore
  git commit -m "023: add the Pages workflow (tested, current head only) and keep site data tracked"
  ```
  No push. The agent then runs the full suite on a fresh checkout of that commit (L-022).
- **B2:** `git push -u origin change/023-publish-on-github-pages-portfolio-card-a` (CI runs on the branch; the Pages workflow runs only for main).
- **C, go live** (after review and finish): turn Pages on, then merge, prune and push. Turning Pages on first means the first push of main deploys; if Pages is already on, the API answers 409, which is fine.

  ```
  gh api -X POST repos/neifertg/audit-knowledge-graph/pages -f build_type=workflow
  git switch main
  git merge --no-ff --no-edit change/023-publish-on-github-pages-portfolio-card-a
  .venv\Scripts\python -m capitan branches --prune --yes
  git push origin main
  ```
  The tests run on main, then the page deploys; the agent watches both and starts 024.

## Data impact
None. `.gitignore` gains `!src/features/site/data/` (owner, governance), so the committed site data stays tracked without `git add -f`.

## Test plan
AC-1 to AC-4's tests in the suite. Per L-022, the full suite runs on a fresh checkout of B1's commit before B2, plain and under `with_neo4j`. CI runs it on the branch and on main.

**Evidence** (pre-plan, 2026-11-22): Pages is not enabled (the API answers 404); the latest majors are `configure-pages@v6`, `upload-pages-artifact@v5`, `deploy-pages@v5`; the portfolio is a public Jekyll site whose `index.md` lists project cards in the draft's shape; the builder needs only the standard library and committed files.

## Risks
- **Going live is outward-facing and the owner's call.** It happens only through block C, after review, local preview and a green suite; only a tested, current commit can deploy.
- **The first deploy fails** (permissions or the environment's branch policy). The run's log says why; 024 starts with it, and nothing is live until a deploy passes.
- **The reader test's rule is unfair to plain wording.** Fixed before answers, with examples, two judges and the stricter reading on ties.

## Out of scope
- The live check, the portfolio card commit and the reader answers (change 024).
- A custom domain; analytics on the page (none: it loads nothing but the pinned Cytoscape).
- M1's milestone close (after 024).

## Relevant lessons
- **L-001:** the owner's blocks above are complete.
- **L-020:** no test here requires evidence of the deploy.
- **L-022:** the fresh-checkout run before B2.
- **L-023:** 022's findings are named tests (AC-1), ticked in review.

## Slices
1. AC-1's tests and fixes; the workflow, reader-test and docs tests (AC-2 to AC-4); `capitan research` and the script and template; the docs.
2. B1, the fresh-checkout run, B2; review; finish.
3. Block C (the owner's go-live); then plan 024.
