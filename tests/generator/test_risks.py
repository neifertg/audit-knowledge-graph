"""Child c (007): ERM and IA risk populations at full size, and how hard they are to reconcile."""
import unittest
from collections import Counter, defaultdict

from . import checks
from .dictionary import deny_entries
from .difficulty import Risks
from .helpers import build, read

FULL = ("--size", "full")


def linking_rules(test, out) -> None:
    """Epic rules: audits test what their covered entities are exposed to; issues link per source."""
    covered = defaultdict(set)
    for r in read(out, "audit_covered_auditable_entity"):
        covered[r["audit_id"]].add(r["auditable_entity_id"])
    mitigates = defaultdict(set)
    for r in read(out, "control_mitigates_risk_ia"):
        mitigates[r["control_id"]].add(r["risk_id"])
    exposed = defaultdict(set)
    for r in read(out, "auditable_entity_exposed_to_risk_ia"):
        exposed[r["risk_id"]].add(r["auditable_entity_id"])
    tested = defaultdict(set)
    for r in read(out, "audit_tested_control_ia"):
        tested[r["audit_id"]].add(r["control_id"])
        reachable = {a for risk in mitigates[r["control_id"]] for a in exposed[risk]}
        test.assertTrue(reachable & covered[r["audit_id"]],
                        f"audit {r['audit_id']} tests {r['control_id']}, which covers none of its entities")

    audit_of = {r["issue_id"]: r["audit_id"] for r in read(out, "audit_raised_issue")}
    source = {r["issue_id"]: r["source"] for r in read(out, "issue")}
    for r in read(out, "issue_against_control_ia"):
        test.assertEqual(source[r["issue_id"]], "IA")
        test.assertIn(r["control_id"], tested[audit_of[r["issue_id"]]], "IA issue against an untested control")
    controls_of = defaultdict(set)
    for r in read(out, "issue_against_control_ia"):
        controls_of[r["issue_id"]].add(r["control_id"])
    for r in read(out, "issue_against_risk_ia"):
        test.assertTrue(any(r["risk_id"] in mitigates[c] for c in controls_of[r["issue_id"]]),
                        "IA issue against a risk its controls do not mitigate")
    for name in ("issue_against_control_erm", "issue_against_risk_erm"):
        for r in read(out, name):
            test.assertNotEqual(source[r["issue_id"]], "IA", f"{name}: IA issues link to IA items only")


def no_identical_rows(test, out) -> None:
    for name in ("risk_erm", "risk_ia", "control_erm", "control_ia"):
        pairs = Counter((r["title"], r["description"]) for r in read(out, name))
        test.assertEqual([p for p, c in pairs.items() if c > 1], [], f"{name} has identical rows")


class RiskTests(unittest.TestCase):
    def test_ac1_full_risk_counts_and_quotas(self):
        out = build(*FULL)
        r = Risks(out)
        self.assertTrue(162 <= len(r.erm_ids) <= 198, f"ERM risks: {len(r.erm_ids)}")
        self.assertTrue(135 <= len(r.ia_ids) <= 165, f"IA risks: {len(r.ia_ids)}")
        for name, value, low, high in (("overlap", r.overlap(), 0.55, 0.65),
                                       ("ERM duplicates", r.erm_duplicate_rate(), 0.05, 0.10),
                                       ("misfiled", r.misfiled_rate(), 0.10, 0.20)):
            with self.subTest(measure=name):
                self.assertTrue(low <= value <= high, f"{name} {value:.3f} not in {low}-{high}")
        bands = {"High": (0.15, 0.35), "Medium": (0.40, 0.60), "Low": (0.15, 0.35)}
        for source in ("erm", "ia"):
            ratings = Counter(row["inherent_rating"] for row in read(out, f"risk_{source}"))
            total = sum(ratings.values())
            for rating, (low, high) in bands.items():
                with self.subTest(source=source, rating=rating):
                    share = ratings[rating] / total
                    self.assertTrue(low <= share <= high, f"{source} {rating} {share:.2f} not in {low}-{high}")

    def test_ac3_answer_key_and_linking_rules_hold_at_both_sizes(self):
        for size in ((), FULL):
            with self.subTest(size=size or "sample"):
                out = build(*size)
                checks.answer_key_rules(self, out)
                checks.referential(self, out)
                checks.data_dictionary(self, out)
                checks.output_names(self, out, deny_entries())
                no_identical_rows(self, out)
                linking_rules(self, out)

    def test_ac4_risk_matching_is_hard_but_possible(self):
        out = build(*FULL)
        r = Risks(out)
        self.assertLess(r.exact_text_f1(), 0.5)
        self.assertTrue(0.40 <= r.tfidf_f1() <= 0.75, f"TF-IDF F1 {r.tfidf_f1():.3f}")
        self.assertGreaterEqual(r.hard_negative_rate(), 0.10)
        self.assertTrue(0.30 <= r.erm_duplicate_f1() <= 0.80, f"ERM duplicate F1 {r.erm_duplicate_f1():.3f}")
        for kind in ("risk", "control"):
            with self.subTest(kind=kind):
                checks.leakage(self, out, kind)

    def test_ac5_exposure_structure_does_not_leak_matches(self):
        r = Risks(build(*FULL))
        self.assertLess(r.exposure_f1(), 0.5, "exposure alone finds matches")
        self.assertLessEqual(r.combined_f1(), 0.80, "same business unit plus best text finds matches")
        self.assertLessEqual(r.entity_mention_f1(), 0.80, "entity-name words in ERM text find matches")
        self.assertGreaterEqual(r.same_unit_hard_negative_share(), 0.20)
        self.assertTrue(0.10 <= r.stale_link_share() <= 0.20, f"stale links {r.stale_link_share():.3f}")


if __name__ == "__main__":
    unittest.main()
