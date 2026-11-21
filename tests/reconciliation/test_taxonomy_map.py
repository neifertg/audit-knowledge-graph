"""E2 child a (011): map IA taxonomy nodes onto ERM nodes by a risk-level vote."""
import shutil
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

from src.features.reconciliation import taxonomy_map as tm

from .helpers import ROOT, answer_key, full_build, read

# names-only baseline (character TF-IDF on node names), correct nodes per level at seed 42,
# measured before the plan; each level must at least match it (AC-3)
NAMES_ONLY_CORRECT = {1: 4, 2: 5, 3: 16}


def score(out: Path, rows: list[dict]) -> dict:
    truth = {r["ia_node_id"]: r["erm_node_id"] for r in answer_key(out, "taxonomy_map")}
    level = {r["taxonomy_node_id"]: int(r["level"]) for r in read(out, "taxonomy_node_ia")}
    vote_rows = [r for r in rows if r["basis"] == "vote"]
    right = lambda r: r["erm_node_id"] == truth[r["ia_node_id"]]
    per_level = defaultdict(lambda: [0, 0])
    for r in vote_rows:
        per_level[level[r["ia_node_id"]]][0] += right(r)
        per_level[level[r["ia_node_id"]]][1] += 1
    result = {
        "vote_nodes": len(vote_rows),
        "vote_correct": sum(map(right, vote_rows)),
        "all_accuracy": sum(map(right, rows)) / len(rows),
        "false_unmapped": sum(r["erm_node_id"] == tm.UNMAPPED and truth[r["ia_node_id"]] != tm.UNMAPPED for r in vote_rows),
        "per_level": dict(per_level),
    }
    result["vote_accuracy"] = result["vote_correct"] / result["vote_nodes"]
    print(f"\n{out.name}: nodes holding risks {result['vote_correct']}/{result['vote_nodes']} = "
          f"{result['vote_accuracy']:.3f}; " + ", ".join(f"L{l} {c}/{t}" for l, (c, t) in sorted(per_level.items()))
          + f"; all nodes {result['all_accuracy']:.3f}; falsely unmapped {result['false_unmapped']}")
    return result


class TaxonomyMapTests(unittest.TestCase):
    def test_ac1_one_row_per_ia_node_at_allowed_levels_deterministic(self):
        out = full_build(42)
        rows = tm.map_taxonomy(out)
        ia_level = {r["taxonomy_node_id"]: int(r["level"]) for r in read(out, "taxonomy_node_ia")}
        erm_level = {r["taxonomy_node_id"]: int(r["level"]) for r in read(out, "taxonomy_node_erm")}
        self.assertEqual([r["ia_node_id"] for r in rows], sorted(ia_level), "one row per IA node, sorted")
        self.assertEqual(len(rows), 75)
        for r in rows:
            with self.subTest(node=r["ia_node_id"]):
                self.assertEqual(set(r), {"ia_node_id", "erm_node_id", "score", "basis"})
                self.assertIn(r["basis"], ("vote", "no_risks"))
                self.assertTrue(0.0 <= r["score"] <= 1.0)
                if r["basis"] == "no_risks":
                    self.assertEqual((r["erm_node_id"], r["score"]), (tm.UNMAPPED, 0.0))
                elif r["erm_node_id"] == tm.UNMAPPED:
                    self.assertLess(r["score"], tm.MAJORITY)
                else:
                    self.assertGreaterEqual(r["score"], tm.MAJORITY)
                    self.assertIn(erm_level[r["erm_node_id"]], tm.ALLOWED[ia_level[r["ia_node_id"]]])
        self.assertEqual(rows, tm.map_taxonomy(out), "two runs give identical rows")

    def test_ac2_vote_picks_deepest_node_with_majority(self):
        # ERM: E1 > E2 > {E3, E4}; E1 > E5 > E6.   IA: I1 > I2 > {I3, I4, I5, I6}
        erm_level = {"E1": 1, "E2": 2, "E3": 3, "E4": 3, "E5": 2, "E6": 3}
        erm_parent = {"E2": "E1", "E3": "E2", "E4": "E2", "E5": "E1", "E6": "E5"}
        ia_level = {"I1": 1, "I2": 2, "I3": 3, "I4": 3, "I5": 3, "I6": 3}
        ia_parent = {"I2": "I1", "I3": "I2", "I4": "I2", "I5": "I2", "I6": "I2"}
        choices = {
            "r1": ("I3", "E3"), "r2": ("I3", "E3"), "r3": ("I3", "E4"),   # I3: E3 2/3 -> E3 (deepest majority)
            "r4": ("I4", "E3"), "r5": ("I4", "E4"),                        # I4: E3 1/2, E4 1/2 -> tie at L3, lower ID
            "r6": ("I5", "E3"), "r7": ("I5", "E6"), "r8": ("I5", "E4"),   # I5: no L3 majority; E2 2/3 -> E2
            # I6 holds no risks -> no_risks
        }
        rows = {r["ia_node_id"]: r for r in tm.vote(ia_level, ia_parent, erm_level, erm_parent, choices)}
        self.assertEqual((rows["I3"]["erm_node_id"], rows["I3"]["score"]), ("E3", round(2 / 3, 6)))
        self.assertEqual(rows["I4"]["erm_node_id"], "E3", "a tie at the same level goes to the lower ID")
        self.assertEqual((rows["I5"]["erm_node_id"], rows["I5"]["score"]), ("E2", round(2 / 3, 6)),
                         "no L3 majority falls back to the deepest allowed node with one")
        self.assertEqual(rows["I6"], {"ia_node_id": "I6", "erm_node_id": tm.UNMAPPED, "score": 0.0, "basis": "no_risks"})
        # I2 (L2, 8 risks): E2 holds 7/8 -> E2;  I1 (L1): E1 holds 8/8 -> E1
        self.assertEqual(rows["I2"]["erm_node_id"], "E2")
        self.assertEqual(rows["I1"]["erm_node_id"], "E1")
        # no majority anywhere allowed -> unmapped with the best share found
        # (a 1-1 split is exactly 0.5, which counts; a three-way split across branches does not)
        erm_level3 = {**erm_level, "E7": 2, "E8": 3}
        erm_parent3 = {**erm_parent, "E7": "E1", "E8": "E7"}
        split = {"a": ("I3", "E3"), "b": ("I3", "E6"), "c": ("I3", "E8")}
        lone = {r["ia_node_id"]: r for r in tm.vote({"I3": 3}, {}, erm_level3, erm_parent3, split)}["I3"]
        self.assertEqual((lone["erm_node_id"], lone["score"], lone["basis"]), (tm.UNMAPPED, round(1 / 3, 6), "vote"))

    def test_ac3_accuracy_beats_names_only_baseline(self):
        result = score(full_build(42), tm.map_taxonomy(full_build(42)))
        self.assertGreaterEqual(result["vote_accuracy"], 0.65)
        self.assertLessEqual(result["false_unmapped"], 5)
        self.assertGreaterEqual(result["all_accuracy"], 0.55)
        for level, floor in NAMES_ONLY_CORRECT.items():
            with self.subTest(level=level):
                self.assertGreaterEqual(result["per_level"][level][0], floor)

    def test_ac4_holds_on_other_seeds(self):
        for seed in (7, 1):
            with self.subTest(seed=seed):
                out = full_build(seed, "templated")
                result = score(out, tm.map_taxonomy(out))
                self.assertGreaterEqual(result["vote_accuracy"], 0.55)
                self.assertLessEqual(result["false_unmapped"], 12)

    def test_ac5_never_reads_the_answer_key(self):
        out = full_build(42)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "build"
            shutil.copytree(out, copy, ignore=shutil.ignore_patterns("answer_key"))
            self.assertFalse((copy / "answer_key").exists())
            self.assertEqual(tm.map_taxonomy(copy), tm.map_taxonomy(out))
        for name in ("taxonomy_map.py", "similarity.py"):
            source = (ROOT / "src" / "features" / "reconciliation" / name).read_text(encoding="utf-8")
            self.assertNotIn("answer_key", source, name)

    def test_ac6_data_model_and_readme_describe_the_mapping(self):
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        for phrase in ("ia_maps_to_erm", "`ia_node_id`", "`erm_node_id`", "`score`", "`basis`", "no_risks",
                       "not detected"):
            self.assertIn(phrase, doc)
        readme = (ROOT / "src" / "features" / "reconciliation" / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("TODO", readme)
        self.assertIn("taxonomy_map.py", readme)


if __name__ == "__main__":
    unittest.main()
