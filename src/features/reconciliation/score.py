"""Score the reconciliation against the published bank's answer key (E2 child d, change 014).

    .venv\\Scripts\\python -m src.features.reconciliation.score     # writes scores.json

This is the scoring step: the one module allowed to read the published bank's answer key (INV-6).
Definitions (014 plan, AC-1): a *true pair* is an (ERM, IA) pair of one item type whose answer-key
cluster_id is equal and not `none`; a *merged pair* shares a canonical ID; a *queued pair* is a
review_queue row (item_a ERM, item_b IA); *missed* = true pairs neither merged nor queued;
*recall if resolved* = (true merged + true queued) / true; *raw accept* = merged + conflict rows.
Every ratio is published with its count.
"""
import csv
import json
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .features import control_table, risk_tables
from .match import bands, load_weights, probability

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCORES = HERE / "scores.json"
PUBLISHED_SEED = 42

CAVEATS = {
    "orphans": "Orphan controls ({orphans}) mitigate no risk and enter the candidate pairs as easy negatives "
               "({orphans_merged} merged; {orphans_queued} review-queue rows touch one). That helps the figures; "
               "it is structure, not matcher skill.",
    "same_generator": "The training bank (seed {training_seed}) comes from the same generator as the published bank, "
                      "so the learned weights know the generator's habits in a way a real bank's history would not.",
    "one_bank": "These figures come from one bank with small samples: precision rests on {risk_merged} risk and "
                "{control_merged} control merges. Raw auto-accept precision was {risk_raw} for risks here and "
                "39/42 (0.93) on seed 1.",
    "conservative": "Thresholds are deliberately conservative: only pairs reaching 95% precision on the training bank "
                    "merge, so merged recall is low and the review queue carries the rest. Merged F1 ({risk_f1} risks, "
                    "{control_f1} controls) is not comparable with research R1's best-threshold F1 (about 0.81 and 0.74).",
}


def ratio(a: int, b: int) -> dict:
    return {"count": f"{a}/{b}", "value": round(a / b, 4) if b else None}


def pair_figures(erm: list, ia: list, cluster: dict, canonical: dict, queued: set, conflicts: set) -> dict:
    """Cross-source figures for one item type (all inputs are plain IDs and pairs)."""
    true = {(e, i) for e in erm for i in ia if cluster[e] != "none" and cluster[e] == cluster[i]}
    merged = {(e, i) for e in erm for i in ia if canonical[e] == canonical[i]}
    tm, tq = len(merged & true), len(queued & true)
    raw = merged | conflicts
    precision, recall = (tm / len(merged) if merged else 0.0), tm / len(true)
    return {"true_pairs": len(true), "merged": len(merged), "precision": ratio(tm, len(merged)),
            "recall": ratio(tm, len(true)),
            "f1": round(2 * precision * recall / (precision + recall), 4) if tm else 0.0,
            "queued": len(queued), "true_queued": tq, "missed": len(true - merged - queued),
            "recall_if_resolved": ratio(tm + tq, len(true)),
            "raw_accept": len(raw), "raw_accept_precision": ratio(len(raw & true), len(raw))}


def duplicate_figures(erm: list, cluster: dict, queued: set) -> dict:
    ids = sorted(erm)
    true = {(a, b) for n, a in enumerate(ids) for b in ids[n + 1:] if cluster[a] != "none" and cluster[a] == cluster[b]}
    return {"true_pairs": len(true), "queued": len(queued), "true_queued": len(queued & true),
            "missed": len(true - queued)}


def taxonomy_figures(rows: list[dict], truth: dict, level: dict) -> dict:
    out = {}
    for lvl in sorted({level[r["ia_node_id"]] for r in rows}):
        at = [r for r in rows if level[r["ia_node_id"]] == lvl]
        mapped = [r for r in at if r["erm_node_id"] != "unmapped"]
        right = sum(r["erm_node_id"] == truth[r["ia_node_id"]] for r in mapped)
        held = [r for r in at if r["basis"] == "vote"]
        out[f"L{lvl}"] = {"precision": ratio(right, len(mapped)),
                          "recall": ratio(right, sum(truth[r["ia_node_id"]] != "unmapped" for r in at)),
                          "accuracy_on_nodes_holding_risks": ratio(sum(r["erm_node_id"] == truth[r["ia_node_id"]] for r in held), len(held))}
    held = [r for r in rows if r["basis"] == "vote"]
    out["nodes_holding_risks"] = ratio(sum(r["erm_node_id"] == truth[r["ia_node_id"]] for r in held), len(held))
    return out


def placement_figures(ia_risks: list, placed: dict, true_node: dict, misfiled: set) -> dict:
    """placed: IA risk -> (ERM L3 node, method)."""
    by = defaultdict(lambda: [0, 0])
    for i in ia_risks:
        node, how = placed[i]
        by[how][0] += node == true_node[i]
        by[how][1] += 1
    right = sum(a for a, _ in by.values())
    mis = [i for i in ia_risks if i in misfiled]
    return {"all": ratio(right, len(ia_risks)), **{how: ratio(a, b) for how, (a, b) in sorted(by.items())},
            "misfiled": ratio(sum(placed[i][0] == true_node[i] for i in mis), len(mis))}


def orphan_figures(orphans: set, canonical: dict, queued: set) -> dict:
    size = Counter(canonical.values())
    return {"orphans": len(orphans), "merged": sum(1 for o in orphans if size[canonical[o]] > 1),
            "queue_rows": sum(1 for a, b in queued if a in orphans or b in orphans)}


def band_figures(model: dict, X: np.ndarray, y: np.ndarray) -> dict:
    band = np.array(bands(model, probability(model, X)))
    accepted = band == "accept"
    return {"accepted": int(accepted.sum()), "precision": ratio(int((accepted & y).sum()), int(accepted.sum())),
            "review_band": int((band == "review").sum()), "true_below_floor": int((y & (band == "below")).sum())}


def _read(folder: Path, name: str) -> list[dict]:
    with open(folder / f"{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def score(build_dir: Path, weights: dict | None = None) -> dict:
    build_dir = Path(build_dir)
    weights = weights or load_weights()
    rec, key = build_dir / "reconciled", build_dir / "answer_key"
    queue = _read(rec, "review_queue")
    queued = lambda kind, reason=None: {(r["item_a"], r["item_b"]) for r in queue
                                        if r["kind"] == kind and (reason is None or r["reason"] == reason)}
    out = {"provenance": {"seed": PUBLISHED_SEED, "text": "ai", "size": "full",
                          "training_seed": weights["training_seed"], "weights_fingerprint": weights["fingerprint"]},
           "threshold_targets": {"auto_accept_training_precision": 0.95, "review_floor_training_recall": 0.99}}
    for kind, item in (("risk", "risk_id"), ("control", "control_id")):
        maps = _read(rec, f"{kind}_maps_to_canonical")
        cluster = {r[item]: r["cluster_id"] for r in _read(key, f"{kind}_clusters")}
        canonical = {r[item]: r[f"canonical_{kind}_id"] for r in maps}
        erm = [r[item] for r in maps if r["source"] == "ERM"]
        ia = [r[item] for r in maps if r["source"] == "IA"]
        out[kind] = pair_figures(erm, ia, cluster, canonical, queued(kind), queued(kind, "conflict"))
        if kind == "risk":
            out["duplicate"] = duplicate_figures(erm, cluster, queued("duplicate"))
        else:
            mitigating = {r["control_id"] for s in ("erm", "ia") for r in _read(build_dir, f"control_mitigates_risk_{s}")}
            out["orphan_controls"] = orphan_figures(set(canonical) - mitigating, canonical, queued("control"))

    truth = {r["ia_node_id"]: r["erm_node_id"] for r in _read(key, "taxonomy_map")}
    level = {r["taxonomy_node_id"]: int(r["level"]) for r in _read(build_dir, "taxonomy_node_ia")}
    out["taxonomy"] = taxonomy_figures(_read(rec, "ia_maps_to_erm"), truth, level)

    erm_parent = {r["child_id"]: r["parent_id"] for r in _read(build_dir, "taxonomy_node_parent_of_taxonomy_node_erm")}
    def ancestors(n):
        chain = [n]
        while chain[-1] in erm_parent:
            chain.append(erm_parent[chain[-1]])
        return chain
    true_node = {r["risk_id"]: r["true_erm_node_id"] for r in _read(key, "risk_clusters")}
    ia_node = {r["risk_id"]: r["taxonomy_node_id"] for r in _read(build_dir, "taxonomy_node_classifies_risk_ia")}
    canon_risk = {r["canonical_risk_id"]: r for r in _read(rec, "canonical_risk")}
    maps = [r for r in _read(rec, "risk_maps_to_canonical") if r["source"] == "IA"]
    placed = {r["risk_id"]: (canon_risk[r["canonical_risk_id"]]["erm_l3_node_id"], canon_risk[r["canonical_risk_id"]]["placement"])
              for r in maps}
    misfiled = {i for i in placed if truth[ia_node[i]] == "unmapped" or truth[ia_node[i]] not in ancestors(true_node[i])}
    out["placement"] = placement_figures(sorted(placed), placed, true_node, misfiled)
    out["review_queue"] = {f"{k}/{r}": n for (k, r), n in sorted(Counter((q["kind"], q["reason"]) for q in queue).items())}
    out["review_queue"]["total"] = len(queue)

    # citation cue: the committed control model with and without it, at pair-band level (AC-2)
    (rX, rpairs), _ = risk_tables(build_dir)
    cX, cpairs = control_table(build_dir, dict(zip(rpairs, probability(weights["risk"], rX))))
    ccluster = {r["control_id"]: r["cluster_id"] for r in _read(key, "control_clusters")}
    y = np.array([ccluster[a] != "none" and ccluster[a] == ccluster[b] for a, b in cpairs])
    ablated = weights["control_without_citation"]
    keep = [k for k, name in enumerate(weights["control"]["columns"]) if name in ablated["columns"]]
    out["citation_cue"] = {"with": band_figures(weights["control"], cX, y),
                           "without": band_figures(ablated, cX[:, keep], y)}

    out["caveats"] = {name: text.format(
        orphans=out["orphan_controls"]["orphans"], orphans_merged=out["orphan_controls"]["merged"],
        orphans_queued=out["orphan_controls"]["queue_rows"], training_seed=weights["training_seed"],
        risk_merged=out["risk"]["merged"], control_merged=out["control"]["merged"],
        risk_raw=f'{out["risk"]["raw_accept_precision"]["count"]} ({out["risk"]["raw_accept_precision"]["value"]:.2f})',
        risk_f1=f'{out["risk"]["f1"]:.2f}', control_f1=f'{out["control"]["f1"]:.2f}') for name, text in CAVEATS.items()}
    return out


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="akg-score-") as tmp:
        out = Path(tmp) / "bank"
        subprocess.run([sys.executable, "-m", "akg", "build", "--seed", str(PUBLISHED_SEED), "--size", "full",
                        "--out", str(out)], cwd=ROOT, check=True, capture_output=True)
        result = score(out)
    SCORES.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {SCORES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
