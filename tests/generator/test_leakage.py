"""AC-7: items in one true cluster share no ID number, sentence, near-identical text or row order."""
import unittest

from . import checks
from .helpers import build


class LeakageTests(unittest.TestCase):
    def test_ac7_matched_items_share_no_id_sentence_attributes_or_order(self):
        for text in ("templated", "ai"):
            out = build("--text", text)
            for kind in ("risk", "control"):
                with self.subTest(text=text, kind=kind):
                    checks.leakage(self, out, kind)


if __name__ == "__main__":
    unittest.main()
