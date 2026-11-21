"""Map each IA taxonomy node onto an ERM node by a risk-level vote (E2 child a, change 011).

Each IA risk votes for its most similar ERM risk (similarity.py). A vote counts for every ancestor
of the IA risk's node, toward every ancestor of the ERM risk's node. An IA node's share for an ERM
node is votes / IA risks in its subtree. It maps to the deepest ERM node at an allowed level with a
share of at least MAJORITY (then the highest share, then the lowest ID), else `unmapped`. A node
whose subtree holds no IA risk is `unmapped` with basis `no_risks`.
Reads published files only (INV-6).
"""
from collections import defaultdict
from pathlib import Path

import numpy as np

from .similarity import read, risk_similarity

MAJORITY = 0.5
UNMAPPED = "unmapped"
# IA level -> ERM levels it may map to (E1 answer-key schema: never deeper than the IA node)
ALLOWED = {1: {1}, 2: {1, 2}, 3: {2, 3}}


def _tree(build_dir: Path, source: str) -> tuple[dict, dict]:
    level = {r["taxonomy_node_id"]: int(r["level"]) for r in read(build_dir, f"taxonomy_node_{source}")}
    parent = {r["child_id"]: r["parent_id"]
              for r in read(build_dir, f"taxonomy_node_parent_of_taxonomy_node_{source}")}
    return level, parent


def _ancestors(node: str, parent: dict) -> list[str]:
    chain = [node]
    while chain[-1] in parent:
        chain.append(parent[chain[-1]])
    return chain


def vote(ia_level: dict, ia_parent: dict, erm_level: dict, erm_parent: dict,
         choices: dict[str, tuple[str, str]]) -> list[dict]:
    """choices: IA risk ID -> (its IA node, the ERM node of the ERM risk it voted for)."""
    votes = defaultdict(lambda: defaultdict(int))
    held = defaultdict(int)
    for ia_node, erm_node in choices.values():
        for a in _ancestors(ia_node, ia_parent):
            held[a] += 1
            for e in _ancestors(erm_node, erm_parent):
                votes[a][e] += 1
    rows = []
    for node in sorted(ia_level):
        if not held[node]:
            rows.append({"ia_node_id": node, "erm_node_id": UNMAPPED, "score": 0.0, "basis": "no_risks"})
            continue
        allowed = [(e, n / held[node]) for e, n in votes[node].items() if erm_level[e] in ALLOWED[ia_level[node]]]
        winners = [(e, share) for e, share in allowed if share >= MAJORITY]
        if winners:
            target, share = min(winners, key=lambda w: (-erm_level[w[0]], -w[1], w[0]))
        else:
            target, share = UNMAPPED, max((s for _, s in allowed), default=0.0)
        rows.append({"ia_node_id": node, "erm_node_id": target, "score": round(share, 6), "basis": "vote"})
    return rows


def map_taxonomy(build_dir: Path) -> list[dict]:
    """One row per IA taxonomy node: ia_node_id, erm_node_id (or `unmapped`), score, basis."""
    ia_level, ia_parent = _tree(build_dir, "ia")
    erm_level, erm_parent = _tree(build_dir, "erm")
    node_of = {r["risk_id"]: r["taxonomy_node_id"] for source in ("erm", "ia")
               for r in read(build_dir, f"taxonomy_node_classifies_risk_{source}")}
    ia_ids, erm_ids, sims = risk_similarity(build_dir)
    best = np.argmax(sims, axis=1)  # first maximum: erm_ids are sorted, so ties go to the lowest ID
    choices = {i: (node_of[i], node_of[erm_ids[b]]) for i, b in zip(ia_ids, best)}
    return vote(ia_level, ia_parent, erm_level, erm_parent, choices)
