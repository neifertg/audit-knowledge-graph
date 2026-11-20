# E1 Synthetic bank generator

```json plan
{
  "id": "001-e1-synthetic-bank-generator",
  "tier": "epic",
  "status": "draft",
  "created": "2026-11-19",
  "objective": "O3",
  "children": [
    {
      "key": "a",
      "title": "Sample pack for realism review",
      "depends_on": []
    },
    {
      "key": "b",
      "title": "Organization, regulations, taxonomies and audit universe",
      "depends_on": [
        "a"
      ]
    },
    {
      "key": "c",
      "title": "ERM and IA risk populations with answer key",
      "depends_on": [
        "b"
      ]
    },
    {
      "key": "d",
      "title": "ERM and IA control populations with answer key",
      "depends_on": [
        "c"
      ]
    },
    {
      "key": "e",
      "title": "Three years of audits and issues with planted scenarios",
      "depends_on": [
        "d"
      ]
    },
    {
      "key": "f",
      "title": "Full-size AI text in one batch",
      "depends_on": [
        "e"
      ]
    }
  ],
  "revised": "2026-11-20"
}
```

## Why
Everything downstream (reconciliation in E2, the head-to-head rounds in E3, the page in E4) is only as convincing as this data. It has to read as a real US regional bank to audit professionals (the milestone's riskiest assumption) and carry a realistic reconciliation problem with a hidden answer key, so O3's accuracy numbers mean something.

## Shape
`src/features/generator/`: one seeded entry point that writes CSVs plus a separate `answer_key/` folder. Its `README.md` is the data dictionary (every CSV, column, type and allowed values); each child updates it for what it adds, and E3a builds the schema from it. Timebox: 10 working days of build time for the whole epic (a: 2, b-e: about 2 each), not counting time waiting on the owner's review at the gate; each child plan states its own.

**a (gate, walking skeleton).** a builds a thin end-to-end slice of the generator: every entity type at about 15 rows, both taxonomies, a first answer key, the AI-text script, and the name lists with their deny-list test. b-e extend a's code to full size and add rules; they do not rewrite it. The sample pack is that slice's output, with templated and AI-written descriptions side by side (R2). Pass condition: the owner marks each entity type realistic / not realistic and picks templated or AI text, recorded in `research/r2-synthetic-text-realism/decision.md` as GO. b does not start until that decision is GO.

**Partial pass.** If the owner marks some entity types not realistic, a is revised and the pack re-reviewed for those types only; R2 goes GO only when every type passes.

**Entry point and packages.** a creates the `akg` package with a `build` command that, in E1, runs only the generator; E2 and E3 add their steps to it. a creates `requirements.txt` with exact pins of the approved packages it uses (`anthropic`, `scikit-learn`, `pandas`).

**Areas.** Every child: `src/features/generator/**`, `tests/**`, `docs/data-model.md`. a also: `akg/**`, `requirements.txt`, `.gitattributes`, `research/r2-synthetic-text-realism/**`.

**Random streams.** Each entity type draws from its own sub-seeded stream (derived from the master seed and the type name), so a later child's draws never change an earlier child's output.

**Ownership of every entity and edge in the ER diagram** (each child adds a test that its types have at least one row; e adds one test that every relationship type in the diagram is populated):
| Child | Entities | Edges |
|---|---|---|
| b | SEGMENT, BUSINESS_UNIT, AUDITABLE_ENTITY, PROCESS, SYSTEM, PERSON, REGULATION (~15), TAXONOMY_NODE (ERM and IA, L1-L3) | has, owns, performs, runs_on, parent_of |
| c | RISK (ERM, IA) | classifies, exposed_to |
| d | CONTROL (ERM, IA) | mitigates, depends_on, requires, CONTROL owned_by |
| e | AUDIT, ISSUE | covered, tested, raised, ISSUE against CONTROL / RISK, ISSUE owned_by |
CANONICAL_* and maps_to / ia_maps_to_erm are E2 output; E1 writes only their true values in the answer key.

**Answer-key schema** (c writes risks and taxonomy, d writes controls):
- `taxonomy_map.csv`: every IA L1-L3 node -> exactly one true ERM node, or `unmapped` (matching the ER diagram's at-most-one `ia_maps_to_erm`). Levels: IA L1 -> ERM L1; IA L2 -> ERM L1 or L2; IA L3 -> ERM L2 or L3; never deeper than the IA node. "Maps unevenly" comes from level mismatches, unmapped nodes, and misfiled risks (below).
- `risk_clusters.csv`: every source risk -> a true canonical cluster ID, or `none` (singleton); every IA risk, matched or not, also gets its `true_erm_node` (an ERM L3). For 10-20% of IA risks ("misfiled"), that node is not under their IA node's mapped target. E2 scores node mapping and per-risk placement separately.
- `control_clusters.csv`: every source control -> a true canonical cluster ID, or `none`.
- `scenarios.csv`: one row per planted scenario item (scenario name, item IDs), so E3 can check that each query finds what was planted.
- In all cluster files: A cluster with items from both sources is a cross-source match; two ERM items in one cluster are a within-ERM duplicate. E2 scores both separately, plus true non-matches.
- Consistency test: every published risk, control and IA taxonomy node appears in the answer key exactly once; ERM risks sharing a cluster share one ERM L3 node; every referenced ID exists; targets are ERM nodes at an allowed level; every cross-source risk cluster's IA risks have the ERM risk's L3 node as `true_erm_node`; every scenarios.csv ID exists.

**Overlap and quotas, defined.** Overlap = share of IA risks (resp. controls) whose true cluster also holds an ERM item: 55-65%. Counts within ±10% of the targets in `docs/data-model.md`. ERM within-source duplicates 5-10% of ERM risks; orphan controls 3-6% of controls; at least 20% of matched control pairs differ in level of detail. One test checks all of these: counts from the published CSVs, overlap and duplicate rates from the answer key.

**No answer-key leakage.** IDs and row order shuffled independently per source; matched items never share ID numbering, a template sentence or a full identical attribute set (owner, frequency, type at most 2 of 3 equal); a hard negative is a cross-source non-matching pair whose TF-IDF cosine is at or above the median cosine of true matching pairs, and at least 10% of IA risks and controls have one. Tests against the answer key, run separately for risks and for controls: candidate pairs are all (ERM item, IA item) pairs; a pair is positive when both share a true cluster. Exact text match scores F1 below 0.5 (risks and controls); exact owner+frequency match scores F1 below 0.5 (controls only; risks have neither); a scikit-learn TF-IDF cosine baseline at its best threshold scores F1 between 0.40 and 0.75 for each, so the problem is neither trivial nor hopeless.

**Planted scenarios for M1's story and E3's rounds** (one test each, in e unless noted): at least 5 repeat findings under different titles across years; at least 3 systems that controls of 3+ auditable entities depend on (d); at least 8 High inherent-rated IA risks whose IA controls were never tested in the 3-year window (ERM risks with no IA match are untested by construction; that is a coverage-gap finding, not this scenario); one ERM L1 category's issue count rises at least 50% from year 1 to year 3 while total issues change less than 15% (an issue's L1 is that of the first risk it links to, or of the first risk its control mitigates; issues against orphan controls always also link a risk); every regulation reaches at least one business unit through requires -> control -> risk -> entity. "Stale coverage" means never tested in the window, or last tested more than 24 months before window end; E3 round 2's "untested 3+ years" wording is parked for the owner to amend in E3.

**Ratings.** RISK carries `inherent_rating` (High / Medium / Low); ISSUE carries `rating` (High / Medium / Low).

**Audit scope.** Audits test IA controls only (IA works from its own RCMs) and cover auditable entities; ERM controls are never in `tested`. Every control an audit tests mitigates a risk that one of its covered entities is exposed to (test).

**Issue linking (INV-4).** IA issues link to IA controls / risks, and only to controls their audit tested and risks those controls mitigate (test); regulator, self-identified and 2nd-line issues link to ERM controls / risks.

**Data model (rule 6).** Each child adds to `docs/data-model.md` the definitions it introduces: answer-key schema, level-mapping and misfiled-risk rules (c, d), ratings (c, e), issue-linking rule and stale-coverage definition (e).

**Determinism (INV-7).** AI text (if R2 picks it) is generated once by a separate script (`src/features/generator/write_text.py`), keyed by each item's internal key (assigned by the seeded generator before shuffling and never published), and committed with a hash of the item's template inputs. The build fails loudly if an item has no text or its stored hash no longer matches, and a test fails on committed text whose key no item uses. Full-size AI text (revision 1, 2026-11-20, owner decision): children c-e build full size with templated text only; child f generates all full-size AI text (risks, controls, issues) in one Message Batch with claude-opus-5-5 after e has replaced positional issue keys with natural keys, within a budget the owner approves (measured 2026-11-20: about $0.0039 per item at batch prices, about $5 for ~1,280 items). f re-validates every result against the L-002 rules, resubmits failures once, removes 006's full-size AI-text guard, and regenerates the full golden and baseline F1. Until f, sample size uses AI text and full size uses templated text. The build never imports `anthropic` or touches the network (test). Writers emit UTF-8 without BOM and `\n` line endings; `.gitattributes` pins committed text and CSVs to LF.

**Byte identity across machines.** A committed `tests/golden/checksums.sha256` lists the SHA-256 of every output file for the default seed; the INV-7 test regenerates and compares, so Windows and Linux are both checked against the same bytes. Locally it runs on Windows now; it runs on Linux once E3's CI job exists. A change that intentionally alters output regenerates the checksum file in the same commit.

**Names (INV-9).** Name lists are checked against a committed deny-list of real US bank, vendor and core-system names (test, from a), plus a one-time owner review in a.

**f (full-size AI text).** One batch, one budget approval, one guard removal; AI text stored apart from the sample text (`text/ai_text_full.jsonl`) so each size's orphan check stays exact.

**Invariant tests.** Each child names the tests for its invariants (a: INV-9, INV-7 checksums; b: INV-1 taxonomy part, INV-2; c: INV-1 risk part; e: INV-4, INV-5; every child after a refreshes the checksums) and replaces the matching `TBD (E1)` in `docs/data-model.md`.

## Out of scope
- Documents (workpapers, RCMs as documents, reports): M2.
- Scale dial beyond 1x for benchmarking: M2.
- Any loading into SQLite or Neo4j: E3.
- Extra answer-key fields R1 might want: added by an E2 change if R1 asks for them.

## Relevant lessons
- None yet (new project).

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard ...).
Children with no unmet depends_on can run in parallel, one branch/worktree each.
