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
- **a:** map each IA L1-L3 node to an ERM node, or flag it unmapped, from node names and the text of the risks each node classifies. The answer key's `taxonomy_map` is used only to score (precision and recall per level).
- **b:** match risks and controls with the method R1 chose (`research/r1-reconciliation-matching-method/decision.md`, GO 2026-11-21).
  - *Features:* word and character TF-IDF on title and description, plus structural features. For risks: shared exposed entity, shared business unit, child a's taxonomy mapping, equal rating, and candidate rank. For controls: whether they mitigate a predicted risk match, equal type, nature and frequency, a shared system, and the documented citation cue.
  - *Weights:* a logistic model's weights and its two thresholds (auto-accept and review floor) are learned once by a separate training script on a *training bank* (seed 7, templated text) and its answer key, and committed as a small JSON file. The build reads that file and never trains. A test re-runs training and asserts the committed file is current.
  - *Output:* canonical risks and controls (INV-3). Pairs above the auto-accept threshold merge; pairs between the two thresholds go to `review_queue.csv` with their score and the features that drove it; nothing below the auto-accept threshold merges silently.
  - *Leakage:* the pipeline never reads the published bank's answer key (INV-6, enforced by a test). INV-6's wording is clarified in docs/data-model.md in this child: only the training bank's answer key may train, and only in the training script.
  - *Reference figures (R1, seed 42, AI text):* risks F1 about 0.81, controls about 0.74 at the best threshold. E2 reports its figures at the thresholds fixed on the training bank, not the best one.
- **c:** precision, recall and review-queue size (auto-accepted, queued, and missed, per source type) against the published bank's answer key, plus child a's mapping accuracy, exported for the page. Scoring is the only code that reads the published answer key.

## Out of scope
- A UI for working the review queue: it is a CSV for now (park any UI idea).
- Learning from reviewer decisions (active learning): parked.

## Relevant lessons
- L-007 and L-010: measure on the AI text early; the published accuracy is on the AI-text build.
- L-008: any exact shared phrase becomes a lookup key. The citation cue is a documented, deliberate feature; E2 reports how much of control accuracy it carries (data-model.md asks for this).
- Research R1 (decision.md): thresholds must be fixed on the training bank; the learned model's default 0.5 cut collapses precision.

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard ...).
Children with no unmet depends_on can run in parallel, one branch/worktree each.
