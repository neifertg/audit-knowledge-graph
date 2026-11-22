VERDICT: READY
1. [minor] "this epic and M1 are closed only after a recorded pass ... whatever d's status" is a stated rule, not a gate. `capitan` (cli.py:742) closes the epic once every child is done or dropped, and d can now finish on a miss, so after a miss every child would be done and the epic would close mechanically with O1 unmet; "the revision of the top section is a new change" does not say whose child it is. -> Say that on a miss the revision (and its re-test) is added to this epic as a new child (child e, via `capitan revise`), so the existing close check holds the epic open until a recorded pass or the owner's recorded decision.
2. [minor] The live check of record is taken "as late as possible before d finishes", after the readers have read the page, so it does not show which build the readers saw. d's areas cannot change the build output, but another change merged to main during the reader window could. -> Record in `results.md` the deployed commit when the script goes out (the owner's confirmation already sits at that point), and if the late live check finds a different build output, say so beside the results.

Previous round's items, all answered in d:
- 1 (major, unreachable done condition): d's criterion is now answers recorded, judged and written into `results.md` and `decision.md` whatever the outcome; M1's O1 condition stays 2 of 3; the epic and M1 close only after a recorded pass or the owner's decision after a second miss. Answered (see issue 1 for the mechanics).
- 2 (major, live check vs. d's own merge): point-in-time record, as late as possible, with run, commit and time; later deploys with unchanged build output do not reopen it, a build-output change repeats it; the guard fix is judged by its test and by reading, its first live run noted after merge (L-020). Answered.
- 3 (card draft untested): a test of `changes/023-.../proposed/portfolio-card.md` (sections, no figures, the two links); the file exists. Answered.
- 4 (partial re-run): `docs/pages.md` to say re-run all jobs. Answered.
- 5 (owner confirmation unrecorded): recorded in `docs/pages.md`'s 'Live check', before the card or reader test go out. Answered.
- 6 (portfolio repo outside areas): stated, with the published portfolio showing the card and its link opening the live page as the evidence. Answered.
- 7 (change number): d is named change 024. Answered.

Facts checked: `changes/023-publish-on-github-pages-portfolio-card-a/proposed/` holds `pages.yml` and `portfolio-card.md`; `research/o1-reader-test/` holds `script.md`, `results.md`, `decision.md`; `docs/pages.md` has 'Live check' ("Filled in by change 024 after the first deploy"); cli.py:742 treats done or dropped children as not blocking the epic.
Not checked: the live page and the Pages runs (d's job); the content of the card draft against the portfolio's existing cards; where d's guard-fix draft will live (presumably `changes/024-.../proposed/`, which the plan for 024 should name).
