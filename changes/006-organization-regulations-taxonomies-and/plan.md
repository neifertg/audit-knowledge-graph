# Organization, regulations, taxonomies and audit universe

```json plan
{
  "id": "006-organization-regulations-taxonomies-and",
  "tier": "standard",
  "status": "draft",
  "created": "2026-11-20",
  "objective": "O3",
  "areas": [
    "src/features/generator/**",
    "tests/**",
    "docs/data-model.md",
    "requirements.txt"
  ],
  "timebox": "2 working days of build time. Past this, stop and re-plan with `capitan revise` (e.g. split the taxonomies from the organization); never drop criteria silently.",
  "criteria": [
    {
      "id": "AC-1",
      "when": "`python -m akg build --size full --seed 42 --out <dir>` runs",
      "then": "b's entities are at full size within the epic's ±10%: auditable entities 72-88, people 108-132, systems 27-33, regulations 14-16; plus segments exactly the 7 in docs/data-model.md, business units 20-40, processes 80-160; every auditable entity performs at least one process; at least 80% of processes run on a system; every relationship file b owns (has, owns, performs, runs_on, parent_of x2) has rows. Entities c-e own stay at sample size in this change",
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
      "then": "answer_key/taxonomy_map.csv covers every IA node exactly once at an allowed level (child a's consistency rules), and maps unevenly: at least 1 IA L1 branch unmapped throughout, at least 4 IA nodes mapped to a shallower ERM level, of which at least 2 are IA L3 nodes mapped to an ERM L2",
      "test": "generator.test_full_build.FullBuildTests.test_ac4_full_taxonomy_map_consistent_and_uneven",
      "status": "pending"
    },
    {
      "id": "AC-5",
      "when": "the default build runs (sample size) after this change",
      "then": "the default text is AI-written (`--text ai`, per R2); every sample-size file is byte-identical to what `--text ai` produced before this change (checked against checksums recorded from the pre-change build), so b changes no sample output beyond the text default; tests/golden/checksums.sha256 is regenerated for the new default, and a new tests/golden/checksums_full.sha256 covers the full build (INV-7 at both sizes)",
      "test": "generator.test_determinism.DeterminismTests.test_ac5_golden_checksums_at_both_sizes",
      "status": "pending"
    },
    {
      "id": "AC-6",
      "when": "the full build has run",
      "then": "child a's size-independent checks hold at full size too: referential integrity and no cross-source links (INV-10), data dictionary matches output, name columns come from their lists and no text names a real institution (INV-9), and changing `--count REGULATION` or `--count PERSON` leaves every file not naming that type unchanged",
      "test": "generator.test_full_build.FullBuildTests.test_ac6_child_a_checks_hold_at_full_size",
      "status": "pending"
    }
  ],
  "epic": "001-e1-synthetic-bank-generator",
  "child": "b"
}
```

## Why
The milestone needs a bank that reads as real at full size: an audit universe of about 80 auditable entities across believable business units, about 120 people, 30 systems, 15 regulations, and two taxonomies at real breadth that map unevenly. Children c-e hang risks, controls, audits and issues on this structure, and E3's rounds (shared-system blast radius, regulation-to-business-unit paths) need it to be dense enough to be interesting.

## Data impact
- **Sizes.** Adds `--size full`. In this change, full size scales only b's entities (segment, business unit, auditable entity, process, system, person, regulation, both taxonomies) and their relationships (has, owns, performs, runs_on, parent_of). Risks, controls, audits and issues stay at sample size until c-e. The default stays `sample` until child e makes full size the default.
- **Sample output is unchanged** except the text default: full-size content is a superset, and sample mode keeps selecting exactly the rows it selects today. So the sample pack and child a's results stand.
- **Text default.** Per R2's decision, `--text` defaults to `ai`; `--text templated` stays. Golden checksums regenerate for that one reason.
- **Taxonomy answer key.** The epic gives `taxonomy_map.csv` to child c, but a's consistency rules require every IA node in it, so b extends the true IA-to-ERM mapping for every node it adds. c still owns risk-level truth (`risk_clusters.csv`, misfiled risks).
- **Content** lives in `library.py` and `names/*.txt`: about 80 auditable entities grouped under 25-35 business units, about 120 processes with their systems, 30 systems with fictional vendors and criticality, 15 real US regulations, an ERM taxonomy (Basel-style L1, banking L2/L3) and a legacy IA taxonomy organized by audit area. New fictional names (vendors, systems, titles) pass the deny-list.
- **Invariants.** INV-1 (taxonomy part) and INV-2 get named tests, replacing `TBD (E1)` in `docs/data-model.md`. INV-7 gains a full-size golden. No new entities, columns or relationships.

## Test plan
- Done check: `.venv\Scripts\python -m unittest discover -s tests -v`; every named test shows `ok`.
- Real builds through the CLI into temp directories; no mocks.
- Child a's tests keep running unchanged at sample size; AC-6 runs their size-independent checks again on the full build (shared helpers, not copies).
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
1. `--size full` plumbing; text default to `ai`; regenerate sample golden; AC-5 (sample part).
2. Organization at full size: segments, business units, auditable entities, processes, systems, people, regulations, new names; AC-1, AC-3.
3. Taxonomies at full size and the extended IA-to-ERM map; AC-2, AC-4.
4. Full-size golden, child a's checks at full size, data-model test names; AC-5 (full part), AC-6.
