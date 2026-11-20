"""AC-4 (INV-9): names come only from the fictional lists; no real bank, vendor or system name appears."""
import csv
import unittest

from .dictionary import deny_entries, denied_in, name_list, parse
from .helpers import build


class NameTests(unittest.TestCase):
    def test_ac4_inv9_names_from_lists_and_no_denied_name_anywhere(self):
        out = build()
        deny = deny_entries()
        self.assertTrue(deny, "deny-list is empty")
        self.assertFalse([e for e in deny if len(e) == 1 and e[0].isalpha() and e[0] in {
            "key", "regions", "citizens", "popular", "frost", "discover", "chase", "associated"}],
            "deny-list entries must be distinctive forms, never a single common word")

        # every name list entry is clear of the deny-list
        for list_name in ("institution", "first_names", "last_names", "systems", "vendors", "titles", "people"):
            for entry in name_list(list_name):
                self.assertEqual(denied_in(entry, deny), [], f"{list_name} entry {entry!r} matches a real name")

        # name_list columns take values only from their list; no text cell names a real institution
        spec = parse()
        for name, columns in spec.items():
            with open(out / name, encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            for column, type_, values in columns:
                if type_ != "text":
                    continue
                cells = [r[column] for r in rows]
                if values.startswith("name_list: "):
                    allowed = name_list(values.split(": ", 1)[1])
                    stray = sorted(set(cells) - allowed)
                    self.assertEqual(stray, [], f"{name}.{column}: values not on the list")
                for cell in cells:
                    self.assertEqual(denied_in(cell, deny), [], f"{name}.{column}: real name in {cell!r}")
        # the AI text and the sample pack are checked here too once they exist (slices 6 and 7)


if __name__ == "__main__":
    unittest.main()
