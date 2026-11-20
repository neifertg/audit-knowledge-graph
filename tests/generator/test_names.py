"""AC-4 (INV-9): names come only from the fictional lists; no real bank, vendor or system name appears."""
import csv
import json
import re
import unittest

from .dictionary import deny_entries, denied_in, name_list, parse
from .helpers import ROOT, build

TEXT_DIR = ROOT / "src" / "features" / "generator" / "text"


def capitalized_words(text: str) -> list[str]:
    """Capitalized words that do not start a sentence."""
    words = []
    for sentence in re.split(r"(?<=[.!?])\s+|;\s+|:\s+", text):
        tokens = re.findall(r"[A-Za-z][\w/&'-]*", sentence)
        words += [t.removesuffix("'s") for t in tokens[1:] if t[0].isupper()]
    return words


class NameTests(unittest.TestCase):
    def test_ac4_inv9_names_from_lists_and_no_denied_name_anywhere(self):
        out = build()
        deny = deny_entries()
        self.assertTrue(deny, "deny-list is empty")
        self.assertFalse([e for e in deny if len(e) == 1 and e[0].isalpha() and e[0] in {
            "key", "regions", "citizens", "popular", "frost", "discover", "chase", "associated"}],
            "deny-list entries must be distinctive forms, never a single common word")

        # every name list entry is clear of the deny-list
        for list_name in ("institution", "first_names", "last_names", "systems", "vendors", "titles", "people",
                          "regulations", "allow_terms"):
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
                self.assertTrue(values.startswith("name_list: ") or values == "free_text",
                                f"{name}.{column}: text column must be marked name_list or free_text")
                if values.startswith("name_list: "):
                    allowed = name_list(values.split(": ", 1)[1])
                    stray = sorted(set(cells) - allowed)
                    self.assertEqual(stray, [], f"{name}.{column}: values not on the list")
                for cell in cells:
                    self.assertEqual(denied_in(cell, deny), [], f"{name}.{column}: real name in {cell!r}")
        # committed AI text: no real names, and no capitalized word outside the name lists and allow-list
        allowed_terms = set()
        for list_name in ("systems", "vendors", "institution", "regulations", "titles", "allow_terms", "people"):
            allowed_terms |= name_list(list_name)
        allowed_words = {w for term in allowed_terms for w in re.findall(r"[A-Za-z][\w/&'-]*", term)}
        for line in (TEXT_DIR / "ai_text.jsonl").read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            self.assertEqual(denied_in(entry["text"], deny), [], f"{entry['key']}: real name in AI text")
            stray = sorted(set(capitalized_words(entry["text"])) - allowed_words)
            self.assertEqual(stray, [], f"{entry['key']}: capitalized words not on any list")
        # AI text names a system only when its templated draft does
        from src.features.generator.generate import build as generate
        from src.features.generator.write_text import added_systems

        drafts = {item.key: item.templated for item in generate().text_items}
        for line in (TEXT_DIR / "ai_text.jsonl").read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            self.assertEqual(added_systems(entry["text"], drafts[entry["key"]]), [],
                             f"{entry['key']}: AI text names a system its draft does not")
        # a freshly generated sample pack names no real institution
        from .test_sample_pack import generate_pack

        self.assertEqual(denied_in(generate_pack(), deny), [], "real name in the sample pack")


if __name__ == "__main__":
    unittest.main()
