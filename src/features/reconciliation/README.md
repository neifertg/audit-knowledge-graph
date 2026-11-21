# reconciliation

Purpose: reconciles ERM's and IA's separate taxonomies, risks and controls into one canonical framework (ERM's taxonomy), with a review queue for uncertain matches (epic E2).
Entry point: `canonical.py` (`write_reconciled()`, child c; run by `python -m akg build` or `python -m akg reconcile`), which uses `match.py` (`pair_scores()`, child b), `features.py` and `taxonomy_map.py` (child a). Child d adds scoring against the answer key.
Owns: the canonical layer in `docs/data-model.md` (`<out>/reconciled/`: canonical risks and controls, maps-to files, `ia_maps_to_erm`, the review queue).
Depends on: the generator's published files only (read from a build directory); scikit-learn.

Notes for people and agents working here:
- **Never read the answer key here (INV-6).** Every module works from the published CSVs only. Tests check this by running on a copy of the build with `answer_key/` deleted. Only scoring code and the training script (later children) may read an answer key.
- **`similarity.py`** holds the shared risk-to-risk similarity, and its constants are fixed by the 011 plan. It is word TF-IDF on 1-2 grams plus character TF-IDF on 3-5 grams, both on `title. description` and fitted on both sources. It adds 0.3 for a shared exposed entity, or else 0.15 for a shared business unit.
- **`taxonomy_map.py`** maps each IA node by a risk-level vote:
  - Each IA risk votes for its most similar ERM risk, with ties going to the lowest ID.
  - Each IA node maps to the deepest ERM node at an allowed level holding at least `MAJORITY` (0.5) of its subtree's votes.
  - A node whose subtree holds no IA risk is `unmapped` with basis `no_risks`.
  - Node names are **not** used as evidence. A names-only mapping is only the baseline the vote must beat: 0.33 accuracy on seed 42, against the vote's 0.71 on nodes holding risks.
- **Known limit:** IA nodes that are truly unmapped but hold risks are not detected, because their risks truly sit in one ERM node.
- **`features.py`** builds the three pair tables (cross-source risks, ERM duplicates, cross-source controls). Their columns are pinned by the 012 plan. Word and character cosines become tail scores, `-log10(1 - p + 1/n)` of their within-bank percentile.
- **`train.py`** is the only module that reads an answer key, and only the training bank's: seed 7, templated, built in a temporary directory. It writes `weights.json` (coefficients, thresholds, the training pair each threshold falls on, and a fingerprint). Re-run it after changing any feature code:

  ```
  .venv\Scripts\python -m src.features.reconciliation.train
  ```

  It takes about 7 seconds, and a test fails if the fingerprint no longer matches.
- **`match.py`** applies `weights.json` and gives every pair a probability and a band: `accept`, `review` or `below`. ERM duplicates are review-only, never `accept`.
- **Circular by design:** the control feature `risk_link` uses risk scores. Training uses the risk model's in-sample scores on seed 7; scoring uses the committed risk model on the scored bank.
- **`canonical.py`** merges accepted pairs, places every risk at an ERM L3 node, builds the review queue and writes `<out>/reconciled/`. The rules are in its docstring and the 013 plan. Its output is frozen by `tests/golden/checksums_reconciled.sha256`; regenerate that file with `.venv\Scripts\python -m tests.reconciliation.golden` after an intentional change.
- Generator tests build with `--no-reconcile`, and the generator goldens skip `reconciled/`.
