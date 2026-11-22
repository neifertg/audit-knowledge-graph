VERDICT: READY
1. [minor] Round-1 item 3 asked that the superseded build stay visible. The new precondition 3 says 024 re-records the build "in `docs/pages.md` and `results.md`, replacing `7d9c32e`". "Replacing" could be read as deleting the line that records what the owner confirmed on 2026-11-22. -> When 024 does the re-record, keep the `7d9c32e` line and mark it superseded (by 025's deployed commit) instead of overwriting it. This is a note for 024's work, not a 025 criterion. It does not block approval.

Round-1 items, checked against the revised plan:
- Major 1 (teaser count claim and "length"): answered. The teaser now reads "scored by a published rule: SQL wins [once], the graph [three times], and [three] are close". That is verdict language tied to the rule, so it is correct under the rule even though Cypher's score is lower in round 3 as well. The disclosure keeps 021's exact wording ("how much query each needs, not speed"), which matches the string already in the tests' `COPY` list.
- Major 2 ('In short' overclaim, "year after year"): answered. The subject is now the linked records ("linking risks, controls, systems and issues, in the ERM register and Internal Audit's records alike"), so the IA-only repeat-finding story is no longer credited to the ERM-IA join. "in different years under different titles" matches the repeat-finding story's own sentence in `template.html`.
- Major 3 (hand-off to 024): answered. The new "Before the reader script goes out" section states the deploy and the possible re-run of all jobs (main's `pages.yml` still lacks 024's retry), the owner's re-confirmation in light, dark and phone, and 024's re-record of the deployed build. It is correctly framed as preconditions on 024, which 025 cannot satisfy inside its own `areas`.
- Minor 4 (record the post-pilot revision): answered by precondition 3 (024's `results.md` note citing 025, with the pass rule unchanged).
- Minor 5 ("now"): answered. The sentence ends "That is what audit planning can target."
- Minor 6 (test placement): answered. AC-1 now says the test checks the 'In short' paragraph is the first element after the `<h1>`, which matches the test plan.

Copy verified against the sources:
- `src/features/rounds/rounds.json`: 7 rounds, `measured_verdict` counts graph 3 (rounds 1, 6, 7), close 3 (rounds 2, 3, 4), SQL 1 (round 5). The teaser's rendered words come from `count_word`/`times_word`, giving "seven", "once", "three times" and "three". The bracketed figures in the copy match.
- Stories (`template.html`, `src/features/site/data/site.json`): the blast radius reaches 20 business units ("many business units"), the repeat finding is stated as "in different years under different titles", and owner concentration names two owners ("a few hands"). The 'In short' claims stay within what the stories show.
- Copy-rules scan, run on both new paragraphs with the bracketed figures and *[disclosure: ...]* removed: no digit outside {60, 1.25, M1, M2, L1}, no number word (one..twenty, dozen, half, once, twice), no speed word. "once" and "three times" appear only as rendered figures, so they are allowed.

Not checked: the rendered look (AC-2's owner visual check). No tests, Neo4j or deploy were run.
