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
      "title": "Organization, taxonomies and audit universe",
      "depends_on": ["a"]
    },
    {
      "key": "c",
      "title": "ERM and IA risk and control populations with answer key",
      "depends_on": ["b"]
    },
    {
      "key": "d",
      "title": "Three years of audits and issues",
      "depends_on": ["c"]
    }
  ]
}
```

## Why
Everything downstream (reconciliation in E2, the head-to-head rounds in E3, the page in E4) is only as convincing as this data. It has to read as a real US regional bank to audit professionals (the milestone's riskiest assumption) and carry a realistic reconciliation problem with a hidden answer key, so O3's accuracy numbers mean something.

## Shape
- `src/features/generator/`: one seeded entry point that writes CSVs plus a separate `answer_key/` folder.
- **a (gate):** about 15 rows per entity, both taxonomies, hard duplicates, and templated vs AI-written descriptions side by side (research R2). The owner reviews it; b-d are built only after it passes.
- **b:** segments, business units, auditable entities, processes, systems, people; the ERM (Basel-style) and IA (legacy) L1-L3 taxonomies.
- **c:** L4 risks and controls for each source with about 60% overlap; duplicates inside ERM; controls at different levels of detail; orphan controls; the answer key (true duplicates, true taxonomy mapping).
- **d:** about 75 audits across 3 years, coverage and test results, about 250 issues from four sources (IA, regulator MRA/MRIA, self-identified, 2nd line).
- Invariants enforced here: INV-1, INV-2, INV-4, INV-5, INV-7, INV-9 (`docs/data-model.md`).
- AI-written text (if R2 says so) is generated once with the Anthropic SDK and committed; the build reads the committed text.

## Out of scope
- Documents (workpapers, RCMs as documents, reports): M2.
- Scale dial beyond 1x for benchmarking: M2.
- Any loading into SQLite or Neo4j: E3.

## Relevant lessons
- None yet (new project).

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard ...).
Children with no unmet depends_on can run in parallel, one branch/worktree each.
