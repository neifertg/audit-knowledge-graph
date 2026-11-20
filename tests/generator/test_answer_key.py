"""AC-2: the answer key is consistent and the sample holds every reconciliation case."""
import unittest

from . import checks
from .helpers import build


class AnswerKeyTests(unittest.TestCase):
    def test_ac2_answer_key_consistent_and_covers_each_case(self):
        for text in ("templated", "ai"):
            with self.subTest(text=text):
                checks.answer_key_rules(self, build("--text", text))


if __name__ == "__main__":
    unittest.main()
