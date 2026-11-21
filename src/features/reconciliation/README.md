# reconciliation

Purpose: reconciles ERM's and IA's separate taxonomies, risks and controls into one canonical framework (ERM's taxonomy), with a review queue for uncertain matches (epic E2).
Entry point: `taxonomy_map.py` (`map_taxonomy()`, child a). Children b-d add matching, the canonical layer and scoring.
Owns: the canonical layer in `docs/data-model.md` (`ia_maps_to_erm` so far; canonical risks and controls from child c).
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
