# Pages

The public page, https://neifertg.github.io/audit-knowledge-graph/, is published by `.github/workflows/pages.yml` (E4 child c, change 023).

## How it is built and deployed
- **Built from committed files only:** `python -m src.features.site.build --out _site` renders `index.html` from `src/features/site/template.html` and the committed exports (`src/features/site/data/site.json`, `src/features/rounds/rounds.json`, `src/features/reconciliation/scores.json`) and copies the CSS, JS and the three JSON files beside it. Standard library only: no `pip install` in the workflow, and nothing generated is committed.
- **Tests first.** The workflow runs on `workflow_run` when the `tests` workflow completes for main; its guard job proceeds only if that run's conclusion is success and its event was a push.
- **Only the exact tested commit, and only while it is main's head.** The deploy job checks out `workflow_run.head_sha`. The guard job compares that SHA with main's current head (`git ls-remote`) first; if main has moved on, the deploy is **refused**: the run ends green with a notice, and, because the guard job has no environment, no deployment is recorded. A re-run of an older green run therefore cannot put an older page over the current one; the newer commit's own run deploys it.
- **One deployment at a time** (`concurrency: pages`, not cancelled), so a newer commit's deploy queues behind an older one and lands last.

## Turning Pages on
Once, before the first push of main that should deploy:

```
gh api -X POST repos/neifertg/audit-knowledge-graph/pages -f build_type=workflow
```

An answer of 409 means Pages is already on.

## Checking the live page against a local build
Take the deployed commit from a pages run whose guard reported current (never from the Deployments list), check it equals main's head, build that commit in a fresh `git worktree` with the command above, and compare each of the six files (`index.html`, `site.css`, `site.js`, `site.json`, `rounds.json`, `scores.json`) with the live one **byte for byte**, allowing one retry a minute later for the Pages cache.

## Changing the workflow later
A test (`ci.test_workflow.WorkflowTests.test_ac2_023_pages_workflow_deploys_only_current_tested_head`) requires the committed workflow to equal change 023's reviewed draft, `changes/023-publish-on-github-pages-portfolio-card-a/proposed/pages.yml`, byte for byte. A later change to the workflow drafts its own copy in its own change folder and re-points that test's `proposed` path there, in the same change, so the reviewed draft and the committed file stay tied.

## Live check
Filled in by change 024 after the first deploy.
