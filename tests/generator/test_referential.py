"""AC-12: every relationship ID exists in the right entity file; nothing links ERM to IA."""
import unittest

from .helpers import build, tables

SOURCED = {"taxonomy_node_id": "taxonomy_node", "parent_id": "taxonomy_node", "child_id": "taxonomy_node",
           "risk_id": "risk", "control_id": "control"}
SHARED = {"segment_id": "segment", "business_unit_id": "business_unit",
          "auditable_entity_id": "auditable_entity", "process_id": "process", "system_id": "system",
          "person_id": "person", "regulation_id": "regulation", "audit_id": "audit", "issue_id": "issue"}


class ReferentialTests(unittest.TestCase):
    def test_ac12_relationship_ids_exist_and_never_cross_sources(self):
        written = tables(build())
        ids = {name: {next(iter(row.values())) for row in rows} for name, rows in written.items()}
        relationships = [n for n, rows in written.items() if rows and len(rows[0]) == 2 and all(
            c in SOURCED or c in SHARED for c in rows[0])]
        self.assertGreater(len(relationships), 20)
        for name in relationships:
            source = name.rsplit("_", 1)[1] if name.endswith(("_erm", "_ia")) else None
            for column in written[name][0]:
                if column in SOURCED:
                    self.assertIsNotNone(source, f"{name}.{column} is sourced but the file has no source suffix")
                    entity = f"{SOURCED[column]}_{source}"
                else:
                    entity = SHARED[column]
                missing = {row[column] for row in written[name]} - ids[entity]
                self.assertFalse(missing, f"{name}.{column} references IDs missing from {entity}: {missing}")


if __name__ == "__main__":
    unittest.main()
