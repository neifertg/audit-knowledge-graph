"""AC-1: the sample build writes every entity and relationship file in the agreed layout."""
import unittest

from .helpers import build, tables

SHARED_ENTITIES = ["segment", "business_unit", "auditable_entity", "process", "system", "person",
                   "regulation", "audit", "issue"]
SOURCED_ENTITIES = ["taxonomy_node", "risk", "control"]
SHARED_RELATIONSHIPS = [
    "segment_has_business_unit", "business_unit_owns_auditable_entity", "auditable_entity_performs_process",
    "process_runs_on_system", "audit_covered_auditable_entity", "audit_raised_issue", "issue_owned_by_person",
]
SOURCED_RELATIONSHIPS = [
    "taxonomy_node_parent_of_taxonomy_node", "taxonomy_node_classifies_risk", "auditable_entity_exposed_to_risk",
    "control_mitigates_risk", "control_depends_on_system", "regulation_requires_control",
    "control_owned_by_person", "issue_against_control", "issue_against_risk",
]


def expected_entities() -> set[str]:
    return set(SHARED_ENTITIES) | {f"{e}_{s}" for e in SOURCED_ENTITIES for s in ("erm", "ia")}


def expected_relationships() -> set[str]:
    sourced = {f"{r}_{s}" for r in SOURCED_RELATIONSHIPS for s in ("erm", "ia")}
    return set(SHARED_RELATIONSHIPS) | sourced | {"audit_tested_control_ia"}


class SampleBuildTests(unittest.TestCase):
    def test_ac1_sample_build_writes_every_entity_and_edge(self):
        out = build()
        written = tables(out)
        self.assertEqual(set(written), expected_entities() | expected_relationships())
        self.assertFalse((out / "audit_tested_control_erm.csv").exists(), "audits test IA controls only")
        for forbidden in ("canonical", "maps_to"):
            self.assertFalse([n for n in written if forbidden in n], f"{forbidden} belongs in answer_key/ only")

        for name in expected_relationships():
            self.assertGreaterEqual(len(written[name]), 1, f"{name} has no rows")
        for name in expected_entities():
            limit = 30 if name.startswith("taxonomy_node") else 20
            self.assertTrue(1 <= len(written[name]) <= limit, f"{name} has {len(written[name])} rows")


if __name__ == "__main__":
    unittest.main()
