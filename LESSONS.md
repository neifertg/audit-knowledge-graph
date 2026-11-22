# Lessons

One entry per lesson, added with `python -m capitan learn "<title>" --area <a,b> --body "..."`.
Plans search this file automatically. A lesson that keeps recurring should become a check (a test, a lint rule, a hook), not a longer entry.

Format: `### L-NNN (YYYY-MM-DD) [areas] Title`, then what happened and what to do next time.

### L-001 (2026-11-20) [workflow] Owner-run commands: copy-paste blocks, never an editor
When the owner must run something (capitan approve, capitan allow-governance, committing a governance file such as .gitignore), give one complete PowerShell block to paste, including branch switches and the allow-governance step. Never give a git command that opens an editor: use git merge --no-edit, git commit -m, git commit --no-edit. A plain git merge dropped the owner into Vim (2026-11-20).
Source: 005-sample-pack-for-realism-review
Scope: general

### L-002 (2026-11-20) [src/features/generator] AI rewrites invent facts unless code enforces the rule
Asked to rewrite drafts, claude-opus-5-5 added system names absent from the draft (even when the prompt said not to) and expanded brief ERM controls into detailed ones, which made matched ERM/IA pairs too similar (killed hard negatives) and less realistic. Next time: state the rule in the prompt AND check it in code with a retry plus a test (write_text.added_systems); regenerate the whole set after any prompt change so all text shares one prompt.
Source: 005-sample-pack-for-realism-review

### L-003 (2026-11-20) [src/features/generator] Cross-source text needs shared domain vocabulary for realistic near-misses
ERM risk statements and IA audit-universe entries shared almost no words, so TF-IDF found no hard negatives (non-match >= matched median). Prefixing IA entries with their audit area and letting sibling scopes overlap fixed it realistically. At ~15 rows the hard-negative check is fragile (0.18 vs 0.19 margins); children c/d should measure it at full size before tuning content.
Source: 005-sample-pack-for-realism-review

### L-004 (2026-11-20) [workflow] capitan rescue runs from main and leaves files uncommitted
capitan rescue <id> refuses on the change branch ('switch to main first'), copies knowledge into main's working tree, and expects you to commit there; the branch switch back then fails until you commit. Sequence: commit on branch, git switch main, capitan rescue <id>, commit on main, git switch back, git merge --no-edit main.
Source: 005-sample-pack-for-realism-review

### L-005 (2026-11-20) [src/features/generator] Give every per-row choice its own random stream from day one
rng.choice consumes a variable number of random bits depending on the list length, so drawing issue owners from the issue stream made the person count shift every later issue draw (006). Fixing it later changes existing output and conflicts with criteria that freeze it. Next time: any draw from another entity's population (owners, links) gets its own stream named after the relationship file, from the first commit.
Source: 006-organization-regulations-taxonomies-and

### L-006 (2026-11-20) [workflow] Check new criteria against output-freezing criteria before approval
006's AC-5 froze sample output while AC-6 demanded a --count PERSON independence that could only be reached by changing sample output; the conflict surfaced mid-build and cost a plan revision. Next time: when a plan freezes existing output, check every other criterion for whether it needs that output to change, and probe the code (one quick run) before approval.
Source: 006-organization-regulations-taxonomies-and

### L-007 (2026-11-20) [src/features/generator] Measure difficulty early and tune content, not thresholds
007's 2-hour checkpoint measured all 12 difficulty bands on the first 80 instances. Only within-ERM duplicate detection failed (0.10 vs 0.30 floor): same-theme siblings were near-copies (cosine 0.87), so no duplicate could stand out. Realistic variation fixed it (team-specific sentence frames and wording, duplicates keeping their original's statement), raising it to 0.375 at full size without loosening any band. Next time: build the measurement helper first (tests/generator/difficulty.py), run it at the checkpoint, and use one sorted sweep for best-threshold F1 (the naive loop timed out at 27,000 pairs).
Source: 007-erm-and-ia-risk-populations-with-answer

### L-008 (2026-11-20) [src/features/generator] Any exact shared phrase becomes a lookup key; measure it
008: to lift control TF-IDF above its 0.40 floor, IA text cited ERM's exact title words; a title-in-description lookup then paired generic controls at F1 0.76. Rewording IA's kind label dropped it to 0.30 while TF-IDF stayed 0.44, but ERM's subject phrase still gives F1 0.64-0.78 with a small hand map (owner accepted as a realistic cue, documented). Next time: whenever shared vocabulary is added to help text matching, add the matching exact-phrase lookup as a measure in the same change and decide consciously which cues are realistic.
Source: 008-erm-and-ia-control-populations-with-answ

### L-009 (2026-11-20) [src/features/generator] Planted scenarios need a completeness rule, not just a minimum
009 listed the 6 planted repeat-finding groups, but 9 more controls had issues in two years by chance, so E3's obvious query would have scored correct answers as false positives. The fix: keep non-planted items out of the scenario (one year per control) and test listed == every qualifying item. Next time: for every planted scenario, define the qualifying set from published data and require the answer key to equal it exactly; also say which seeds the targets are guaranteed for.
Source: 009-three-years-of-audits-and-issues-with-pl

### L-010 (2026-11-21) [src/features/generator] AI paraphrase erases shared-wording cues; tune derived text in both directions
010: rewriting every description independently dropped control TF-IDF F1 0.44->0.28, ERM duplicate F1 0.38->0.13 and the repeat-finding text cue to 0. Rewriting duplicates from their original's AI text first overshot (0.93, near-copies), then a looser note undershot (0.16); a middle note (keep the impact sentence, own words for cause and event) landed at 0.60. Next time: measure every band on AI text before the full batch (a small pilot is cheap), generate dependent items (duplicates, repeats) from their source's AI text, and expect to calibrate the per-item note once in each direction.
Source: 010-full-size-ai-text-in-one-batch

### L-011 (2026-11-21) [src/features/generator] Check-only allowances must stay out of prompt-listed name files
010: adding 'IDs' to allow_terms.txt to fix a rule false positive silently changed the full prompt version (the prompt lists allow_terms), which would have marked all 1,274 paid entries stale; test_sample_prompt_is_pinned caught it. Next time: words the rule check may accept but the prompt need not list go in text_rules.RULE_ONLY_WORDS, never in a file the prompt reads.
Source: 010-full-size-ai-text-in-one-batch

### L-012 (2026-11-21) [src/features/reconciliation] Quote the built module's figures, not the pre-plan experiment's
011: the plan's bars came from a scratch experiment whose tie-break (highest ERM node ID, not lowest) and small details differed from the pinned method, so the build measured 44/62 not 46/62 on seed 42 (seeds 7/1 moved by +-0.02). The bars had margin, so nothing failed. Next time: implement the experiment with the same constants the plan pins (or re-measure with the module before the plan is approved), and downstream plans quote the figures recorded in docs/data-model.md from the build, never the plan's pre-plan numbers.
Source: 011-map-ia-taxonomy-onto-erm-taxonomy

### L-013 (2026-11-21) [src/features/reconciliation] Learned models must transfer across text styles: use scale-free features and converge the fit
012: a model trained on templated text (seed 7) missed 10 of 13 AI-text duplicates with raw cosine features, because templated duplicates are near-copies and AI ones paraphrases. Within-bank percentiles fixed transfer but, with class_weight='balanced' and 13 positives, bunched duplicate scores within 1e-5; a tail transform -log10(1-p+1/n) spread them. sklearn's default tol=1e-4 stopped lbfgs early (coefficients moved up to 0.38 when converged). Next time: make similarity features relative to their own bank, check score spread near thresholds, pin tol tightly before comparing retrains, and route kinds with too few positives to review-only.
Source: 012-match-features-training-script-and-commi

### L-014 (2026-11-21) [tests] Estimate test-suite cost by counting the builds each new step adds
013: adding reconciliation (about 7 s per full build) to akg build took the suite from about 65 s to about 180 s; the plan estimated 30-40 s because it counted only some direct run_akg callers. Next time: before adding a step to the build, grep every test path that builds (helpers.build, run_akg('build'...), subprocess builds) and multiply by the step's time; give generator-only tests an opt-out flag (--no-reconcile) from the start.
Source: 013-canonical-layer-review-queue-and-build-s

### L-015 (2026-11-21) [src/features/reconciliation] Check published caveats against the code that builds the candidates
014: the first plan claimed orphan controls were excluded from the pair figures and could not inflate them; features.control_table actually puts every control in the candidate pairs, so orphans are easy negatives that help precision (0 merged, 2 queue rows). The epic's wording ('helps the figures, not matcher skill') was right. Next time: before writing any sentence about what a published figure includes or excludes, trace the candidate set in code and add a figure that shows it (here: orphans merged and queued).
Source: 014-score-reconciliation-against-the-answer

### L-016 (2026-11-21) [src/features/reconciliation] A fingerprint over source code ripples into every artifact that copies it
015: adding --no-load to train.py's build changed train.py's source, which the training fingerprint hashes; that moved weights.json's fingerprint and, because score.py copies it into provenance, scores.json too. Two critique rounds found the chain one link at a time. Next time: before editing any fingerprinted file, grep for every place the fingerprint is stored or copied (weights.json, scores.json, later rounds.json) and plan to regenerate all of them, proving with git diff that only the fingerprint line moved.
Source: 015-sqlite-schema-and-loader

### L-017 (2026-11-21) [tests] On a low-memory machine, reviewers must not wait on long test runs
016: this machine has 7.6 GB RAM; with VS Code, Zoom, Chrome and Neo4j open it hit 87-90% memory and Windows memory compression, and test runs slowed 10-30x (Neo4j module 61 s vs 28 min; full suite 3 min vs 37 min). A review subagent that started the tests in the background and waited was killed by the 600 s watchdog with no review written. Next time: the main session runs the slow tests to a log file in the scratchpad and the reviewer reads that log; ask the owner to close other apps before long runs; check memory with Get-CimInstance Win32_OperatingSystem when timings jump.
Source: 016-neo4j-loader-with-fact-parity

### L-018 (2026-11-21) [src/features/rounds] Measure a comparison metric on the prototypes before approval, and normalise schema artifacts out of it
017: the first verdict rule charged SQL a moving part for every UNION ALL over the per-source tables, so every round would have come out 'graph': it measured our one-table-per-source schema, not SQL vs Cypher; and line counts let wrapping flip a boundary verdict. Two critique rounds found it only because the plan gave no measured figures. Fix: shared views as published setup (the analogue of Neo4j's shared labels), clauses not lines, symmetric counting of subqueries/unions. Next time: for any scoring rule that a page will publish, run it on the prototype inputs and put the results (and which are near a boundary) in the plan before critique; give both sides the same normalisation and score the setup cost separately.
Source: 017-rounds-1-4-paired-sql-and-cypher-with-ag

### L-019 (2026-11-21) [src/features/rounds] Audit a scoring rule's symmetry as a table of constructs, not one critique at a time
018: the verdict rule's asymmetries surfaced one per review round: a SQL JOIN counted as clause and step (critique 1), fixed Cypher *n as one hop (critique 1), a recursive CTE as 3 moving parts vs Cypher's 1 (critique 2), and Cypher write clauses as clause plus moving part vs SQL's moving part only (code review, parked). Each found late cost a plan revision or a parked item. Next time: before planning, list every construct class (join/hop, variable-length, subquery/stage, recursion, union, write/DDL, optional match) with what it adds to each metric on each side, and require each to count the same on both sides or be disclosed; put that table in the plan.
Source: 018-rounds-5-7-owner-concentration-and-the-r

### L-020 (2026-11-21) [tests] A test that runs in CI must not require evidence of its own CI run
019: the AC-4 doc test first required the URL of the first green CI run in docs/ci.md, but that test runs inside the very CI run whose URL it needs, so the first run could never go green; the local CI-environment rehearsal caught it before the push. Later, a doc edit broke a case-sensitive phrase check and a chained command committed it anyway. Next time: record post-run evidence (URLs, timings) as a reviewed doc step, not a test; make doc phrase checks case-insensitive; and gate commits on the test result (commit only if the run printed OK).
Source: 019-github-repo-and-ci-with-a-neo4j-service
