"""Invariants that hold at every size: INV-1 (taxonomy part), INV-2, and one-per-bank titles."""
import unittest
from collections import Counter

from .helpers import build, read

SIZES = ((), ("--size", "full"))
KEY_ONE_PER_BANK = {"Chief Credit Officer", "Chief Risk Officer", "Chief Audit Executive",
                    "Chief Information Security Officer", "Treasurer", "Controller", "BSA Officer",
                    "General Counsel"}


def one_per_bank(title: str) -> bool:
    return title.startswith(("Chief ", "Head of ")) or title in {"Treasurer", "Controller", "BSA Officer",
                                                                 "General Counsel"}


class InvariantTests(unittest.TestCase):
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
