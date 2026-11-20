"""Check logic shared by tests at sample and full size, so each rule is written once."""
from collections import Counter

from .helpers import answer_key, read

ALLOWED_TARGET_LEVELS = {1: {1}, 2: {1, 2}, 3: {2, 3}}
ERM_L1 = {"Credit", "Market", "Liquidity", "Operational", "Compliance", "Strategic", "Reputational"}


def taxonomy_map(test, out) -> dict:
    """Every IA node mapped exactly once, to an existing ERM node at an allowed level, or unmapped.

    Returns {ia_node_id: erm_node_id or None}.
    """
    erm_nodes = {r["taxonomy_node_id"]: r for r in read(out, "taxonomy_node_erm")}
    ia_nodes = {r["taxonomy_node_id"]: r for r in read(out, "taxonomy_node_ia")}
    rows = answer_key(out, "taxonomy_map")
    test.assertEqual(sorted(r["ia_node_id"] for r in rows), sorted(ia_nodes), "IA nodes vs taxonomy_map rows")
    target = {}
    for row in rows:
        if row["erm_node_id"] == "unmapped":
            target[row["ia_node_id"]] = None
            continue
        test.assertIn(row["erm_node_id"], erm_nodes)
        ia_level = int(ia_nodes[row["ia_node_id"]]["level"])
        test.assertIn(int(erm_nodes[row["erm_node_id"]]["level"]), ALLOWED_TARGET_LEVELS[ia_level],
                      f"{row['ia_node_id']} maps to a deeper or disallowed ERM level")
        target[row["ia_node_id"]] = row["erm_node_id"]
    return target


def strict_tree(test, out, source: str) -> list[dict]:
    """INV-1 (taxonomy part): a strict three-level tree with names unique per level. Returns the nodes."""
    nodes = {r["taxonomy_node_id"]: r for r in read(out, f"taxonomy_node_{source}")}
    edges = read(out, f"taxonomy_node_parent_of_taxonomy_node_{source}")
    parents = Counter(e["child_id"] for e in edges)
    parent_of = {e["child_id"]: e["parent_id"] for e in edges}
    for nid, node in nodes.items():
        level = int(node["level"])
        test.assertIn(level, (1, 2, 3), f"{source} {nid} has level {level}")
        if level == 1:
            test.assertNotIn(nid, parents, f"{source} L1 node {nid} has a parent")
        else:
            test.assertEqual(parents[nid], 1, f"{source} {nid} needs exactly one parent")
            test.assertEqual(int(nodes[parent_of[nid]]["level"]), level - 1, f"{source} {nid} parent level")
    for level in (1, 2, 3):
        names = Counter(n["name"] for n in nodes.values() if n["level"] == str(level))
        test.assertEqual({n for n, c in names.items() if c > 1}, set(),
                         f"{source} reuses level-{level} names")
    return list(nodes.values())
