"""AC-2: the answer key is consistent and the sample holds every reconciliation case."""
import statistics
import unittest
from collections import defaultdict

from .helpers import answer_key, build, cosine_by_id, read

ALLOWED_TARGET_LEVELS = {1: {1}, 2: {1, 2}, 3: {2, 3}}


def clusters(rows: list[dict], id_col: str) -> dict[str, list[dict]]:
    grouped = defaultdict(list)
    for row in rows:
        if row["cluster_id"] != "none":
            grouped[row["cluster_id"]].append(row)
    return grouped


def hard_negative_exists(out, kind: str, cluster_rows: list[dict]) -> bool:
    id_col = f"{kind}_id"
    erm, ia = read(out, f"{kind}_erm"), read(out, f"{kind}_ia")
    sims = cosine_by_id(erm, ia, id_col)
    cluster_of = {r[id_col]: r["cluster_id"] for r in cluster_rows}
    same = lambda a, b: cluster_of[a] != "none" and cluster_of[a] == cluster_of[b]
    pairs = [(e[id_col], i[id_col]) for e in erm for i in ia]
    matched = [sims[p] for p in pairs if same(*p)]
    median = statistics.median(matched)
    return any(sims[p] >= median for p in pairs if not same(*p))


class AnswerKeyTests(unittest.TestCase):
    def check(self, out):
        erm_nodes = {r["taxonomy_node_id"]: r for r in read(out, "taxonomy_node_erm")}
        ia_nodes = {r["taxonomy_node_id"]: r for r in read(out, "taxonomy_node_ia")}
        erm_parent = {r["child_id"]: r["parent_id"] for r in read(out, "taxonomy_node_parent_of_taxonomy_node_erm")}

        # taxonomy map: every IA node exactly once, valid targets at allowed levels
        tmap = answer_key(out, "taxonomy_map")
        self.assertEqual(sorted(r["ia_node_id"] for r in tmap), sorted(ia_nodes))
        target = {}
        for row in tmap:
            if row["erm_node_id"] == "unmapped":
                target[row["ia_node_id"]] = None
                continue
            self.assertIn(row["erm_node_id"], erm_nodes)
            ia_level = int(ia_nodes[row["ia_node_id"]]["level"])
            self.assertIn(int(erm_nodes[row["erm_node_id"]]["level"]), ALLOWED_TARGET_LEVELS[ia_level])
            target[row["ia_node_id"]] = row["erm_node_id"]
        self.assertGreaterEqual(sum(t is None for t in target.values()), 1, "no unmapped IA node")

        # risk clusters: every risk exactly once, true node an ERM L3, clusters share a node
        risks = {("ERM", r["risk_id"]) for r in read(out, "risk_erm")} | {("IA", r["risk_id"]) for r in read(out, "risk_ia")}
        rc = answer_key(out, "risk_clusters")
        self.assertEqual(sorted((r["source"], r["risk_id"]) for r in rc), sorted(risks))
        for row in rc:
            self.assertEqual(erm_nodes[row["true_erm_node_id"]]["level"], "3")
        risk_clusters = clusters(rc, "risk_id")
        for members in risk_clusters.values():
            self.assertEqual(len({m["true_erm_node_id"] for m in members}), 1, "cluster spans ERM nodes")
        cross = [m for m in risk_clusters.values() if {x["source"] for x in m} == {"ERM", "IA"}]
        dup = [m for m in risk_clusters.values() if sum(x["source"] == "ERM" for x in m) >= 2]
        self.assertGreaterEqual(len(cross), 5, "fewer than 5 cross-source risk matches")
        self.assertGreaterEqual(len(dup), 1, "no within-ERM duplicate")

        # misfiled IA risk: true node not under its IA node's mapped target
        ia_node_of = {r["risk_id"]: r["taxonomy_node_id"] for r in read(out, "taxonomy_node_classifies_risk_ia")}

        def ancestors(node):
            chain = [node]
            while chain[-1] in erm_parent:
                chain.append(erm_parent[chain[-1]])
            return chain

        misfiled = [r for r in rc if r["source"] == "IA"
                    and target[ia_node_of[r["risk_id"]]] not in ancestors(r["true_erm_node_id"])]
        self.assertGreaterEqual(len(misfiled), 1, "no misfiled IA risk")

        # control clusters: every control exactly once, at least 5 cross-source matches
        controls = {("ERM", r["control_id"]) for r in read(out, "control_erm")} | {("IA", r["control_id"]) for r in read(out, "control_ia")}
        cc = answer_key(out, "control_clusters")
        self.assertEqual(sorted((r["source"], r["control_id"]) for r in cc), sorted(controls))
        cross_c = [m for m in clusters(cc, "control_id").values() if {x["source"] for x in m} == {"ERM", "IA"}]
        self.assertGreaterEqual(len(cross_c), 5, "fewer than 5 cross-source control matches")

        self.assertEqual(answer_key(out, "scenarios"), [])
        self.assertTrue(hard_negative_exists(out, "risk", rc), "no hard negative among risks")
        self.assertTrue(hard_negative_exists(out, "control", cc), "no hard negative among controls")

    def test_ac2_answer_key_consistent_and_covers_each_case(self):
        for text in ("templated", "ai"):
            with self.subTest(text=text):
                self.check(build("--text", text))


if __name__ == "__main__":
    unittest.main()
