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
      "title": "Match features, training script and committed weights",
      "depends_on": [
        "a"
      ]
    },
    {
      "key": "c",
      "title": "Canonical layer, review queue and build step",
      "depends_on": [
        "b"
      ]
    },
    {
      "key": "d",
      "title": "Score reconciliation against the answer key",
      "depends_on": [
        "c"
      ]
    }
  ],
  "revised": "2026-11-21"
}
```

## Why
O3: the realistic hard part. ERM and IA keep separate, overlapping populations with no common framework. This epic turns them into one canonical framework (ERM's Basel-style taxonomy) and measures how well that worked, instead of assuming clean data like most knowledge graph demos.

## Shape
`src/features/reconciliation/` (one feature folder with a README). Depends on E1 (generator output, AI text). Method: research R1 (`research/r1-reconciliation-matching-method/decision.md`, GO 2026-11-21).

**Output contract (for E3).** `python -m akg build` runs the generator, then reconciliation, at either size, which writes to `<out>/reconciled/`. The published figures and the reconciled golden are at full size; the sample run exists for quick tests:
- `canonical_risk.csv` (`canonical_risk_id`, `erm_l3_node_id`)
- `canonical_control.csv` (`canonical_control_id`)
- `risk_maps_to_canonical.csv` and `control_maps_to_canonical.csv` (`source`, source ID, canonical ID, `logit`; as built in 013, see the revision below)
- `ia_maps_to_erm.csv` (`ia_node_id`, `erm_node_id` or `unmapped`, `score`, `basis`)
- `review_queue.csv` (`kind`, `item_a`, `item_b`, `logit`, `reason`, `drivers`: the three features that drove the score)

The column lists are final in each child's plan and in docs/data-model.md, the same change. Canonical IDs are deterministic: seeded, and assigned in sorted order. `tests/generator/golden.py`'s generator checksums skip `reconciled/`, so E1's frozen golden files are untouched (L-006). A separate `tests/golden/checksums_reconciled.sha256` covers the reconciled output, which is the determinism check for E2 (INV-7).

**Canonical assignment rule (INV-3).** Pairs scored at or above the auto-accept threshold are merged edges; connected components of merged edges become canonical items.
- *Risks* (as built in 013): a canonical risk holds at most one ERM risk and at most one IA risk. Accepted edges merge in order of logit, then ERM ID, then IA ID; an edge whose ERM or IA risk is already merged goes to the queue as a `conflict`. ERM duplicates are review-only (012), so no within-ERM pair is ever auto-accepted and duplicates never chain.
- *Controls:* a canonical control holds at most one ERM control (the answer key has no within-ERM control duplicates), and any number of IA controls. Each IA control merges only its single highest-scoring auto-accepted edge, and its other auto-accepted edges go to the queue. This stops chaining through generic controls that share a subject phrase.
- *Ties* are broken by the lower source ID, so the output is deterministic.
- An item in no merged edge becomes a singleton canonical item.
- A pair scored between the review floor and the auto-accept threshold goes to `review_queue.csv`. Its two items stay in their own canonical items until a reviewer decides, and reviewer decisions are out of scope for M1.
- A whole-output test asserts that every source risk and control maps to exactly one canonical item, that every merged edge scored at or above the auto-accept threshold, and that no canonical control holds two ERM controls.
- Scoring (child d) scores the pairs implied by the *final* canonical items, not the raw edges, and reports the raw-edge figures beside them.

**Leakage (INV-6).** New wording, landing in docs/data-model.md in child c:
"The reconciliation pipeline never reads the published bank's answer key; only the scoring step does. The training script alone may read the *training* bank's (seed 7) answer key, to learn the committed weights."

Tests:
- Running reconciliation on a copy of the build with `answer_key/` deleted gives byte-identical `reconciled/` output.
- A static check: within `src/features/reconciliation/*.py`, only `score.py` (the scoring module, the published bank) and `train.py` (the training script, the training bank) mention `answer_key`.

**Training and thresholds.** A separate script, `python -m src.features.reconciliation.train`, builds the training bank (full size, `--text templated`, because AI text exists only for seed 42), computes the same features with the same code the build uses (including child a's real taxonomy mapper, not R1's stand-in), fits the logistic models, and commits their weights and thresholds as a small JSON file. The build only reads that file. The rule for setting the thresholds on the training bank is:
- the *auto-accept* threshold is the lowest score at which the pairs at or above it have at least 95% precision;
- the *review floor* is the highest score at which the pairs at or above it hold at least 99% of the true pairs.

Both rules are applied unchanged to the published bank, which uses AI text. ERM duplicates have a review floor but no auto-accept threshold (review-only; owner decision in 012). So child d reports the precision and recall actually reached on seed 42 at those thresholds, alongside the 95% and 99% targets. Two tests check that the committed file is current:
- a fast one that compares a fingerprint of the training inputs (the seed-7 build's checksums plus a hash of the feature code);
- a full retrain, comparing weights within 1e-6 (so Windows and Linux floats agree), and comparing each threshold by the training pair it selects rather than by its value.

The seed-7 build takes under a second. The retrain is bounded by feature computation; child b states its measured time.

**Children:**
- **a. Map IA taxonomy onto ERM (1 day).** Areas: `src/features/reconciliation/**`, `tests/**`, `docs/data-model.md`. Each IA L1-L3 node maps to one ERM node at an allowed level (the E1 answer-key schema), or to `unmapped`. Evidence comes from node names and the text of the risks each node classifies. A low-confidence node maps to `unmapped`, and the risks under it are placed by b. a's plan measures a name-only baseline first and sets its accuracy bars from it, per level, as R1 did for b. It is scored against `taxonomy_map`.
- **b. Match features, training script and committed weights (1.5 days).** Areas: as a.
  - *Features (R1):* word and character TF-IDF on title and description, plus structural features.
    - Risks: shared exposed entity, shared business unit, a's mapping, equal rating, candidate rank.
    - Controls: whether they mitigate a predicted risk match, equal type, nature and frequency, a shared system, and the documented citation cue.
    - Within-ERM duplicates: their own pair model, trained the same way and using the same features except cross-source ones.
  - *Training:* the training script, the committed weights and thresholds file, and the two currency tests.
  - *R1 reference figures* (seed 42, AI text, best threshold): risks about 0.81, controls about 0.74.
- **c. Canonical layer, review queue and build step (1 day).** Areas: as a, plus `akg/**` (the build step) and `tests/golden/**`.
  - *Canonical layer:* the assignment rule above, and the output files.
  - *Placement:* each IA risk's canonical ERM L3 is its matched ERM risk's L3. Without a match, it is the target of its IA node under a's mapping, or the ERM L3 whose risks' text it is most similar to, if that target is `unmapped` or above L3.
  - *INV-3 and INV-6:* the INV-3 whole-output test, the INV-6 tests and wording, the generator golden skipping `reconciled/`, and the reconciled golden.
- **d. Score and export for the page (1 day).** Areas: `src/features/reconciliation/**`, `tests/**`, `docs/data-model.md`. Scoring is the only code that reads the published answer key. It reports, each against the answer key:
  - taxonomy mapping precision and recall per level;
  - cross-source risk and control matching: precision, recall, auto-accepted, queued and missed;
  - within-ERM duplicate detection, scored separately;
  - per-risk ERM L3 placement accuracy, including on misfiled IA risks;
  - review-queue size by kind;
  - how much control accuracy the citation cue carries, as data-model.md asks: the controls score with and without that feature.

  The figures are exported as one JSON for the page, with a test that the export matches a fresh scoring run. The page text must state two caveats:
  - controls that mitigate no risk (orphans) always score as "unmatched", which helps the figures and is not matcher skill;
  - the training bank comes from the same generator, so its weights know the generator's habits in a way a real bank's history would not.

## Revision 2026-11-21: what the children built (closing E2)
All four children are done: a (011), b (012), c (013) and d (014). Where they diverged from the shape above, the owner decided in each child's approval. This section records the divergences:
- **ERM duplicates are review-only** (012, owner decision at approval). With 13 true duplicate pairs per bank, a 95%-precision auto-accept cannot be supported; on seed 1 the only auto-accepted duplicate was wrong. Every duplicate pair at or above its floor goes to the queue (14 at seed 42, 12 of them true).
- **Risk canonical rule** (013). At most one ERM risk and one IA risk per canonical risk, the mirror rule the epic critique asked for. It replaces the duplicate-group wording above, which could not apply once duplicates were review-only.
- **Features are tail scores of within-bank percentiles** (012). Raw cosines learned on the templated training bank missed 10 of 13 AI-text duplicates. The fit runs until it converges (`tol=1e-10`), and thresholds are found in one sorted sweep.
- **Scores are written as logits** (013). Probabilities above 0.9999 lost precision at 6 decimals.
- **A second model, the control model without the citation cue,** is committed in `weights.json` (014). It publishes the cue's share without retraining in tests; the weights currency check covers it.
- **Two modules may read an answer key:** `train.py` (the training bank) and `score.py` (the published bank, scoring only). INV-6's wording and its static check say so.
- **Taxonomy mapping** (011) is a risk-level vote. IA nodes holding no risks are left `unmapped` (`basis` = `no_risks`); truly unmapped nodes that hold risks are not detected, a stated limit.
- **Published results** (014; `src/features/reconciliation/scores.json`, seed 42, AI text):
  - risks: 33/33 auto-merged, recall 33/103, and 101/103 if a reviewer resolves the queue correctly;
  - controls: 68/68 auto-merged, recall 68/245, and 240/245 if resolved;
  - 482 queue rows;
  - IA placement 130/150;
  - taxonomy 44/62 on nodes holding risks;
  - the citation cue: 68/68 with it, 73/82 without.

  Four caveats travel with the figures: orphans help the figures and are not matcher skill; the training bank comes from the same generator; one bank with small samples; deliberately conservative thresholds.
- **Test-suite time** rose from about 65 s to about 190 s, because full builds now reconcile (L-014).
- **Parked from the children's reviews** (ROADMAP): two stale data-model lines about who reads answer keys, a few missing fixture tests, edge-case guards in `score.py` and `canonical.py`, and a reconcile speed-up.

## Out of scope
- A UI for working the review queue: it is a CSV for now (park any UI idea).
- Learning from reviewer decisions (active learning): parked.

## Relevant lessons
- L-012 to L-015 (from E2's children): quote the built module's figures; make learned features scale-free and converge the fit; count the builds a new step adds to the suite; check published caveats against the code that builds the candidates.
- L-007 and L-010: measure on the AI text early; the published accuracy is on the AI-text build.
- L-008: any exact shared phrase becomes a lookup key. The citation cue is a documented, deliberate feature; E2 reports how much of control accuracy it carries (data-model.md asks for this).
- Research R1 (decision.md): thresholds must be fixed on the training bank; the learned model's default 0.5 cut collapses precision.

Each child becomes its own standard change (python -m capitan new "<child title>" --tier standard ...).
Children with no unmet depends_on can run in parallel, one branch/worktree each.
