"""Score every candidate pair with the committed weights (E2 child b, change 012).

`pair_scores(build_dir)` reads published files only (INV-6) and `weights.json`, never an answer key.
Bands: `accept` (at or above the auto-accept threshold), `review` (at or above the review floor),
`below`. ERM duplicates are review-only (owner decision, 012): they never get `accept`.
"""
import json
from pathlib import Path

import numpy as np

from .features import control_table, risk_tables

WEIGHTS = Path(__file__).resolve().parent / "weights.json"
KINDS = ("risk", "duplicate", "control")


def load_weights(path: Path = WEIGHTS) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def probability(model: dict, X: np.ndarray) -> np.ndarray:
    z = X @ np.array(model["coefficients"]) + model["intercept"]
    return 1.0 / (1.0 + np.exp(-z))


def bands(model: dict, scores: np.ndarray) -> list[str]:
    auto, floor = model["auto_accept"], model["review_floor"]
    return ["accept" if auto is not None and s >= auto else "review" if s >= floor else "below" for s in scores]


def pair_scores(build_dir: Path, weights: dict | None = None) -> dict:
    """kind -> {"pairs": [...], "score": array, "band": [...]} for risk, duplicate and control pairs."""
    weights = weights or load_weights()
    (rX, rpairs), (dX, dpairs) = risk_tables(build_dir)
    rscore = probability(weights["risk"], rX)
    cX, cpairs = control_table(build_dir, dict(zip(rpairs, rscore)))
    out = {}
    for kind, X, pairs in (("risk", rX, rpairs), ("duplicate", dX, dpairs), ("control", cX, cpairs)):
        score = rscore if kind == "risk" else probability(weights[kind], X)
        out[kind] = {"pairs": pairs, "score": score, "band": bands(weights[kind], score)}
    return out
