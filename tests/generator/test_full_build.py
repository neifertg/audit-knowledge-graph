"""Child b (006): the organization, regulations and taxonomies at full size."""
import unittest
from collections import defaultdict

from .helpers import build, read

FULL = ("--size", "full")
DATA_MODEL_SEGMENTS = {"Consumer Banking", "Commercial Banking", "Wealth Management", "Treasury & Markets",
                       "Operations", "Technology", "Corporate Functions"}
B_RELATIONSHIPS = ["segment_has_business_unit", "business_unit_owns_auditable_entity",
                   "auditable_entity_performs_process", "process_runs_on_system",
                   "taxonomy_node_parent_of_taxonomy_node_erm", "taxonomy_node_parent_of_taxonomy_node_ia"]


class FullBuildTests(unittest.TestCase):
    def test_ac1_full_build_org_counts_within_targets(self):
        out = build(*FULL)
        count = lambda name: len(read(out, name))
        self.assertEqual({r["name"] for r in read(out, "segment")}, DATA_MODEL_SEGMENTS)
        for name, low, high in (("auditable_entity", 72, 88), ("person", 108, 132), ("system", 27, 33),
                                ("regulation", 14, 16), ("business_unit", 25, 35), ("process", 80, 160)):
            with self.subTest(entity=name):
                self.assertTrue(low <= count(name) <= high, f"{name}: {count(name)} not in {low}-{high}")
        for name in B_RELATIONSHIPS:
            self.assertGreater(count(name), 0, f"{name} has no rows")

        performing = {r["auditable_entity_id"] for r in read(out, "auditable_entity_performs_process")}
        self.assertEqual({r["auditable_entity_id"] for r in read(out, "auditable_entity")} - performing, set(),
                         "every auditable entity performs at least one process")
        on_system = {r["process_id"] for r in read(out, "process_runs_on_system")}
        self.assertGreaterEqual(len(on_system) / count("process"), 0.8, "fewer than 80% of processes use a system")

        # entities c-e own stay at sample size in this change
        for name in ("risk_erm", "risk_ia", "control_erm", "control_ia", "audit", "issue"):
            self.assertEqual(count(name), len(read(build(), name)), f"{name} changed size")

    def test_ac8_systems_are_shared_across_units(self):
        out = build(*FULL)
        unit_of = {r["auditable_entity_id"]: r["business_unit_id"]
                   for r in read(out, "business_unit_owns_auditable_entity")}
        segment_of = {r["business_unit_id"]: r["segment_id"] for r in read(out, "segment_has_business_unit")}
        entity_of = {r["process_id"]: r["auditable_entity_id"] for r in read(out, "auditable_entity_performs_process")}
        units = defaultdict(set)
        for r in read(out, "process_runs_on_system"):
            units[r["system_id"]].add(unit_of[entity_of[r["process_id"]]])
        systems = {r["system_id"] for r in read(out, "system")}
        self.assertEqual(systems - set(units), set(), "orphan systems run no process")
        shared = {s: u for s, u in units.items() if len(u) >= 3}
        self.assertGreaterEqual(len(shared), 8, "fewer than 8 systems serve 3+ business units")
        spanning = [s for s, u in shared.items() if len({segment_of[b] for b in u}) >= 2]
        self.assertGreaterEqual(len(spanning), 3, "fewer than 3 shared systems span 2+ segments")


if __name__ == "__main__":
    unittest.main()
