# E4 Page v1 and publish

```json plan
{
  "id": "004-e4-page-v1-and-publish",
  "tier": "epic",
  "status": "draft",
  "created": "2026-11-19",
  "objective": "O1",
  "children": [
    {
      "key": "a",
      "title": "CAE layer and page skeleton",
      "depends_on": []
    },
    {
      "key": "b",
      "title": "Rounds, operating model and technical appendix",
      "depends_on": ["a"]
    },
    {
      "key": "c",
      "title": "Publish to GitHub Pages and link from portfolio",
      "depends_on": ["b"]
    }
  ]
}
```

## Why
O1 first, O2 second: one scroll that gives a CAE the value in 60 seconds and gives a data scientist the depth to trust it. This is what hiring audiences actually see (O5).

## Shape
- `src/features/site/`: static HTML/JS, data from the build's JSON export; CDN libraries (Cytoscape.js for the graph, a chart library) pinned to exact versions; light and dark themes; works at phone width.
- **a:** the top layer: headline, the three planted stories (ERM shared-system blast radius, repeat finding in disguise, owner concentration) with one line of business impact each, and one clickable blast-radius graph. Copy can be drafted before E3 finishes, with placeholder data.
- **b:** the 7 rounds side by side with verdicts (including SQL wins); the operating model (pros/cons, keys for success, maintenance table, effort estimate); the technical appendix (data model, generator design, reconciliation accuracy, test results, limitations). Depends on E3's exports.
- **c:** create the public GitHub repo and Pages site (the owner confirms before anything goes public); add a card to risk-analytics-portfolio; run the O1 reader test with 2-3 of the owner's contacts.

## Out of scope
- Live GraphRAG chat and the AWS production-architecture diagram: parked.
- Documents and the vector layer: M2.

## Relevant lessons
- None yet (new project).

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard ...).
Children with no unmet depends_on can run in parallel, one branch/worktree each.
