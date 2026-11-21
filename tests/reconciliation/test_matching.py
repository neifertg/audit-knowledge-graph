"""E2 child b (012): pair features, the training script, committed weights and pair scores."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.features.reconciliation import features as F
from src.features.reconciliation import match as M
from src.features.reconciliation import train as T

from .helpers import ROOT, answer_key, full_build

FEATURE_DIR = ROOT / "src" / "features" / "reconciliation"


def truth(out: Path, kind: str, pairs: list) -> np.ndarray:
    key = "risk_id" if kind == "risk" else "control_id"
    cluster = {r[key]: r["cluster_id"] for r in answer_key(out, f"{kind}_clusters")}
    return np.array([cluster[a] != "none" and cluster[a] == cluster[b] for a, b in pairs])


def outcome(out: Path, scores: dict) -> dict:
    """kind -> counts, printed for the record."""
    result = {}
    for kind, source in (("risk", "risk"), ("duplicate", "risk"), ("control", "control")):
        y = truth(out, source, scores[kind]["pairs"])
        band = np.array(scores[kind]["band"])
        accepted, queued = band == "accept", band == "review"
        result[kind] = {"true": int(y.sum()), "accepted": int(accepted.sum()),
                        "precision": (accepted & y).sum() / accepted.sum() if accepted.any() else None,
                        "queued": int(queued.sum()), "missed": int((y & (band == "below")).sum())}
        result[kind]["recall_at_floor"] = 1 - result[kind]["missed"] / result[kind]["true"]
        print(f"\n{out.name} {kind}: {result[kind]}")
    return result


class MatchingTests(unittest.TestCase):
    def test_ac1_feature_tables_shapes_columns_and_definitions(self):
        # tail score: average rank of ties, p = rank / (n - 1), -log10(1 - p + 1/n)
        values = np.array([0.1, 0.5, 0.5, 0.9])
        p = np.array([0, 1.5, 1.5, 3]) / 3
        np.testing.assert_allclose(F.tail(values), -np.log10(1 - p + 1 / 4))
        np.testing.assert_allclose(F.row_rank(np.array([[0.2, 0.9, 0.2]])), [[1 / 2, 1, 1 / 3]])
        self.assertTrue(F.citation("Outgoing wire transfers: oversight", "The enterprise oversight standard on OUTGOING WIRE TRANSFERS."))
        self.assertFalse(F.citation("Outgoing wire transfers", "outgoing wire transfers"), "no ':' -> 0")
        self.assertFalse(F.citation("Card disputes: policy", "outgoing wire transfers"))

        out = full_build(42)
        (rX, rpairs), (dX, dpairs) = F.risk_tables(out)
        self.assertEqual((rX.shape, len(rpairs)), ((27000, len(F.RISK_COLUMNS)), 27000))
        self.assertEqual((dX.shape, len(dpairs)), ((16110, len(F.DUPLICATE_COLUMNS)), 16110))
        self.assertEqual(rpairs, sorted(rpairs, key=lambda p: (p[1], p[0])), "IA-major, both sorted")
        both = rX[:, F.RISK_COLUMNS.index("shared_entity")] * rX[:, F.RISK_COLUMNS.index("shared_unit_only")]
        self.assertEqual(both.sum(), 0, "shared_unit_only excludes pairs sharing an entity")
        for c in ("shared_entity", "shared_unit_only", "taxonomy", "same_rating"):
            self.assertTrue(set(np.unique(rX[:, F.RISK_COLUMNS.index(c)])) <= {0.0, 1.0}, c)
        self.assertTrue(all(a < b for a, b in dpairs), "unordered ERM pairs, no self-pairs")
        cX, cpairs = F.control_table(out, {p: 0.5 for p in rpairs})
        self.assertEqual((cX.shape, len(cpairs)), ((118105, len(F.CONTROL_COLUMNS)), 118105))
        self.assertTrue(set(np.unique(cX[:, F.CONTROL_COLUMNS.index("risk_link")])) <= {0.0, 0.5})

    def test_ac2_threshold_rule(self):
        # scores high->low with labels; ties at 0.8
        s = np.array([0.9, 0.8, 0.8, 0.7, 0.6, 0.5])
        y = np.array([1, 1, 0, 1, 0, 1], bool)
        auto, floor = T.thresholds(s, y)
        self.assertEqual(auto, 0.9, "only the top group (1/1) reaches 95%; the 0.8 tie group drops it to 2/3")
        self.assertEqual(floor, 0.5, "99% of true pairs needs every one")
        # ties count together at the cut: {0.8, 0.8} enters as one group (precision 2/3 after it)
        s2, y2 = np.array([0.8, 0.8, 0.3]), np.array([1, 0, 1], bool)
        self.assertEqual(T.thresholds(s2, y2), (None, 0.3), "no qualifying score -> no auto-accept")
        # lowest qualifying score: precision stays >= 0.95 down to 0.4
        s3 = np.linspace(1.0, 0.0, 41)[:40]
        y3 = np.array([True] * 39 + [False])
        self.assertAlmostEqual(T.thresholds(s3, y3)[0], s3[39])  # 39/40 = 0.975 still qualifies

    def test_ac2_committed_weights_are_current(self):
        weights = M.load_weights()
        with tempfile.TemporaryDirectory() as tmp:
            bank = Path(tmp) / "bank"
            T.build_training_bank(bank)
            self.assertEqual(T.fingerprint(bank), weights["fingerprint"], "re-run the training script")
            fresh = T.train(bank)
        for kind in M.KINDS:
            with self.subTest(kind=kind):
                np.testing.assert_allclose(fresh[kind]["coefficients"], weights[kind]["coefficients"], atol=1e-6)
                self.assertAlmostEqual(fresh[kind]["intercept"], weights[kind]["intercept"], delta=1e-6)
                for which in ("auto_accept_pair", "review_floor_pair"):
                    self.assertEqual(fresh[kind][which], weights[kind][which])
        self.assertIsNone(weights["duplicate"]["auto_accept"], "duplicates are review-only")
        published = M.pair_scores(full_build(42))
        again = M.pair_scores(full_build(42), fresh)
        for kind in M.KINDS:
            self.assertEqual(published[kind]["band"], again[kind]["band"], f"{kind}: every pair keeps its band")

    def test_ac3_transfer_to_the_published_bank(self):
        out = full_build(42)
        r = outcome(out, M.pair_scores(out))
        for kind in ("risk", "control"):
            self.assertGreaterEqual(r[kind]["precision"], 0.90, kind)
            self.assertGreaterEqual(r[kind]["recall_at_floor"], 0.95, kind)
        self.assertEqual(r["duplicate"]["accepted"], 0)
        self.assertGreaterEqual(r["duplicate"]["recall_at_floor"], 0.75)

    def test_ac4_transfer_to_another_bank(self):
        out = full_build(1, "templated")
        r = outcome(out, M.pair_scores(out))
        for kind in ("risk", "control"):
            self.assertGreaterEqual(r[kind]["precision"], 0.90, kind)
            self.assertGreaterEqual(r[kind]["recall_at_floor"], 0.95, kind)
        self.assertEqual(r["duplicate"]["accepted"], 0)
        self.assertGreaterEqual(r["duplicate"]["recall_at_floor"], 0.75)

    def test_ac5_scoring_never_reads_the_answer_key(self):
        out = full_build(42)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "build"
            shutil.copytree(out, copy, ignore=shutil.ignore_patterns("answer_key"))
            a, b = M.pair_scores(out), M.pair_scores(copy)
        for kind in M.KINDS:
            np.testing.assert_array_equal(a[kind]["score"], b[kind]["score"])
        mentions = sorted(p.name for p in FEATURE_DIR.glob("*.py") if "answer_key" in p.read_text(encoding="utf-8"))
        self.assertEqual(mentions, ["train.py"])

    def test_ac6_docs_describe_matching(self):
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        readme = (FEATURE_DIR / "README.md").read_text(encoding="utf-8")
        for phrase in ("weights.json", "review-only", "training bank", "tail score", "10 of 13"):
            self.assertIn(phrase, doc)
        for name in ("features.py", "train.py", "match.py", "weights.json"):
            self.assertIn(name, readme)
        self.assertEqual(json.loads((FEATURE_DIR / "weights.json").read_text(encoding="utf-8"))["training_seed"], 7)


if __name__ == "__main__":
    unittest.main()
