# Organization, regulations, taxonomies and audit universe

Change `006-organization-regulations-taxonomies-and` · objective **O3**: It shows, and measures, the realistic hard part: reconciling ERM's and IA's separate risk taxonomies, risks and controls into one framework (ERM's Basel-style taxonomy). Signal: precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue rather than being merged silently.

## Why
The milestone needs a bank that reads as real at full size: an audit universe of about 80 auditable entities across believable business units, about 120 people, 30 systems, 15 regulations, and two taxonomies at real breadth that map unevenly. Children c-e hang risks, controls, audits and issues on this structure, and E3's rounds (shared-system blast radius, regulation-to-business-unit paths) need it to be dense enough to be interesting.

## Acceptance criteria

| ID | When | Then | Test | Builder | Reviewer |
|---|---|---|---|---|---|
| AC-1 | `python -m akg build --size full --seed 42 --out <dir>` runs | b's entities are at full size within the epic's ±10%: auditable entities 72-88, people 108-132, systems 27-33, regulations 14-16; plus segments exactly the 7 in docs/data-model.md, business units 25-35, processes 80-160; every auditable entity performs at least one process; at least 80% of processes run on a system; every relationship file b owns (has, owns, performs, runs_on, parent_of x2) has rows. Entities c-e own stay at sample size in this change | `generator.test_full_build.FullBuildTests.test_ac1_full_build_org_counts_within_targets` | pass | PASS |
| AC-2 | either size is built | each taxonomy (ERM, IA) is a strict three-level tree: every L1 has no parent, every L2 and L3 node has exactly one parent one level up, there are no cycles, sibling names are unique; ERM's L1 set is exactly Credit, Market, Liquidity, Operational, Compliance, Strategic, Reputational; at full size ERM has 60-120 nodes with at least 2 L2 under every L1, and IA has 40-100 nodes (INV-1, taxonomy part) | `generator.test_invariants.InvariantTests.test_ac2_inv1_taxonomies_are_strict_trees` | pass | PASS |
| AC-3 | either size is built | every auditable entity is owned by exactly one business unit and every business unit belongs to exactly one segment (INV-2) | `generator.test_invariants.InvariantTests.test_ac3_inv2_each_entity_has_exactly_one_owner` | pass | PASS |
| AC-4 | the full build has run | answer_key/taxonomy_map.csv covers every IA node exactly once at an allowed level (child a's consistency rules), and maps unevenly: at least 1 IA L1 branch unmapped throughout, at least 4 IA nodes mapped to a shallower ERM level, of which at least 2 are IA L3 nodes mapped to an ERM L2; and stays mostly mappable: unmapped IA nodes are at most 20% of IA nodes, and shallower-level mappings at most 40% | `generator.test_full_build.FullBuildTests.test_ac4_full_taxonomy_map_consistent_and_uneven` | pass | PASS |
| AC-5 | the build runs at either size after this change | the default text is AI-written (`--text ai`, per R2) at sample size; at full size it defaults to templated until c-e generate full-size AI text (the explicit `--size full --text ai` case is AC-9). In slice 1, before any content change, only the CLI default switches and tests/golden/checksums.sha256 is regenerated from that otherwise unmodified code; it is not regenerated again in this change, so the final sample build matching it proves b changed no sample output beyond the text default. A new tests/golden/checksums_full.sha256 (written by `python -m tests.generator.golden --size full`) covers the full build (INV-7 at both sizes) | `generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and generator.test_determinism.DeterminismTests.test_ac5_full_build_matches_full_golden; plus `git log --oneline main.. -- tests/golden/checksums.sha256` shows exactly one commit (slice 1)` | pass | PASS |
| AC-6 | the full build has run | child a's size-independent checks, moved into shared helpers that a's existing tests and this test both call, hold at full size too: referential integrity and no cross-source links (INV-10), data dictionary matches output, name columns come from their lists and no text names a real institution (INV-9), and changing `--count REGULATION` leaves every file not naming regulations unchanged. (Revision 1: the `--count PERSON` clause was dropped: issue owners share the issue random stream, so the person count shifts issue draws, and fixing that changes sample issue output, which AC-5 forbids here. Parked for child e.) | `generator.test_full_build.FullBuildTests.test_ac6_child_a_checks_hold_at_full_size` | pass | PASS |
| AC-7 | either size is built | titles that a bank has one of (Chief Credit Officer, Chief Risk Officer, Chief Audit Executive, Chief Information Security Officer, Treasurer, Controller, BSA Officer, General Counsel) appear at most once each in person.csv; other titles may repeat | `generator.test_invariants.InvariantTests.test_ac7_one_per_bank_titles_are_unique` | pass | PASS |
| AC-8 | the full build has run | no system is orphaned (each runs at least one process); at least 8 systems run processes of auditable entities in 3 or more business units, and at least 3 of those span 2 or more segments, so E3's shared-system round has real blast radius | `generator.test_full_build.FullBuildTests.test_ac8_systems_are_shared_across_units` | pass | PASS |
| AC-9 | `python -m akg build --size full --text ai` runs before children c-e generate full-size AI text | it exits non-zero before writing any file, with a message saying AI text exists only at sample size so far and to use `--text templated`; the refusal is a deliberate size check in the generator, not the per-item stale-text check, so no item can silently receive sample AI text at full size and the message never suggests regenerating (which would spend unapproved API budget). Children c-e remove the check when they add full-size AI text. | `generator.test_full_build.FullBuildTests.test_ac9_full_size_explicit_ai_text_fails_loudly` | pass | PASS |

## Review in this order

1. **src/features/generator/****: `src/features/generator/cli.py`, `src/features/generator/generate.py`, `src/features/generator/library.py`, `src/features/generator/names/first_names.txt`, `src/features/generator/names/last_names.txt`, `src/features/generator/names/regulations.txt`, `src/features/generator/names/systems.txt`, `src/features/generator/names/titles.txt`, `src/features/generator/names/vendors.txt`, `src/features/generator/sample_pack.py`
2. **akg/****: `akg/__main__.py`
3. **Tests**: `tests/generator/checks.py`, `tests/generator/golden.py`, `tests/generator/test_answer_key.py`, `tests/generator/test_data_dictionary.py`, `tests/generator/test_determinism.py`, `tests/generator/test_full_build.py`, `tests/generator/test_invariants.py`, `tests/generator/test_names.py`, `tests/generator/test_referential.py`, `tests/golden/checksums.sha256`, `tests/golden/checksums_full.sha256`

## Data impact
- **Sizes.** Adds `--size full`. In this change, full size scales only b's entities (segment, business unit, auditable entity, process, system, person, regulation, both taxonomies) and their relationships (has, owns, performs, runs_on, parent_of). Risks, controls, audits and issues stay at sample size until c-e. The default stays `sample` until child e makes full size the default.
- **Sample output is unchanged** except the text default: full-size content is a superset, and sample mode keeps selecting exactly the rows it selects today. So the sample pack and child a's results stand.
- **Text default.** Per R2's decision, `--text` defaults to `ai` at sample size; `--text templated` stays. Golden checksums regenerate for that one reason. At full size the default is `templated` until c-e write full-size AI text: sample AI text cannot apply to full-size issues (their draws differ), and the build must never mix the two silently.
- **Revision 1 (2026-11-20).** AC-6's `--count PERSON` independence clause is dropped and parked for child e. Issue owners are drawn from the issue stream, so the person count shifts every later issue draw; moving owners to their own stream changes sample issue output, which AC-5 forbids in this change. Child e rebuilds issues at full size and regenerates the goldens anyway.
- **Taxonomy answer key.** The epic gives `taxonomy_map.csv` to child c, but a's consistency rules require every IA node in it, so b extends the true IA-to-ERM mapping for every node it adds. c still owns risk-level truth (`risk_clusters.csv`, misfiled risks).
- **Content** lives in `library.py` and `names/*.txt`: about 80 auditable entities grouped under 25-35 business units, about 120 processes with their systems, 30 systems with fictional vendors and criticality, 15 real US regulations, an ERM taxonomy (Basel-style L1, banking L2/L3) and a legacy IA taxonomy organized by audit area. New fictional names (vendors, systems, titles) pass the deny-list.
- **Invariants.** INV-1 (taxonomy part) and INV-2 get named tests, replacing `TBD (E1)` in `docs/data-model.md`. INV-7 gains a full-size golden: its "Enforced by" lists both the sample test (AC-3 of 005) and `test_ac5_full_build_matches_full_golden`. No new entities, columns or relationships.
- **Areas.** `akg/**` is needed because `--size` choices and the `--text` default are defined in `akg/__main__.py` (the epic listed it for child a only because a created it); the edit is limited to those two options. `requirements.txt` is not touched: no package changes.
- **Titles.** One-per-bank titles (C-suite, Treasurer, Controller, BSA Officer, General Counsel) are assigned at most once; other titles repeat (AC-7). Sample mode keeps its current 20 people and titles.
- **Shared systems.** Process-to-system links are b's alone, so b makes them dense enough for E3's blast-radius round (AC-8).

## Risks
- **Hand-writing ~80 auditable entities and ~120 processes is slow.** Cheapest signal: draft the org table first and time it; if it runs past half a day, re-plan rather than cut realism.
- **Sample mode drifting.** Changing shared lists (e.g. appending systems) could shift sample-size draws. Guard: sample mode reads fixed slices of each list, and AC-5 compares against the pre-change outputs.
- **Taxonomies that c cannot use.** c needs ERM L3 homes for many more risk concepts. Mitigation: design L3 nodes around real bank risk categories, and c may add nodes through its own plan.
- **Realism.** The owner reviewed a's sample only; full-size names and structure get a quick owner skim at review time (the full build's org table, rendered by the existing pack code into a temp file on request).

## Deliberately not in this PR
- Risks, controls, audits, issues at full size: c, d, e.
- AI text at full size: c-e, after the owner approves the cost (R2 Next).
- A vendor entity for E3 round 5: parked (vendors stay a system attribute here).
- Making full size the default: e.

Parked for later:
- 2026-11-20 E1 child c: IA risks filed under an unmapped IA node always count as misfiled; with up to 20% unmapped IA nodes (006 AC-4), place IA risks so misfiled stays within the epic's 10-20% (from 006-organization-regulations-taxonomies-and)
- 2026-11-20 E1 child e: move issue owners onto their own random stream (issue_owned_by_person) so --count PERSON leaves issue files unchanged; dropped from 006 AC-6 because it changes sample issue output (from 006-organization-regulations-taxonomies-and)
- 2026-11-20 E1 children c-e: the full-size AI-text guard from 006 AC-9 is all-or-nothing; c and d narrow it to entity types still lacking full-size AI text, e removes it (from 006-organization-regulations-taxonomies-and)
- 2026-11-20 Governance follow-up (owner at a terminal): .claude/skills/capitan-plan/SKILL.md still says 'Never run approve yourself'; align it with AGENTS.md rule 2's relay exception (needs capitan allow-governance) (from 006-organization-regulations-taxonomies-and)
- 2026-11-20 E1 sample mode: --count PERSON above 20 repeats one-per-bank titles (sample cycles the first 20 titles); harmless at defaults, fix if sample counts ever grow (review of 006) (from 006-organization-regulations-taxonomies-and)
- 2026-11-20 E1 children c-e: decide what 'check-text --size full' means once full-size AI text exists (review of 006) (from 006-organization-regulations-taxonomies-and)
- 2026-11-20 E1 child c: full-size sample pack intro still says '~15 rows' and asks for a text choice; reword when no AI text is shown (review of 006) (from 006-organization-regulations-taxonomies-and)

## Lessons recorded
- L-005 Give every per-row choice its own random stream from day one
- L-006 Check new criteria against output-freezing criteria before approval

## Verification
- Plan critique: READY
- Code review: PASS on code fingerprint `8ac1c36e3eae53a3`
- Size: 22 code files, +981 / -122 lines
