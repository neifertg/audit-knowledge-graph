# Research: R1 reconciliation matching method

Objective: O3
Question: Can text similarity (TF-IDF) plus attribute rules (owner, frequency, system, taxonomy mapping) reach defensible precision and recall against the answer key, or do we need embeddings (a new package or an API)?
Timebox: 1 day. Past this, decide with what you have.

## Findings
Experiment run on 2026-11-21 against the seed-42 full build with the committed AI text (E1 child f). Features came from published files only. The answer key was used only to score, and for method C as labels from a *different* bank. Every ERM × IA pair was scored: 27,000 risk pairs (103 true) and 118,105 control pairs (245 true). The figures are best-threshold F1, with precision and recall in brackets.

| Method | Risks F1 | Controls F1 |
|---|---|---|
| A. Word TF-IDF (title + description, 1-2 grams) | 0.56 | 0.35 |
| A. Character TF-IDF (3-5 grams) | 0.58 | 0.42 |
| A. LSA (TF-IDF reduced to 150 dimensions) | 0.52 | 0.36 |
| B. Hand-weighted: text + structure | 0.81 (P 0.78, R 0.85) | 0.57 (P 0.79, R 0.45) |
| C. Logistic regression, cross-validated by theme on seed 42 | 0.79 | 0.75 |
| **C'. Logistic regression learned on seed 7 (templated text), applied unchanged to seed 42 (AI text)** | **0.81 (P 0.72, R 0.92)** | **0.74 (P 0.64, R 0.88)** |

The structural features were:
- **Risks:** shared exposed entity, shared business unit, similarity of the taxonomy path names (a stand-in for E2 child a's mapping), equal rating, and the ERM risk's rank among the IA risk's candidates.
- **Controls:** whether the two controls mitigate a *predicted* risk match, equal control type, nature and frequency, a shared system, and ERM's title subject appearing in IA's text (the documented citation cue).

On seed 7 (templated text) the results are nearly the same: B scores 0.81 for risks and 0.55 for controls, and C scores 0.78 and 0.71. The pattern holds across seeds and across text type.

**Review queue.** With C', every true pair scored at least 0.5. If the matcher auto-accepts the top band at 95% precision and sends the rest above 0.5 to review, nothing is lost:
- risks: 54 auto-accepted (recall 0.50), and a queue of 283 pairs covers the rest;
- controls: 85 auto-accepted (recall 0.33), and a queue of 753 pairs covers the rest.

The queue is large because most matches are ambiguous to text. That is the realistic point O3 makes, and E2 should report the queue's size and composition, not hide it.

**Embeddings.** None are needed to reach defensible accuracy in M1:
- Structure carries most of the gain: it takes controls from 0.42 to 0.74.
- LSA, the semantic option already available through scikit-learn, did worse than plain TF-IDF.
- Real embeddings would need either a new local package (sentence-transformers pulls in torch) or an embeddings API, which needs a new vendor and precomputed, committed vectors.

That comparison belongs to R4 (M2).

**Caveats.**
- The thresholds in the table are chosen on the scored bank. E2 must fix its thresholds on the training bank. At the learned model's default 0.5, precision collapses to about 0.3 (because of class weighting), so threshold choice matters.
- B's weights were set by judgment while viewing results, so B is mildly optimistic.

## Decision
Decision: GO
Why: TF-IDF (word and character) plus structural features reaches risks 0.81 and controls 0.74 F1 on the AI text, with no embeddings and no new package. The owner chose (2026-11-21) to learn the weights and thresholds once on a separate training bank (seed 7) and its answer key, commit them, and apply them unchanged to the published bank (seed 42). This mirrors a bank learning from past reviewer decisions. The pipeline never reads the published bank's answer key; INV-6 is clarified to say that.
Next: revise E2 so that:
- child b names this method;
- the training-bank step is a separate script whose committed weights the build reads (the build never trains);
- E2 reports precision, recall and review-queue size, with thresholds fixed on the training bank;
- INV-6's new wording lands in docs/data-model.md in the child that builds the matcher.
