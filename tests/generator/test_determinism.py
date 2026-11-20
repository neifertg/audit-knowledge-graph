"""AC-3 (INV-7) and AC-11: byte-identical output, and independent random streams."""
import tempfile
import unittest
from pathlib import Path

from .golden import checksums, read_golden
from .helpers import build, read, run_akg


class DeterminismTests(unittest.TestCase):
    def test_ac3_inv7_output_matches_golden_checksums(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            run_akg("build", "--seed", "42", "--out", a)
            run_akg("build", "--seed", "42", "--out", b)
            first, second = checksums(Path(a)), checksums(Path(b))
            self.assertEqual(first, second, "two runs with the same seed differ")
            for path in Path(a).rglob("*.csv"):
                data = path.read_bytes()
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"), f"{path.name} has a BOM")
                self.assertNotIn(b"\r", data, f"{path.name} has CR line endings")
                data.decode("utf-8")
            self.assertEqual(first, read_golden(),
                             "output differs from tests/golden/checksums.sha256; if intended, regenerate it")

    def test_ac11_changing_one_type_count_leaves_other_types_unchanged(self):
        # streams, not text, are under test: positional issue text keys (parked for c-e) break --count with AI text
        default = checksums(build("--text", "templated"))
        for type_name, marker, file_name in (("REGULATION", "regulation", "regulation"), ("ISSUE", "issue", "issue")):
            with self.subTest(type=type_name):
                self.assertNotEqual(len(read(build("--text", "templated"), file_name)), 5,
                                    "override must differ from the default")
                override = ("--text", "templated", "--count", f"{type_name}=5")
                changed = checksums(build(*override))
                self.assertEqual(len(read(build(*override), file_name)), 5)
                unrelated = [p for p in default if marker not in Path(p).name]
                self.assertTrue(unrelated)
                drift = [p for p in unrelated if default[p] != changed[p]]
                self.assertEqual(drift, [], f"--count {type_name}=5 changed unrelated files")


if __name__ == "__main__":
    unittest.main()
