"""AC-9: the README data dictionary lists exactly the files and columns the build writes."""
import unittest

from . import checks
from .helpers import build


class DataDictionaryTests(unittest.TestCase):
    def test_ac9_data_dictionary_matches_output(self):
        checks.data_dictionary(self, build())


if __name__ == "__main__":
    unittest.main()
