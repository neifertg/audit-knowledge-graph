"""Invariants that hold at every size: INV-1 (taxonomy part), INV-2, and one-per-bank titles."""
import unittest
from collections import Counter

from . import checks
from .helpers import build, read

SIZES = ((), ("--size", "full"))
KEY_ONE_PER_BANK = {"Chief Credit Officer", "Chief Risk Officer", "Chief Audit Executive",
                    "Chief Information Security Officer", "Treasurer", "Controller", "BSA Officer",
                    "General Counsel"}


def one_per_bank(title: str) -> bool:
    return title.startswith(("Chief ", "Head of ")) or title in {"Treasurer", "Controller", "BSA Officer",
                                                                 "General Counsel"}


class InvariantTests(unittest.TestCase):
    def test_ac2_inv1_taxonomies_are_strict_trees(self):
        for size in SIZES:
            with self.subTest(size=size or "sample"):
                out = build(*size)
                erm = checks.strict_tree(self, out, "erm")
                ia = checks.strict_tree(self, out, "ia")
                self.assertEqual({n["name"] for n in erm if n["level"] == "1"}, checks.ERM_L1)
                if size:
                    self.assertTrue(60 <= len(erm) <= 120, f"ERM has {len(erm)} nodes")
                    self.assertTrue(40 <= len(ia) <= 100, f"IA has {len(ia)} nodes")
                    by_id = {n["taxonomy_node_id"]: n for n in erm}
                    l2_per_l1 = Counter(by_id[e["parent_id"]]["name"]
                                        for e in read(out, "taxonomy_node_parent_of_taxonomy_node_erm")
                                        if by_id[e["parent_id"]]["level"] == "1")
                    self.assertEqual({l1 for l1 in checks.ERM_L1 if l2_per_l1[l1] < 2}, set(),
                                     "every ERM L1 needs at least 2 L2 children")

    def test_ac2_inv1_each_risk_under_one_l3_of_its_source(self):
        # 007 AC-2 (INV-1, risk part) and per-source exposure coverage
        for size in SIZES:
            with self.subTest(size=size or "sample"):
                out = build(*size)
                entities = {r["auditable_entity_id"] for r in read(out, "auditable_entity")}
                for source in ("erm", "ia"):
                    l3 = {n["taxonomy_node_id"] for n in read(out, f"taxonomy_node_{source}") if n["level"] == "3"}
                    risks = {r["risk_id"] for r in read(out, f"risk_{source}")}
                    links = Counter(r["risk_id"] for r in read(out, f"taxonomy_node_classifies_risk_{source}"))
                    self.assertEqual(set(links), risks, f"{source}: every risk needs a taxonomy node")
                    self.assertEqual({k for k, v in links.items() if v != 1}, set(), f"{source}: one node per risk")
                    nodes = {r["taxonomy_node_id"] for r in read(out, f"taxonomy_node_classifies_risk_{source}")}
                    self.assertLessEqual(nodes, l3, f"{source}: risks must sit under L3 nodes of their own source")
                    exposed = read(out, f"auditable_entity_exposed_to_risk_{source}")
                    self.assertEqual(risks - {r["risk_id"] for r in exposed}, set(), f"{source}: unexposed risks")
                    if size:
                        coverage = len({r["auditable_entity_id"] for r in exposed}) / len(entities)
                        floor = 0.70 if source == "erm" else 0.60
                        self.assertGreaterEqual(coverage, floor, f"{source} exposure covers {coverage:.0%}")

    def test_ac3_inv2_each_entity_has_exactly_one_owner(self):
        for size in SIZES:
            with self.subTest(size=size or "sample"):
                out = build(*size)
                owners = Counter(r["auditable_entity_id"] for r in read(out, "business_unit_owns_auditable_entity"))
                entities = {r["auditable_entity_id"] for r in read(out, "auditable_entity")}
                self.assertEqual(set(owners), entities, "every auditable entity needs an owning business unit")
                self.assertEqual({e for e, c in owners.items() if c != 1}, set())
                segments = Counter(r["business_unit_id"] for r in read(out, "segment_has_business_unit"))
                units = {r["business_unit_id"] for r in read(out, "business_unit")}
                self.assertEqual(set(segments), units, "every business unit needs a segment")
                self.assertEqual({u for u, c in segments.items() if c != 1}, set())

    def test_ac7_one_per_bank_titles_are_unique(self):
        for size in SIZES:
            with self.subTest(size=size or "sample"):
                titles = Counter(r["title"] for r in read(build(*size), "person"))
                repeated = {t: c for t, c in titles.items() if one_per_bank(t) and c > 1}
                self.assertEqual(repeated, {}, "one-per-bank titles held by more than one person")
                if size:
                    missing = {t for t in KEY_ONE_PER_BANK if titles[t] != 1}
                    self.assertEqual(missing, set(), "key one-per-bank roles must each be held exactly once")


if __name__ == "__main__":
    unittest.main()
