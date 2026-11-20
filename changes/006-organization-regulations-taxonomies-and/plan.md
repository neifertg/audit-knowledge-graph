# Organization, regulations, taxonomies and audit universe

```json plan
{
  "id": "006-organization-regulations-taxonomies-and",
  "tier": "standard",
  "status": "approved",
  "created": "2026-11-20",
  "objective": "O3",
  "areas": [
    "src/features/generator/**",
    "tests/**",
    "docs/data-model.md",
    "akg/**"
  ],
  "timebox": "2 working days of build time. Past this, stop and re-plan with `capitan revise` (e.g. split the taxonomies from the organization); never drop criteria silently.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m akg build --size full --seed 42 --out <dir>` runs",
      "then": "b's entities are at full size within the epic's ±10%: auditable entities 72-88, people 108-132, systems 27-33, regulations 14-16; plus segments exactly the 7 in docs/data-model.md, business units 25-35, processes 80-160; every auditable entity performs at least one process; at least 80% of processes run on a system; every relationship file b owns (has, owns, performs, runs_on, parent_of x2) has rows. Entities c-e own stay at sample size in this change",
      "test": "generator.test_full_build.FullBuildTests.test_ac1_full_build_org_counts_within_targets",
      "status": "pending"
    },
    {
      "id": "AC-2",
      "when": "either size is built",
      "then": "each taxonomy (ERM, IA) is a strict three-level tree: every L1 has no parent, every L2 and L3 node has exactly one parent one level up, there are no cycles, sibling names are unique; ERM's L1 set is exactly Credit, Market, Liquidity, Operational, Compliance, Strategic, Reputational; at full size ERM has 60-120 nodes with at least 2 L2 under every L1, and IA has 40-100 nodes (INV-1, taxonomy part)",
      "test": "generator.test_invariants.InvariantTests.test_ac2_inv1_taxonomies_are_strict_trees",
      "status": "pending"
    },
    {
      "id": "AC-3",
      "when": "either size is built",
      "then": "every auditable entity is owned by exactly one business unit and every business unit belongs to exactly one segment (INV-2)",
      "test": "generator.test_invariants.InvariantTests.test_ac3_inv2_each_entity_has_exactly_one_owner",
      "status": "pending"
    },
    {
      "id": "AC-4",
      "when": "the full build has run",
      "then": "answer_key/taxonomy_map.csv covers every IA node exactly once at an allowed level (child a's consistency rules), and maps unevenly: at least 1 IA L1 branch unmapped throughout, at least 4 IA nodes mapped to a shallower ERM level, of which at least 2 are IA L3 nodes mapped to an ERM L2; and stays mostly mappable: unmapped IA nodes are at most 20% of IA nodes, and shallower-level mappings at most 40%",
      "test": "generator.test_full_build.FullBuildTests.test_ac4_full_taxonomy_map_consistent_and_uneven",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the build runs at either size after this change",
      "then": "the default text is AI-written (`--text ai`, per R2) at sample size; at full size it defaults to templated until c-e generate full-size AI text (the explicit `--size full --text ai` case is AC-9). In slice 1, before any content change, only the CLI default switches and tests/golden/checksums.sha256 is regenerated from that otherwise unmodified code; it is not regenerated again in this change, so the final sample build matching it proves b changed no sample output beyond the text default. A new tests/golden/checksums_full.sha256 (written by `python -m tests.generator.golden --size full`) covers the full build (INV-7 at both sizes)",
      "test": "generator.test_determinism.DeterminismTests.test_ac3_inv7_output_matches_golden_checksums and generator.test_determinism.DeterminismTests.test_ac5_full_build_matches_full_golden; plus `git log --oneline main.. -- tests/golden/checksums.sha256` shows exactly one commit (slice 1)",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "the full build has run",
      "then": "child a's size-independent checks, moved into shared helpers that a's existing tests and this test both call, hold at full size too: referential integrity and no cross-source links (INV-10), data dictionary matches output, name columns come from their lists and no text names a real institution (INV-9), and changing `--count REGULATION` leaves every file not naming regulations unchanged. (Revision 1: the `--count PERSON` clause was dropped: issue owners share the issue random stream, so the person count shifts issue draws, and fixing that changes sample issue output, which AC-5 forbids here. Parked for child e.)",
      "test": "generator.test_full_build.FullBuildTests.test_ac6_child_a_checks_hold_at_full_size",
      "status": "pending"
    },
    {
      "id": "AC-7",
      "when": "either size is built",
      "then": "titles that a bank has one of (Chief Credit Officer, Chief Risk Officer, Chief Audit Executive, Chief Information Security Officer, Treasurer, Controller, BSA Officer, General Counsel) appear at most once each in person.csv; other titles may repeat",
      "test": "generator.test_invariants.InvariantTests.test_ac7_one_per_bank_titles_are_unique",
      "status": "pending"
    },
    {
      "id": "AC-8",
      "when": "the full build has run",
      "then": "no system is orphaned (each runs at least one process); at least 8 systems run processes of auditable entities in 3 or more business units, and at least 3 of those span 2 or more segments, so E3's shared-system round has real blast radius",
      "test": "generator.test_full_build.FullBuildTests.test_ac8_systems_are_shared_across_units",
      "status": "pending"
    },
    {
      "id": "AC-9",
      "when": "`python -m akg build --size full --text ai` runs before children c-e generate full-size AI text",
      "then": "it exits non-zero before writing any file, with a message saying AI text exists only at sample size so far and to use `--text templated`; the refusal is a deliberate size check in the generator, not the per-item stale-text check, so no item can silently receive sample AI text at full size and the message never suggests regenerating (which would spend unapproved API budget). Children c-e remove the check when they add full-size AI text.",
      "test": "generator.test_full_build.FullBuildTests.test_ac9_full_size_explicit_ai_text_fails_loudly",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "b",
  "revised": "2026-11-20",
  "approved": "2026-11-20",
  "approved_hash": "264084f1b798384b"
}
```

## Why
The milestone needs a bank that reads as real at full size: an audit universe of about 80 auditable entities across believable business units, about 120 people, 30 systems, 15 regulations, and two taxonomies at real breadth that map unevenly. Children c-e hang risks, controls, audits and issues on this structure, and E3's rounds (shared-system blast radius, regulation-to-business-unit paths) need it to be dense enough to be interesting.

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

## Test plan
- Done check: `.venv\Scripts\python -m unittest discover -s tests -v`; every named test shows `ok`.
- Real builds through the CLI into temp directories; no mocks.
- Child a's tests keep the same names and assertions at sample size; their size-independent check logic moves into shared helpers in `tests/generator/`, which a's tests and AC-6 both call (no copies).
- Not tested here: risk, control, audit and issue volumes and quotas (c-e), AI text at full size (c-e, after the owner approves the cost per R2).

## Risks
- **Hand-writing ~80 auditable entities and ~120 processes is slow.** Cheapest signal: draft the org table first and time it; if it runs past half a day, re-plan rather than cut realism.
- **Sample mode drifting.** Changing shared lists (e.g. appending systems) could shift sample-size draws. Guard: sample mode reads fixed slices of each list, and AC-5 compares against the pre-change outputs.
- **Taxonomies that c cannot use.** c needs ERM L3 homes for many more risk concepts. Mitigation: design L3 nodes around real bank risk categories, and c may add nodes through its own plan.
- **Realism.** The owner reviewed a's sample only; full-size names and structure get a quick owner skim at review time (the full build's org table, rendered by the existing pack code into a temp file on request).

## Out of scope
- Risks, controls, audits, issues at full size: c, d, e.
- AI text at full size: c-e, after the owner approves the cost (R2 Next).
- A vendor entity for E3 round 5: parked (vendors stay a system attribute here).
- Making full size the default: e.

## Relevant lessons
- L-002 (AI rewrites invent facts): no AI text is generated in this change; the text default only switches to already-committed, guarded text.
- L-003 (shared vocabulary for near-misses): not affected here; IA taxonomy names keep their audit-area wording, which c's IA entries reuse as area prefixes.
- L-004 (capitan rescue sequence): followed for any knowledge that lands on the branch.

## Slices
1. `--size full` plumbing in `akg/__main__.py`; text default to `ai`; regenerate the sample golden once, from otherwise unmodified code; AC-5 (sample part).
2. Organization at full size: segments, business units, auditable entities, processes, systems, people, regulations, new names; AC-1, AC-3, AC-7, AC-8.
3. Taxonomies at full size and the extended IA-to-ERM map; AC-2, AC-4.
4. `golden.py --size full`, full-size golden, child a's checks moved to shared helpers and run at full size, data-model test names; AC-5 (full part), AC-6.
5. (Revision 1) Drop the PERSON sub-test from AC-6's test; deliberate full-size AI-text guard and its test; AC-9.
