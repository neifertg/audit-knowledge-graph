"""AC-8: the sample pack shows every entity type, both text variants, the name lists and the review table."""
import tempfile
import unittest
from pathlib import Path

from .dictionary import name_list
from .helpers import run_akg

ENTITIES = ["segment", "business_unit", "auditable_entity", "process", "system", "person", "regulation",
            "taxonomy_node_erm", "taxonomy_node_ia", "risk_erm", "risk_ia", "control_erm", "control_ia",
            "audit", "issue"]


def generate_pack() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pack.md"
        run_akg("sample-pack", "--out", str(path))
        return path.read_text(encoding="utf-8")


def generate_full_pack() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pack.md"
        run_akg("sample-pack", "--size", "full", "--out", str(path))
        return path.read_text(encoding="utf-8")


class SamplePackTests(unittest.TestCase):
    def test_ac7_full_size_pack_describes_full_size(self):
        pack = generate_full_pack()
        self.assertIn("Full-size pack", pack)
        self.assertNotIn("about 15 rows", pack)
        self.assertNotIn("Text choice", pack)
        # 010 AC-5: full size shows templated and AI descriptions side by side, all generated
        self.assertEqual(pack.count("| description (templated) | description (AI) |"), 5)
        self.assertNotIn("(not generated)", pack)

    def test_ac8_committed_pack_is_current(self):
        # 009 AC-8: the committed sample pack equals a freshly generated one
        committed = Path(__file__).resolve().parents[2] / "research" / "r2-synthetic-text-realism" / "sample_pack.md"
        self.assertEqual(generate_pack(), committed.read_text(encoding="utf-8"),
                         "regenerate research/r2-synthetic-text-realism/sample_pack.md (python -m akg sample-pack)")

    def test_ac8_sample_pack_shows_every_entity_and_both_text_variants(self):
        pack = generate_pack()
        for entity in ENTITIES:
            self.assertIn(f"\n### {entity}\n", pack, f"no section for {entity}")
            self.assertIn(f"| {entity} |  |  |", pack, f"{entity} missing from the review table")
        self.assertEqual(pack.count("| description (templated) | description (AI) |"), 5)
        self.assertNotIn("(not generated)", pack)
        self.assertIn("**Text choice (templated / AI):**", pack)
        for list_name in ("institution", "first_names", "last_names", "titles", "systems", "vendors", "regulations"):
            line = next(l for l in pack.splitlines() if l.startswith(f"**{list_name}:**"))
            for entry in name_list(list_name):
                self.assertIn(entry, line, f"{list_name} entry {entry!r} missing from the pack")


if __name__ == "__main__":
    unittest.main()
