# Live check, portfolio card and the O1 reader test results

```json plan
{
  "id": "024-live-check-portfolio-card-and-the-o1-rea",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-22",
  "objective": "O1",
  "areas": [
    "docs/**",
    "research/**",
    "tests/**"
  ],
  "timebox": "Half a day of work, plus the time the readers take (waiting does not count). Past that, stop and re-plan.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "the Pages guard is fixed (023's parked review finding) and the deploy is retried (revision 2026-11-22)",
      "then": "the guard fails **red**, not green, when its own `git ls-remote` lookup returns nothing: the draft `changes/024-.../proposed/pages.yml` differs from 023's only by an empty-head check (`if [ -z \"$head\" ]` with an `::error::` and `exit 1`) and its header line. **It also retries the deploy** (owner decision, 2026-11-22): both deploys so far failed on the first attempt (`deploy-pages@v5` could not yet see the artifact `upload-pages-artifact@v5` had uploaded seconds before; runs 45067874062 and 45069382246) and succeeded on a re-run, so the deploy step gets `continue-on-error: true`, a `sleep 30` step and a second `deploy-pages@v5` step (`id: retry`) run only `if: steps.deployment.outcome == 'failure'`, and the environment's URL takes the retry's output first; the job still fails if the retry fails. The diff test lists every added line (the guard check, the header, the retry) and asserts nothing else changed; a test checks the retry's lines (whole lines, comments stripped). The owner commits it to `.github/workflows/pages.yml` on the change branch under `allow-governance` (block B1). 023's byte-for-byte test is re-pointed to 024's draft; a test asserts the two drafts differ only in those lines; and **a behaviour test** extracts the guard step's script from the committed workflow and runs it with `bash` and a fake `git` on the `PATH` that prints nothing, requiring a nonzero exit and the `::error::` line (bash is on CI's runner and in Git for Windows; the test fails, never skips, if it is missing). `docs/pages.md` says to re-run **all** jobs of a pages run, never only a failed deploy, so the guard checks main's head again, and names 024's draft as the one the byte-for-byte test checks; a docs test checks both. The fix's first live run happens after this change's merge and is noted then, not made a criterion (L-020).",
      "test": "ci.test_workflow.WorkflowTests.test_ac2_023_pages_workflow_deploys_only_current_tested_head (re-pointed), test_ac1_024_guard_fix_is_the_only_difference, test_ac1_024_guard_fails_red_on_empty_lookup (behaviour), test_ac1_024_deploy_retry, test_ac1_024_pages_docs",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "the portfolio card is published",
      "then": "a test checks the draft `changes/023-.../proposed/portfolio-card.md`: the existing cards' sections (a level-three heading, a bold stage line, Problem, What it does, Why it's trustworthy, an 'Under the hood' fold, the links), no digit outside the two URLs, a link to `https://neifertg.github.io/audit-knowledge-graph/` and one to the source repository. It has no demo GIF, unlike the other cards: deliberate for now (the live page is the demo), and the owner may add one later. The owner commits it to `risk-analytics-portfolio`'s `index.md` as the first card under `## Projects` (block P, or the agent at the owner's explicit request in this conversation; that repository is outside capitan's areas and gate). **The portfolio check**, recorded in `docs/pages.md`: the card's text in the portfolio's default-branch `index.md` equals the draft (whitespace-normalised), it is the first card under `## Projects`, and the published portfolio (`https://neifertg.github.io/risk-analytics-portfolio/`) serves a page containing its heading and the live-page link.",
      "test": "ci.test_workflow.WorkflowTests.test_ac2_024_portfolio_card_draft, plus the recorded portfolio check",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "the reader test is run",
      "then": "**before the script goes out**: the agent adds to `script.md` a consent line for readers (their sentence may be published, without their name, in the project's public repository; they can say no) and a redaction rule (any name in a reply is replaced by a role before it is recorded); the owner confirms the live page in light and dark and on a phone; and the agent records that confirmation and the page's deployed commit (from the latest pages run whose guard reported current) in `docs/pages.md` and at the top of `research/o1-reader-test/results.md`, so the record says which build the readers saw. The owner sends `script.md` to three readers and gives each reply, by role only, for `results.md`. **Independent judging, with evidence:** for each answer the agent commits its judgment to `results.md` first, and the owner's judgment is added in a later commit, so the commit order shows the agent judged without the owner's; the stricter reading stands. If a reader never replies, the owner records a decision in `results.md` (replace that reader with another who has not seen the page, recorded as such); fewer than three answers is never a pass. **This criterion passes when three answers are recorded and judged (redacted, by role) and `decision.md`'s Decision line reads `GO` or `NEEDS-CLARIFICATION` with no TODO left, whatever the outcome:** GO when at least 2 of 3 pass (M1's O1 condition met). **On a miss** (NEEDS-CLARIFICATION), before review: the agent runs `capitan revise 004` on main and adds a child e (the top-section revision and a re-test with readers who have not seen the page); that revision gets its own critique and the owner's approval on main; then main is merged into this change's branch, so the branch carries the approved epic and capitan's check of this child passes. The epic's close check then refuses while e is open, keeping the epic and M1 open.",
      "test": "check: results.md has the deployed commit, three role-only redacted answers verbatim, both judgments (the agent's committed before the owner's) and the result; decision.md's Decision line is GO or NEEDS-CLARIFICATION with no TODO; on a miss, main's epic 004 is approved, unchanged since approval, lists child e, and the branch's epic.md equals main's. ci.test_workflow.WorkflowTests.test_ac3_024_reader_record (the consent line and redaction rule in script.md; no denied real name and no email address in results.md)",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the live check is recorded, as late as possible before this change finishes",
      "then": "a **point-in-time record** in `docs/pages.md`'s 'Live check' section: the pages run, its commit and the time; that commit equals **origin/main's head** at that moment (read with `git ls-remote`), after waiting for that head's own pages run to finish; a build of that commit in a fresh `git worktree` (`python -m src.features.site.build`) equals the live page **byte for byte** in all six files (`index.html`, `site.css`, `site.js`, `site.json`, `rounds.json`, `scores.json`), with one retry a minute later for the Pages cache; and whether the build output differs from the build the readers saw (AC-3's commit). Later deploys whose build output is unchanged (this change's merge, knowledge commits) do not reopen it. A test checks the section is filled with these fields (the commit, the six file names, 'byte for byte', the time), not that the page is live.",
      "test": "ci.test_workflow.WorkflowTests.test_ac4_024_live_check_recorded (fields present), plus the recorded check",
      "status": "pending"
    }
  ],
  "epic": "004-e4-page-v1-and-publish",
  "child": "d",
  "revised": "2026-11-22"
}
```

## Why
E4 child d (O1, and M1's last open condition). The page is live (023, run 45067874062, commit `d415a6c`). This change proves the live page is the tested build, puts it in front of the hiring audience through the portfolio, fixes the guard's one weak spot, and runs the reader test that M1's O1 objective is judged by.

## Order
1. The agent's branch work: the guard draft and tests (AC-1), the card test (AC-2), the docs.
2. **The owner confirms the live page** (light, dark, phone); the agent records it and the deployed commit (AC-3).
3. **Block P:** the owner commits the card to the portfolio (or asks the agent to); the agent records the portfolio check (AC-2).
4. **The owner sends the script** to three readers; answers come back over days; both judge them (AC-3).
5. **Block B1** (any time before review): the owner commits the guard fix on the branch under `allow-governance`; the agent runs the full suite on a fresh checkout (L-022); **B2** pushes the branch.
6. **On a reader-test miss only:** the epic revision adding child e, critiqued and approved on main, then main merged into this branch (AC-3).
7. **The live check** (AC-4), as late as possible; then review and finish; the owner merges and pushes, which redeploys the same build output; the guard fix's first live run is noted then.

## Owner blocks (complete, given in turn; L-001)
- **B1** on `change/024-...`: `capitan allow-governance`, copy `changes/024-.../proposed/pages.yml` to `.github/workflows/pages.yml`, commit with `-m`; no push. **B2:** push the branch.
- **P** (portfolio, another repository): clone or open `risk-analytics-portfolio`, insert the card's text as the first card under `## Projects` in `index.md`, commit with `-m`, push. The agent gives the exact block, with the card text, when it is time.
- **On a miss only:** approve the epic revision (`capitan approve 004`, committed on main), then merge main into the change branch: `git switch change/024-...`, `git merge --no-edit main`.
- **Merge:** `git switch main`, `git merge --no-ff --no-edit change/024-...`, prune, `git push origin main`.

## Revision 2026-11-22: retry the deploy
After approval, the Pages run for `890d53b` failed the same way as the first deploy (the guard passed, the upload succeeded, then `deploy-pages@v5` found no artifact). Two first attempts out of two is a pattern, so every push would have needed a manual re-run. The owner chose a retry in the workflow over pinning older action versions or a separate change: if the deploy step fails, the job waits 30 seconds and deploys once more. The page stayed live on the tested `d415a6c` build throughout (the later commits change no page file).

## Data impact
None.

## Test plan
AC-1's, AC-2's and AC-4's tests in the suite; AC-2's portfolio check, AC-3 and AC-4's live comparison are recorded checks the review reads. Per L-022, the full suite runs on a fresh checkout of B1's commit before B2.

**Evidence** (pre-plan, 2026-11-22): the page is live; Pages builds from the workflow; the portfolio is served by classic Pages at `https://neifertg.github.io/risk-analytics-portfolio/`; the guard draft differs from 023's by four lines and the header (`git diff --no-index`).

## Risks
- **Readers are slow or one never replies.** The change waits; the timebox counts work, not waiting. Fewer than three answers is never a pass; the owner's recorded decision replaces a silent reader with another who has not seen the page.
- **A reader's words are published.** The script asks consent, names are redacted to roles, and a test scans `results.md` for real names and email addresses.
- **Judging drifts after seeing answers.** The rule and examples were fixed in 023; the agent's judgment is committed before the owner's, so the commit order is the evidence; ties go to the stricter reading.
- **A redeploy during the wait changes the page.** AC-3 records the readers' build; AC-4 records whether the final build differs from it.

## Out of scope
- The top-section revision on a miss (a new child e, added by epic revision before this change finishes).
- M1's milestone close (the milestone playbook, after the epic closes).

## Relevant lessons
- **L-020:** the live check and the guard's first live run are recorded, not tested in the run that deploys.
- **L-022:** the fresh-checkout run before B2.
- **L-023:** the epic critique's two carried minors are pinned here: the child-e rule on a miss (AC-3) and the readers' build in `results.md` (AC-3).
- **L-024:** the guard fix makes the guard fail red when its own lookup fails.

## Slices
1. Branch work and tests (AC-1, AC-2's test, AC-4's test); docs.
2. The owner's live confirmation; the card; the script sent.
3. The answers, judged; B1, the fresh-checkout run, B2.
4. The live check; review; finish; the merge.
