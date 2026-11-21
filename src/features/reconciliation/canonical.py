"""Canonical layer: merge accepted pairs, place risks, build the review queue (E2 child c, change 013).

Published files only (INV-6). Rules (013 plan, AC-2):
- Accepted cross-source edges are taken in order (logit desc, ERM ID, IA ID).
  Risks: an edge merges only if neither risk has a merged edge (<= 1 ERM and <= 1 IA per item).
  Controls: an edge merges only if its IA control has no merged edge (<= 1 ERM control per item).
  A losing accepted edge goes to the queue as `conflict`.
- Review-band pairs, and every duplicate pair at or above its floor, are queued as `review_band`.
- Everything unmerged is a singleton. Nothing below the auto-accept threshold merges (INV-3).
"""
from collections import defaultdict
from pathlib import Path

import numpy as np

from .match import load_weights, pair_scores
from .similarity import read, risk_similarity
from .taxonomy_map import UNMAPPED, _ancestors, _tree, map_taxonomy

KIND_ORDER = ("risk", "duplicate", "control")


def merge(scored: dict, one_to_one: bool) -> tuple[list, list]:
    """(merged [(logit, (erm, ia))], conflicts [(logit, (erm, ia))]) from accepted edges."""
    edges = [(z, p) for p, z, b in zip(scored["pairs"], scored["logit"], scored["band"]) if b == "accept"]
    edges.sort(key=lambda e: (-e[0], e[1][0], e[1][1]))
    used_erm, used_ia, merged, conflicts = set(), set(), [], []
    for z, (e, i) in edges:
        if i in used_ia or (one_to_one and e in used_erm):
            conflicts.append((z, (e, i)))
            continue
        used_erm.add(e)
        used_ia.add(i)
        merged.append((z, (e, i)))
    return merged, conflicts


def drivers(model: dict, x: np.ndarray, n: int = 3) -> str:
    """Names of the n features with the largest signed coefficient x value; ties in column order."""
    contribution = np.array(model["coefficients"]) * x
    order = sorted(range(len(contribution)), key=lambda c: (-contribution[c], c))
    return ";".join(model["columns"][c] for c in order[:n])


def review_queue(scores: dict, weights: dict, conflicts: dict) -> list[dict]:
    rows = []
    for kind in KIND_ORDER:
        s = scores[kind]
        conflict_pairs = {p for _, p in conflicts.get(kind, [])}
        for k, (pair, band) in enumerate(zip(s["pairs"], s["band"])):
            reason = "conflict" if pair in conflict_pairs else "review_band" if band == "review" else None
            if reason:
                rows.append({"kind": kind, "item_a": pair[0], "item_b": pair[1],
                             "logit": f"{s['logit'][k]:.6f}", "reason": reason,
                             "drivers": drivers(weights[kind], s["X"][k])})
    rows.sort(key=lambda r: (KIND_ORDER.index(r["kind"]), -float(r["logit"]), r["item_a"], r["item_b"]))
    return rows


def canonical_ids(groups: list[list[str]], prefix: str) -> dict[str, str]:
    """member -> canonical ID; items numbered in plain string order of their lowest member ID."""
    ordered = sorted(groups, key=min)
    width = max(4, len(str(len(ordered))))
    return {m: f"{prefix}-{n:0{width}d}" for n, group in enumerate(ordered, 1) for m in group}


def place_ia_risks(build_dir: Path, unmatched_ia: list[str]) -> dict[str, tuple[str, str]]:
    """IA-only risk -> (ERM L3 node, `mapped` | `nearest`)."""
    node_of = {r["risk_id"]: r["taxonomy_node_id"] for s in ("erm", "ia")
               for r in read(build_dir, f"taxonomy_node_classifies_risk_{s}")}
    erm_level, erm_parent = _tree(build_dir, "erm")
    mapping = {r["ia_node_id"]: r["erm_node_id"] for r in map_taxonomy(build_dir)}
    ia_ids, erm_ids, sims = risk_similarity(build_dir)
    row = {i: a for a, i in enumerate(ia_ids)}
    placed = {}
    for i in unmatched_ia:
        target = mapping[node_of[i]]
        if target != UNMAPPED and erm_level[target] == 3:
            placed[i] = (target, "mapped")
            continue
        within = [b for b, e in enumerate(erm_ids) if target != UNMAPPED and target in _ancestors(node_of[e], erm_parent)]
        candidates = within or list(range(len(erm_ids)))
        best = min(candidates, key=lambda b: (-sims[row[i], b], erm_ids[b]))
        placed[i] = (node_of[erm_ids[best]], "nearest")
    return placed


def reconcile(build_dir: Path, weights: dict | None = None) -> dict[str, list[dict]]:
    """file name (without .csv) -> rows, for <out>/reconciled/."""
    weights = weights or load_weights()
    scores = pair_scores(build_dir, weights)
    risk_merged, risk_conflicts = merge(scores["risk"], one_to_one=True)
    control_merged, control_conflicts = merge(scores["control"], one_to_one=False)

    erm_risks = sorted(r["risk_id"] for r in read(build_dir, "risk_erm"))
    ia_risks = sorted(r["risk_id"] for r in read(build_dir, "risk_ia"))
    erm_controls = sorted(r["control_id"] for r in read(build_dir, "control_erm"))
    ia_controls = sorted(r["control_id"] for r in read(build_dir, "control_ia"))
    node_of = {r["risk_id"]: r["taxonomy_node_id"] for r in read(build_dir, "taxonomy_node_classifies_risk_erm")}

    # risks: groups and placement
    risk_logit = {}
    groups, placement = [], {}
    matched_ia = {}
    for z, (e, i) in risk_merged:
        matched_ia[i] = e
        risk_logit[e] = risk_logit[i] = z
    for e in erm_risks:
        partners = [i for i, m in matched_ia.items() if m == e]
        groups.append([e] + partners)
        placement[e] = (node_of[e], "matched" if partners else "erm")
    unmatched = [i for i in ia_risks if i not in matched_ia]
    for i in unmatched:
        groups.append([i])
    placed = place_ia_risks(build_dir, unmatched)
    risk_id = canonical_ids(groups, "CR")
    canonical_risk = {}
    for group in groups:
        lead = group[0]
        node, how = placement[lead] if lead in placement else placed[lead]
        canonical_risk[risk_id[lead]] = {"canonical_risk_id": risk_id[lead], "erm_l3_node_id": node, "placement": how}

    # controls: each IA control joins at most one ERM control
    control_logit, joined = {}, defaultdict(list)
    for z, (e, i) in control_merged:
        joined[e].append(i)
        control_logit[i] = z
        control_logit[e] = max(control_logit.get(e, -np.inf), z)
    cgroups = [[e] + joined[e] for e in erm_controls]
    taken = {i for members in joined.values() for i in members}
    cgroups += [[i] for i in ia_controls if i not in taken]
    control_id = canonical_ids(cgroups, "CC")

    fmt = lambda z: "" if z is None else f"{z:.6f}"
    return {
        "canonical_risk": [canonical_risk[k] for k in sorted(canonical_risk)],
        "canonical_control": [{"canonical_control_id": c} for c in sorted(set(control_id.values()))],
        "risk_maps_to_canonical": sorted(
            ({"source": src, "risk_id": r, "canonical_risk_id": risk_id[r], "logit": fmt(risk_logit.get(r))}
             for src, ids in (("ERM", erm_risks), ("IA", ia_risks)) for r in ids),
            key=lambda x: (x["source"], x["risk_id"])),
        "control_maps_to_canonical": sorted(
            ({"source": src, "control_id": c, "canonical_control_id": control_id[c], "logit": fmt(control_logit.get(c))}
             for src, ids in (("ERM", erm_controls), ("IA", ia_controls)) for c in ids),
            key=lambda x: (x["source"], x["control_id"])),
        "ia_maps_to_erm": [{**r, "score": f"{r['score']:.6f}"} for r in map_taxonomy(build_dir)],
        "review_queue": review_queue(scores, weights, {"risk": risk_conflicts, "control": control_conflicts}),
    }


def write_reconciled(build_dir: Path) -> Path:
    """Reconcile a build directory and (re)write <build_dir>/reconciled/ from scratch."""
    import csv
    import shutil

    target = Path(build_dir) / "reconciled"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for name, rows in reconcile(build_dir).items():
        with open(target / f"{name}.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    return target
