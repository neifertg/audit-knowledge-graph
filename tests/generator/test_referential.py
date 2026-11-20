"""AC-12: every relationship ID exists in the right entity file; nothing links ERM to IA."""
import unittest

from . import checks
from .helpers import build


class ReferentialTests(unittest.TestCase):
    def test_ac12_relationship_ids_exist_and_never_cross_sources(self):
        checks.referential(self, build())


if __name__ == "__main__":
    unittest.main()
