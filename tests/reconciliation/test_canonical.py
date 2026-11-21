"""E2 child c (013): canonical layer, review queue, build step (INV-3, INV-6, INV-7 for E2)."""
import csv
import shutil
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from src.features.reconciliation import canonical as C
from src.features.reconciliation.match import load_weights
from src.features.reconciliation.taxonomy_map import UNMAPPED, _ancestors, _tree, map_taxonomy

from . import golden
from .helpers import ROOT, answer_key, full_build, read
from tests.generator.helpers import run_akg

FILES = {
    "canonical_risk": ["canonical_risk_id", "erm_l3_node_id", "placement"],
    "canonical_control": ["canonical_control_id"],
    "risk_maps_to_canonical": ["source", "risk_id", "canonical_risk_id", "logit"],
    "control_maps_to_canonical": ["source", "control_id", "canonical_control_id", "logit"],
    "ia_maps_to_erm": ["ia_node_id", "erm_node_id", "score", "basis"],
    "review_queue": ["kind", "item_a", "item_b", "logit", "reason", "drivers"],
}


def rec(out: Path, name: str) -> list[dict]:
    return read(out / "reconciled", name)


class CanonicalTests(unittest.TestCase):
    def test_ac1_build_writes_the_reconciled_files(self):
        for out in (full_build(42), self.sample_build()):
            with self.subTest(build=out.name):
                self.assertEqual(sorted(p.stem for p in (out / "reconciled").glob("*.csv")), sorted(FILES))
                for name, columns in FILES.items():
                    raw = (out / "reconciled" / f"{name}.csv").read_bytes()
                    self.assertNotIn(b"\r", raw, f"{name}: LF line endings")
                    rows = rec(out, name)
                    self.assertEqual(list(rows[0]) if rows else columns, columns, name)
                queue = rec(out, "review_queue")
                self.assertTrue(all(r["kind"] in C.KIND_ORDER and r["reason"] in ("review_band", "conflict") for r in queue))
                key = [(C.KIND_ORDER.index(r["kind"]), -float(r["logit"]), r["item_a"], r["item_b"]) for r in queue]
                self.assertEqual(key, sorted(key), "queue order: kind, logit desc, item_a, item_b")
                for name, first in (("risk_maps_to_canonical", "risk_id"), ("control_maps_to_canonical", "control_id")):
                    rows = rec(out, name)
                    self.assertEqual([(r["source"], r[first]) for r in rows], sorted((r["source"], r[first]) for r in rows))
        # --no-reconcile removes a stale reconciled/ folder
        with tempfile.TemporaryDirectory() as tmp:
            run_akg("build", "--size", "sample", "--out", tmp)
            self.assertTrue((Path(tmp) / "reconciled").exists())
            run_akg("build", "--size", "sample", "--out", tmp, "--no-reconcile")
            self.assertFalse((Path(tmp) / "reconciled").exists())

    def sample_build(self) -> Path:
        if not hasattr(CanonicalTests, "_sample"):
            CanonicalTests._tmp = tempfile.TemporaryDirectory(prefix="akg-sample-")
            CanonicalTests._sample = Path(CanonicalTests._tmp.name) / "sample"
            run_akg("build", "--size", "sample", "--out", str(CanonicalTests._sample))
        return CanonicalTests._sample

    def test_ac2_assignment_and_placement_rules(self):
        scored = {"pairs": [("E1", "I1"), ("E1", "I2"), ("E2", "I1"), ("E3", "I3"), ("E4", "I4")],
                  "logit": np.array([9.0, 8.0, 7.0, 6.0, 1.0]),
                  "band": ["accept", "accept", "accept", "accept", "review"]}
        merged, conflicts = C.merge(scored, one_to_one=True)
        self.assertEqual([p for _, p in merged], [("E1", "I1"), ("E3", "I3")])
        self.assertEqual([p for _, p in conflicts], [("E1", "I2"), ("E2", "I1")], "two-IA and two-ERM conflicts")
        merged, conflicts = C.merge(scored, one_to_one=False)  # controls: each IA joins its best ERM
        self.assertEqual([p for _, p in merged], [("E1", "I1"), ("E1", "I2"), ("E3", "I3")])
        self.assertEqual([p for _, p in conflicts], [("E2", "I1")])
        tie = {"pairs": [("E2", "I1"), ("E1", "I1")], "logit": np.array([5.0, 5.0]), "band": ["accept", "accept"]}
        self.assertEqual(C.merge(tie, True)[0][0][1], ("E1", "I1"), "ties: lower ERM ID first")
        self.assertEqual(C.canonical_ids([["B2", "A9"], ["A1"], ["C1"]], "CR"),
                         {"A1": "CR-0001", "A9": "CR-0002", "B2": "CR-0002", "C1": "CR-0003"})
        model = {"columns": ["a", "b", "c", "d"], "coefficients": [1.0, 2.0, -1.0, 2.0]}
        self.assertEqual(C.drivers(model, np.array([1.0, 1.0, 5.0, 1.0])), "b;d;a", "signed, ties in column order")
        # placement on the real seed-42 build follows the rule
        out = full_build(42)
        node_of = {r["risk_id"]: r["taxonomy_node_id"] for s in ("erm", "ia") for r in read(out, f"taxonomy_node_classifies_risk_{s}")}
        erm_level, erm_parent = _tree(out, "erm")
        mapping = {r["ia_node_id"]: r["erm_node_id"] for r in map_taxonomy(out)}
        ia_only = [i for i in sorted(r["risk_id"] for r in read(out, "risk_ia"))]
        placed = C.place_ia_risks(out, ia_only)
        for i, (node, how) in placed.items():
            target = mapping[node_of[i]]
            self.assertEqual(erm_level[node], 3, i)
            if how == "mapped":
                self.assertEqual(node, target)
            elif target != UNMAPPED:
                self.assertIn(target, _ancestors(node, erm_parent) + [node], f"{i}: nearest within the target's subtree")

    def test_ac3_inv3_whole_output(self):
        out = full_build(42)
        weights = load_weights()
        r_map, c_map = rec(out, "risk_maps_to_canonical"), rec(out, "control_maps_to_canonical")
        self.assertEqual(Counter(r["risk_id"] for r in r_map).most_common(1)[0][1], 1)
        self.assertEqual({r["risk_id"] for r in r_map},
                         {r["risk_id"] for s in ("erm", "ia") for r in read(out, f"risk_{s}")})
        self.assertEqual({r["control_id"] for r in c_map},
                         {r["control_id"] for s in ("erm", "ia") for r in read(out, f"control_{s}")})
        self.assertEqual({r["canonical_risk_id"] for r in r_map}, {r["canonical_risk_id"] for r in rec(out, "canonical_risk")})
        members = defaultdict(lambda: defaultdict(list))
        for rows, key, cid in ((r_map, "risk_id", "canonical_risk_id"), (c_map, "control_id", "canonical_control_id")):
            for r in rows:
                members[cid][r[cid]].append((r["source"], r[key], r["logit"]))
        for cid, kind in (("canonical_risk_id", "risk"), ("canonical_control_id", "control")):
            auto = weights[kind]["auto_accept"]
            auto_logit = np.log(auto / (1 - auto))
            for item, rows in members[cid].items():
                sources = Counter(s for s, _, _ in rows)
                self.assertLessEqual(sources["ERM"], 1, f"{item}: two ERM items")
                if kind == "risk":
                    self.assertLessEqual(sources["IA"], 1, f"{item}: two IA risks")
                if len(rows) > 1:
                    for s, _, z in rows:
                        self.assertGreaterEqual(float(z), auto_logit - 1e-5, f"{item}: merged below auto-accept")
        # figures (floors), printed for the record
        for kind, rows, key, cid in (("risk", r_map, "risk_id", "canonical_risk_id"),
                                     ("control", c_map, "control_id", "canonical_control_id")):
            truth = {r[key]: r["cluster_id"] for r in answer_key(out, f"{kind}_clusters")}
            erm = {r[cid]: r[key] for r in rows if r["source"] == "ERM"}
            merged = [(erm[r[cid]], r[key]) for r in rows if r["source"] == "IA" and r[cid] in erm]
            right = sum(truth[e] != "none" and truth[e] == truth[i] for e, i in merged)
            true_pairs = sum(1 for e in {r[key] for r in rows if r["source"] == "ERM"}
                             for i in {r[key] for r in rows if r["source"] == "IA"}
                             if truth[e] != "none" and truth[e] == truth[i])
            print(f"\n{kind}: merged {len(merged)}, precision {right / len(merged):.3f}, recall {right / true_pairs:.3f}")
            self.assertGreaterEqual(right / len(merged), 0.95)
        queue = Counter((r["kind"], r["reason"]) for r in rec(out, "review_queue"))
        print("queue:", dict(sorted(queue.items())))
        true_node = {r["risk_id"]: r["true_erm_node_id"] for r in answer_key(out, "risk_clusters")}
        canon = {r["canonical_risk_id"]: r for r in rec(out, "canonical_risk")}
        placement = defaultdict(lambda: [0, 0])
        for r in r_map:
            if r["source"] == "IA":
                c = canon[r["canonical_risk_id"]]
                placement[c["placement"]][0] += c["erm_l3_node_id"] == true_node[r["risk_id"]]
                placement[c["placement"]][1] += 1
        correct = sum(a for a, _ in placement.values())
        total = sum(b for _, b in placement.values())
        print("IA placement:", {k: f"{a}/{b}" for k, (a, b) in sorted(placement.items())}, f"= {correct}/{total}")
        self.assertGreaterEqual(correct / total, 0.80)

    def test_ac4_inv6_reconciled_output_ignores_the_answer_key(self):
        out = full_build(42)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "build"
            shutil.copytree(out, copy, ignore=shutil.ignore_patterns("answer_key", "reconciled"))
            self.assertFalse((copy / "answer_key").exists() or (copy / "reconciled").exists())
            run_akg("reconcile", "--out", str(copy))
            self.assertEqual(golden.checksums(copy), golden.checksums(out))
            self.assertEqual(len(golden.checksums(copy)), len(FILES), "every file is recreated")
        mentions = sorted(p.name for p in (ROOT / "src" / "features" / "reconciliation").glob("*.py")
                          if "answer_key" in p.read_text(encoding="utf-8"))
        self.assertEqual(mentions, ["train.py"])

    def test_ac5_reconciled_output_matches_its_golden(self):
        out = full_build(42)
        self.assertEqual(golden.checksums(out), golden.read_golden(),
                         "regenerate with: .venv\\Scripts\\python -m tests.reconciliation.golden")
        with tempfile.TemporaryDirectory() as tmp:
            again = Path(tmp) / "again"
            shutil.copytree(out, again, ignore=shutil.ignore_patterns("reconciled"))
            run_akg("reconcile", "--out", str(again))
            self.assertEqual(golden.checksums(again), golden.checksums(out), "two runs are byte-identical")

    def test_ac6_docs_describe_the_canonical_layer(self):
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        for name in FILES:
            self.assertIn(f"{name}.csv", doc)
        for phrase in ("conflict", "review_band", "drivers", "never reads the published bank's answer key",
                       "reconciliation.test_canonical.CanonicalTests.test_ac3_inv3_whole_output",
                       "reconciliation.test_canonical.CanonicalTests.test_ac4_inv6_reconciled_output_ignores_the_answer_key"):
            self.assertIn(phrase, doc)
        self.assertIn("canonical.py", (ROOT / "src" / "features" / "reconciliation" / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
