"""Child d (008): ERM and IA control populations at full size, and how hard they are to reconcile."""
import unittest
from collections import Counter, defaultdict

from . import checks
from .dictionary import deny_entries
from .difficulty import Controls
from .helpers import answer_key, build, read
from .test_risks import linking_rules, no_identical_rows

FULL = ("--size", "full")


def kind_labels():
    from src.features.generator import library

    return [(k.erm_label, k.ia_label) for k in library.CONTROL_KINDS]


class ControlTests(unittest.TestCase):
    def test_ac1_full_control_counts_and_quotas(self):
        out = build(*FULL)
        c = Controls(out)
        self.assertTrue(270 <= len(c.erm_ids) <= 330, f"ERM controls: {len(c.erm_ids)}")
        self.assertTrue(360 <= len(c.ia_ids) <= 440, f"IA controls: {len(c.ia_ids)}")
        self.assertTrue(0.55 <= c.overlap() <= 0.65, f"overlap {c.overlap():.3f}")
        self.assertEqual(c.max_erm_per_cluster(), 1, "a cluster holds two ERM controls")
        for source in ("erm", "ia"):
            with self.subTest(source=source):
                share = c.orphan_share(source)
                self.assertTrue(0.03 <= share <= 0.06, f"{source} orphans {share:.3f}")
                orphans = [x for x in (c.erm_ids if source == "erm" else c.ia_ids) if not c.risks[x]]
                self.assertEqual([x for x in orphans if c.cluster[x] != "none"], [], "orphans sit in no cluster")
        self.assertEqual(c.detail_share(), 1.0, "every matched IA control is at least twice as long")
        self.assertTrue(c.owners_always_differ(), "matched controls share an owner")
        self.assertTrue(0.15 <= c.frequency_disagreement() <= 0.30, f"frequency {c.frequency_disagreement():.3f}")
        self.assertTrue(all(c.row[e]["control_type"] == c.row[i]["control_type"] for e, i in c.truth),
                        "matched controls disagree on type")

    def test_ac1_orphans_have_no_twin(self):
        # recompute each orphan's identity from the generated dataset; the guard refuses a forced twin
        from src.features.generator.generate import build as generate, orphan_twins

        dataset = generate(size="full")
        key_of = {(i.file, i.item_id): i.key.split(":", 1)[1] for i in dataset.text_items
                  if i.file in ("control_erm", "control_ia")}
        mitigating = {row[0] for name in ("control_mitigates_risk_erm", "control_mitigates_risk_ia")
                      for row in dataset.tables[name].rows}
        keys = {"erm": set(), "ia": set()}
        orphans = {"erm": set(), "ia": set()}
        for source in ("erm", "ia"):
            for row in dataset.tables[f"control_{source}"].rows:
                key = key_of[(f"control_{source}", row[0])]
                keys[source].add(key)
                if row[0] not in mitigating:
                    orphans[source].add(key)
        theme = lambda k: k.split("@")[0].split("#")[0]
        slot = lambda k: (theme(k), k.split("#")[1]) if "#" in k else ("specific", k)
        for source, other in (("erm", "ia"), ("ia", "erm")):
            other_slots = {slot(k) for k in keys[other]}
            twins = [k for k in orphans[source] if slot(k) in other_slots]
            self.assertEqual(twins, [], f"{source} orphans with a twin in {other}")
        self.assertTrue(orphans["erm"] and orphans["ia"])
        self.assertEqual(orphan_twins(["wire_fraud@x"], {}, [], {}, set(), {"wire_fraud@x"}, set(), set()),
                         ["wire_fraud@x"], "the guard must refuse a specific twin")
        self.assertEqual(orphan_twins([], {"wire_fraud#policy": ("wire_fraud", "policy")}, [], {}, set(), set(),
                                      set(), {("wire_fraud", "policy")}),
                         ["wire_fraud#policy"], "the guard must refuse a generic twin")

    def test_ac2_control_links_and_shared_system_scenario(self):
        for size in ((), FULL):
            with self.subTest(size=size or "sample"):
                out = build(*size)
                for source in ("erm", "ia"):
                    controls = {r["control_id"] for r in read(out, f"control_{source}")}
                    risks = {r["risk_id"] for r in read(out, f"risk_{source}")}
                    links = read(out, f"control_mitigates_risk_{source}")
                    self.assertEqual(risks - {r["risk_id"] for r in links}, set(), f"{source}: unmitigated risks")
                    self.assertLessEqual({r["risk_id"] for r in links}, risks)
                    owners = Counter(r["control_id"] for r in read(out, f"control_owned_by_person_{source}"))
                    self.assertEqual(set(owners), controls, f"{source}: controls without an owner")
                    self.assertEqual({k for k, v in owners.items() if v != 1}, set(), f"{source}: one owner each")
                # an ERM duplicate shares its original's controls
                controls_of = defaultdict(set)
                for r in read(out, "control_mitigates_risk_erm"):
                    controls_of[r["risk_id"]].add(r["control_id"])
                dup_groups = defaultdict(list)
                for r in answer_key(out, "risk_clusters"):
                    if r["source"] == "ERM" and r["cluster_id"] != "none":
                        dup_groups[r["cluster_id"]].append(r["risk_id"])
                for risks_ in dup_groups.values():
                    if len(risks_) > 1:
                        self.assertEqual(len({frozenset(controls_of[r]) for r in risks_}), 1,
                                         "an ERM duplicate must share its original's controls")
                if not size:
                    self.assertEqual(answer_key(out, "scenarios"), [], "sample size plants no scenarios")
        out = build(*FULL)
        exposed = defaultdict(set)
        risks_of = defaultdict(set)
        reach = defaultdict(set)
        for source in ("erm", "ia"):
            for r in read(out, f"auditable_entity_exposed_to_risk_{source}"):
                exposed[r["risk_id"]].add(r["auditable_entity_id"])
            for r in read(out, f"control_mitigates_risk_{source}"):
                risks_of[r["control_id"]].add(r["risk_id"])
        for source in ("erm", "ia"):
            for r in read(out, f"control_depends_on_system_{source}"):
                for risk in risks_of[r["control_id"]]:
                    reach[r["system_id"]] |= exposed[risk]
        name = {r["system_id"]: r["name"] for r in read(out, "system")}
        ranked = sorted(reach, key=lambda s: (-len(reach[s]), name[s]))
        listed = [r["item_id"] for r in answer_key(out, "scenarios") if r["scenario"] == "shared_system"]
        self.assertEqual(listed, sorted(ranked[:3]), "scenarios.csv shared_system rows differ from the ranking")
        self.assertGreater(len(reach[ranked[2]]), len(reach[ranked[3]]), "rank 3 must beat rank 4 outright")
        unit_of = {r["auditable_entity_id"]: r["business_unit_id"]
                   for r in read(out, "business_unit_owns_auditable_entity")}
        for system in ranked[:3]:
            self.assertGreaterEqual(len(reach[system]), 3)
            self.assertGreaterEqual(len({unit_of[a] for a in reach[system]}), 2)

    def test_ac3_shared_rules_hold_at_both_sizes(self):
        for size in ((), FULL):
            with self.subTest(size=size or "sample"):
                out = build(*size)
                checks.answer_key_rules(self, out)
                checks.referential(self, out)
                checks.data_dictionary(self, out)
                checks.output_names(self, out, deny_entries())
                no_identical_rows(self, out)
                linking_rules(self, out)

    def test_ac4_control_matching_is_hard_but_possible(self):
        out = build(*FULL)
        c = Controls(out)
        self.assertLess(c.exact_text_f1(), 0.5)
        self.assertLess(c.owner_frequency_f1(), 0.5)
        self.assertTrue(0.40 <= c.tfidf_f1() <= 0.75, f"TF-IDF F1 {c.tfidf_f1():.3f}")
        self.assertGreaterEqual(c.hard_negative_rate(), 0.10)
        checks.leakage(self, out, "control")

    def test_ac5_attributes_and_systems_do_not_leak_matches(self):
        c = Controls(build(*FULL))
        self.assertLess(c.attribute_f1(), 0.5, "(a) type, nature and frequency")
        self.assertLess(c.system_f1(), 0.5, "(b) shared systems")
        self.assertLess(c.regulation_f1(), 0.5, "(c) shared regulation")
        self.assertLessEqual(c.system_text_f1(), 0.80, "(d) shared system then best text")
        self.assertLessEqual(c.unit_text_f1(), 0.80, "(e) same business unit then best text")
        self.assertLessEqual(c.entity_mention_f1(), 0.80, "(f) entity-name words")
        self.assertLessEqual(c.subject_kind_f1(kind_labels()), 0.80, "(h) subject and kind in titles")
        self.assertLess(c.title_in_description_f1(), 0.5, "ERM titles quoted inside IA text (008 review)")
        for source in ("erm", "ia"):
            self.assertLess(c.count_cue(source), 0.3, f"(g) control counts reveal matches in {source}")


if __name__ == "__main__":
    unittest.main()
