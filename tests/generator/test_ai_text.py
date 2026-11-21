"""AC-6: missing, stale or orphan AI text fails loudly; the committed text passes."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from .helpers import ROOT, run_akg

TEXT_DIR = ROOT / "src" / "features" / "generator" / "text"
TEXT_FILE = "ai_text.jsonl"


class AiTextTests(unittest.TestCase):
    def variant(self, change) -> tuple[Path, str]:
        tmp = Path(tempfile.mkdtemp(prefix="akg-text-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        entries = [json.loads(line) for line in (TEXT_DIR / TEXT_FILE).read_text(encoding="utf-8").splitlines()]
        key = change(entries)
        with open(tmp / TEXT_FILE, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(json.dumps(e) + "\n" for e in entries)
        return tmp, key

    def build_with(self, text_dir: Path):
        out = tempfile.mkdtemp(prefix="akg-out-")
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        return run_akg("build", "--seed", "42", "--size", "sample", "--out", out, "--text", "ai", "--text-dir", str(text_dir), check=False)

    def test_ac6_missing_stale_or_orphan_ai_text_fails(self):
        unchanged, _ = self.variant(lambda entries: None)
        self.assertEqual(self.build_with(unchanged).returncode, 0)
        self.assertEqual(run_akg("check-text", "--text-dir", str(unchanged), check=False).returncode, 0)

        def remove(entries):
            return entries.pop(3)["key"]

        def alter(entries):
            entries[5]["input_hash"] = "0" * 16
            return entries[5]["key"]

        def orphan(entries):
            entries.append({"key": "risk_ia:no_such_concept", "input_hash": "0" * 16, "text": "x"})
            return "risk_ia:no_such_concept"

        for name, change in (("missing", remove), ("stale", alter)):
            with self.subTest(case=name):
                text_dir, key = self.variant(change)
                result = self.build_with(text_dir)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(key, result.stderr)

        text_dir, key = self.variant(orphan)
        result = run_akg("check-text", "--text-dir", str(text_dir), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(key, result.stderr)


if __name__ == "__main__":
    unittest.main()
