"""AC-9: the README data dictionary lists exactly the files and columns the build writes."""
import csv
import unittest

from .dictionary import TYPES, parse
from .helpers import build


class DataDictionaryTests(unittest.TestCase):
    def test_ac9_data_dictionary_matches_output(self):
        out = build()
        spec = parse()
        written = {p.relative_to(out).as_posix(): p for p in out.rglob("*.csv")}
        self.assertEqual(set(spec), set(written), "files in README vs files written")

        for name, path in written.items():
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                columns = reader.fieldnames
            self.assertEqual([c for c, _, _ in spec[name]], columns, f"{name}: columns differ from README")
            for column, type_, values in spec[name]:
                self.assertIn(type_, TYPES, f"{name}.{column}: unknown type {type_}")
                if type_ == "text":
                    self.assertTrue(values.startswith("name_list: ") or values == "free_text",
                                    f"{name}.{column}: text column must be marked name_list or free_text")
                if type_ == "enum":
                    allowed = {v.strip() for v in values.split(",")}
                    found = {r[column] for r in rows}
                    self.assertLessEqual(found, allowed, f"{name}.{column}: values outside the README")


if __name__ == "__main__":
    unittest.main()
