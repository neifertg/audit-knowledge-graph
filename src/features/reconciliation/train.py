"""Learn the matching weights once on the training bank and commit them (E2 child b, change 012).

    .venv\\Scripts\\python -m src.features.reconciliation.train [--out path]

The training bank is seed 7, full size, templated text, built in a temporary directory. This
script is the only code in the feature that reads an answer key, and only the training bank's
(INV-6). The build never trains; it reads the committed weights.json.
"""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

from .features import CONTROL_COLUMNS, DUPLICATE_COLUMNS, RISK_COLUMNS, control_table, risk_tables
from .match import WEIGHTS

TRAINING_SEED = 7
AUTO_PRECISION = 0.95
FLOOR_RECALL = 0.99
HERE = Path(__file__).resolve().parent
SOURCES = ("similarity.py", "taxonomy_map.py", "features.py", "train.py", "match.py")
ROOT = HERE.parents[2]


def build_training_bank(out: Path) -> None:
    subprocess.run([sys.executable, "-m", "akg", "build", "--seed", str(TRAINING_SEED), "--size", "full",
                    "--text", "templated", "--out", str(out)], cwd=ROOT, check=True, capture_output=True)


def fingerprint(bank: Path) -> str:
    """SHA-256 over the training bank's published and answer-key files and the feature's source."""
    h = hashlib.sha256()
    for p in sorted(bank.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(bank).as_posix().encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    for name in SOURCES:
        h.update(name.encode() + b"\0" + (HERE / name).read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def truth(bank: Path, kind: str, pairs: list) -> np.ndarray:
    key = "risk_id" if kind == "risk" else "control_id"
    with open(bank / "answer_key" / f"{kind}_clusters.csv", encoding="utf-8", newline="") as f:
        cluster = {r[key]: r["cluster_id"] for r in csv.DictReader(f)}
    return np.array([cluster[a] != "none" and cluster[a] == cluster[b] for a, b in pairs])


def thresholds(scores: np.ndarray, y: np.ndarray) -> tuple[float | None, float]:
    """(auto_accept, review_floor) at tie-group boundaries, in one sorted sweep.

    auto_accept: the lowest score whose at-or-above set has precision >= AUTO_PRECISION, or None.
    review_floor: the highest score whose at-or-above set holds >= FLOOR_RECALL of the true pairs.
    """
    order = np.argsort(-scores, kind="stable")
    s, t = scores[order], y[order].astype(float)
    tp, n = np.cumsum(t), np.arange(1, len(t) + 1)
    ends = np.append(np.nonzero(s[1:] != s[:-1])[0], len(s) - 1)  # last index of each tie group
    precision, recall = tp[ends] / n[ends], tp[ends] / t.sum()
    qualifying = ends[precision >= AUTO_PRECISION]
    auto = float(s[qualifying.max()]) if len(qualifying) else None
    floor = float(s[ends[np.argmax(recall >= FLOOR_RECALL)]])
    return auto, floor


def threshold_pair(pairs: list, scores: np.ndarray, value: float | None):
    """The lowest-ID training pair scored exactly at a threshold (None for no threshold)."""
    if value is None:
        return None
    return list(min(p for p, s in zip(pairs, scores) if s == value))


def fit(X: np.ndarray, y: np.ndarray):
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(class_weight="balanced", tol=1e-10, max_iter=100000).fit(X, y)


def model_entry(model, columns, X, y, pairs, review_only=False) -> dict:
    scores = model.predict_proba(X)[:, 1]
    auto, floor = thresholds(scores, y)
    if review_only:
        auto = None  # duplicates: no auto-accept (owner decision, 012); floor uncapped
    elif auto is not None:
        floor = min(floor, auto)
    return {"columns": columns, "coefficients": [float(c) for c in model.coef_[0]],
            "intercept": float(model.intercept_[0]), "iterations": int(model.n_iter_[0]),
            "auto_accept": auto, "review_floor": floor, "review_only": review_only,
            "auto_accept_pair": threshold_pair(pairs, scores, auto),
            "review_floor_pair": threshold_pair(pairs, scores, floor),
            "training_true_pairs": int(y.sum())}


def train(bank: Path) -> dict:
    (rX, rpairs), (dX, dpairs) = risk_tables(bank)
    ry = truth(bank, "risk", rpairs)
    rmodel = fit(rX, ry)
    dy = truth(bank, "risk", dpairs)
    dmodel = fit(dX, dy)
    cX, cpairs = control_table(bank, dict(zip(rpairs, rmodel.predict_proba(rX)[:, 1])))
    cy = truth(bank, "control", cpairs)
    cmodel = fit(cX, cy)
    return {"training_seed": TRAINING_SEED, "fingerprint": fingerprint(bank),
            "risk": model_entry(rmodel, RISK_COLUMNS, rX, ry, rpairs),
            "duplicate": model_entry(dmodel, DUPLICATE_COLUMNS, dX, dy, dpairs, review_only=True),
            "control": model_entry(cmodel, CONTROL_COLUMNS, cX, cy, cpairs)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="train")
    parser.add_argument("--out", type=Path, default=WEIGHTS)
    args = parser.parse_args(argv)
    start = time.time()
    with tempfile.TemporaryDirectory(prefix="akg-train-") as tmp:
        bank = Path(tmp) / "bank"
        build_training_bank(bank)
        weights = train(bank)
    args.out.write_text(json.dumps(weights, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {args.out} in {time.time() - start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
