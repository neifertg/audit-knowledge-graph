"""E2 child d (014): score the reconciliation against the answer key; publish scores.json."""
import json
import re
import unittest

import numpy as np

from src.features.reconciliation import score as S

from .helpers import ROOT, full_build


class ScoringTests(unittest.TestCase):
    def test_ac1_figures_from_a_reconciled_build(self):
        # cross-source pairs: E1-I1 true merged, E2-I2 false merged, E3-I3 true queued,
        # E4-I4 true missed, E3-I5 a conflict row (false), I6 unmatched singleton
        cluster = {"E1": "A", "I1": "A", "E2": "B", "I2": "Z", "E3": "C", "I3": "C", "E4": "D", "I4": "D",
                   "I5": "none", "I6": "none"}
        canonical = {"E1": "c1", "I1": "c1", "E2": "c2", "I2": "c2", "E3": "c3", "I3": "c4", "E4": "c5",
                     "I4": "c6", "I5": "c7", "I6": "c8"}
        queued = {("E3", "I3"), ("E3", "I5")}
        f = S.pair_figures(["E1", "E2", "E3", "E4"], ["I1", "I2", "I3", "I4", "I5", "I6"], cluster, canonical,
                           queued, {("E3", "I5")})
        self.assertEqual((f["true_pairs"], f["merged"], f["queued"], f["true_queued"], f["missed"]), (3, 2, 2, 1, 1))
        self.assertEqual(f["precision"]["count"], "1/2")
        self.assertEqual(f["recall"]["count"], "1/3")
        self.assertEqual(f["recall_if_resolved"]["count"], "2/3")
        self.assertEqual((f["raw_accept"], f["raw_accept_precision"]["count"]), (3, "1/3"))
        d = S.duplicate_figures(["E1", "E2", "E9"], {"E1": "A", "E2": "B", "E9": "A"}, {("E1", "E9"), ("E1", "E2")})
        self.assertEqual(d, {"true_pairs": 1, "queued": 2, "true_queued": 1, "missed": 0})
        rows = [{"ia_node_id": "N1", "erm_node_id": "X", "basis": "vote"},
                {"ia_node_id": "N2", "erm_node_id": "unmapped", "basis": "vote"},      # wrong: truly mapped
                {"ia_node_id": "N3", "erm_node_id": "unmapped", "basis": "no_risks"},  # right: truly unmapped
                {"ia_node_id": "N4", "erm_node_id": "Y", "basis": "vote"}]             # wrong target
        t = S.taxonomy_figures(rows, {"N1": "X", "N2": "W", "N3": "unmapped", "N4": "V"},
                               {"N1": 3, "N2": 3, "N3": 3, "N4": 3})
        self.assertEqual((t["L3"]["precision"]["count"], t["L3"]["recall"]["count"],
                          t["L3"]["accuracy_on_nodes_holding_risks"]["count"]), ("1/2", "1/3", "1/3"))
        placed = {"I1": ("X", "matched"), "I2": ("Y", "mapped"), "I3": ("Q", "nearest")}
        p = S.placement_figures(["I1", "I2", "I3"], placed, {"I1": "X", "I2": "Z", "I3": "Q"}, {"I3"})
        self.assertEqual((p["all"]["count"], p["mapped"]["count"], p["misfiled"]["count"]), ("2/3", "0/1", "1/1"))
        o = S.orphan_figures({"E7", "I8"}, {"E7": "c1", "X": "c1", "I8": "c2"}, {("E9", "I8")})
        self.assertEqual(o, {"orphans": 2, "merged": 1, "queue_rows": 1})
        # seed-42 figures, printed
        result = S.score(full_build(42))
        print("\n" + json.dumps({k: result[k] for k in ("risk", "control", "duplicate", "orphan_controls")}, indent=1))

    def test_ac2_citation_cue_share(self):
        cue = S.score(full_build(42))["citation_cue"]
        print("\ncitation cue:", json.dumps(cue))
        self.assertEqual(cue["with"]["precision"]["count"], "68/68")
        self.assertGreater(cue["with"]["precision"]["value"], cue["without"]["precision"]["value"],
                           "the cue buys precision")
        self.assertLess(cue["with"]["review_band"], cue["without"]["review_band"], "and a smaller queue")

    def test_ac3_committed_scores_are_current(self):
        committed = json.loads(S.SCORES.read_text(encoding="utf-8"))
        fresh = json.loads(json.dumps(S.score(full_build(42)), sort_keys=True))
        self.assertEqual(fresh, committed, "regenerate: .venv\\Scripts\\python -m src.features.reconciliation.score")
        self.assertEqual(set(committed["caveats"]), {"orphans", "same_generator", "one_bank", "conservative"})
        self.assertEqual(committed["provenance"]["seed"], 42)

    def test_ac4_figures_agree_with_the_reconciled_output(self):
        s = json.loads(S.SCORES.read_text(encoding="utf-8"))
        # independently recorded by children a-c (docs/data-model.md)
        self.assertEqual(s["taxonomy"]["nodes_holding_risks"]["count"], "44/62")
        self.assertEqual((s["risk"]["merged"], s["control"]["merged"]), (33, 68))
        self.assertEqual(s["review_queue"]["total"], 482)
        self.assertEqual(s["placement"]["all"]["count"], "130/150")
        # the queue figures by kind come from different code paths and must agree with the file
        queue = s["review_queue"]
        self.assertEqual(s["risk"]["queued"], queue["risk/review_band"] + queue["risk/conflict"])
        self.assertEqual(s["control"]["queued"], queue.get("control/review_band", 0) + queue.get("control/conflict", 0))
        self.assertEqual(s["duplicate"]["queued"], queue["duplicate/review_band"])
        # raw accept = merged + conflicts; the citation model "with" equals the canonical control accepts
        self.assertEqual(s["risk"]["raw_accept"], s["risk"]["merged"] + queue["risk/conflict"])
        self.assertEqual(s["citation_cue"]["with"]["accepted"], s["control"]["raw_accept"])
        for kind in ("risk", "control"):
            self.assertGreaterEqual(s[kind]["precision"]["value"], 0.95)
            self.assertGreaterEqual(s[kind]["recall_if_resolved"]["value"], 0.95)

    def test_ac5_docs_quote_the_published_figures(self):
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        s = json.loads(S.SCORES.read_text(encoding="utf-8"))
        headline = [s["risk"]["precision"]["count"], s["risk"]["recall"]["count"], s["risk"]["recall_if_resolved"]["count"],
                    s["control"]["precision"]["count"], s["control"]["recall"]["count"],
                    s["control"]["recall_if_resolved"]["count"], s["placement"]["all"]["count"],
                    s["citation_cue"]["without"]["precision"]["count"], str(s["review_queue"]["total"])]
        for figure in headline:
            self.assertIn(figure, doc)
        for phrase in ("not matcher skill", "same generator", "small samples", "deliberately conservative",
                       "Reconciliation results", "scores.json"):
            self.assertIn(phrase, doc)
        self.assertNotIn("Matching method for reconciliation (research R1).", doc, "the R1 open question is closed")
        readme = (ROOT / "src" / "features" / "reconciliation" / "README.md").read_text(encoding="utf-8")
        self.assertIn("score.py", readme)
        self.assertIn("scores.json", readme)
        self.assertIsNone(re.search(r"only module that reads an answer key", readme))


if __name__ == "__main__":
    unittest.main()
