# E2 ERM-IA reconciliation

```json plan
{
  "id": "002-e2-erm-ia-reconciliation",
  "tier": "epic",
  "status": "draft",
  "created": "2026-11-19",
  "objective": "O3",
  "children": [
    {
      "key": "a",
      "title": "Map IA taxonomy onto ERM taxonomy",
      "depends_on": []
    },
    {
      "key": "b",
      "title": "Match risks and controls with a review queue",
      "depends_on": ["a"]
    },
    {
      "key": "c",
      "title": "Score reconciliation against the answer key",
      "depends_on": ["b"]
    }
  ]
}
```

## Why
O3: the realistic hard part. ERM and IA keep separate, overlapping populations with no common framework. This epic turns them into one canonical framework (ERM's Basel-style taxonomy) and measures how well that worked, instead of assuming clean data like most knowledge graph demos.

## Shape
- `src/features/reconciliation/`. Depends on E1 (generator output).
- **a:** map each IA L1-L3 node to an ERM node (or flag it unmapped).
- **b:** candidate matching for risks and controls (method chosen in research R1: text similarity plus attribute rules such as owner, frequency and system, or embeddings), a confidence score, a threshold, and a review queue for low-confidence matches. Produces canonical risks and controls (INV-3).
- **c:** precision, recall and review-queue size against the answer key, exported for the page. The pipeline never reads the answer key (INV-6, enforced by a test).

## Out of scope
- A UI for working the review queue: it is a CSV for now (park any UI idea).
- Learning from reviewer decisions (active learning): parked.

## Relevant lessons
- None yet (new project).

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard ...).
Children with no unmet depends_on can run in parallel, one branch/worktree each.
