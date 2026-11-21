"""Child e (009): three years of audits and issues at full size, and the planted scenarios."""
import re
import statistics
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from . import checks
from .golden import checksums
from .helpers import ROOT, answer_key, build, read, run_akg

FULL = ("--size", "full")
WINDOW = ("2023-01-01", "2025-12-31")


class Audits:
    """What audits covered and tested, recomputed from published files."""

    def __init__(self, out):
        self.covered = defaultdict(set)
        for r in read(out, "audit_covered_auditable_entity"):
            self.covered[r["audit_id"]].add(r["auditable_entity_id"])
        self.tested = defaultdict(set)
        for r in read(out, "audit_tested_control_ia"):
            self.tested[r["audit_id"]].add(r["control_id"])
        self.risk_of_control = defaultdict(set)
        for r in read(out, "control_mitigates_risk_ia"):
            self.risk_of_control[r["control_id"]].add(r["risk_id"])
        self.entity_of_risk = {}
        self.risks_of_entity = defaultdict(set)
        for r in read(out, "auditable_entity_exposed_to_risk_ia"):
            self.entity_of_risk[r["risk_id"]] = r["auditable_entity_id"]
            self.risks_of_entity[r["auditable_entity_id"]].add(r["risk_id"])
        self.rating = {r["risk_id"]: r["inherent_rating"] for r in read(out, "risk_ia")}
        self.audits_of_entity = Counter(a for entities in self.covered.values() for a in entities)

    def tested_risks(self, audit_id=None) -> set:
        audits = [audit_id] if audit_id else list(self.tested)
        return {r for a in audits for c in self.tested[a] for r in self.risk_of_control[c]}


class IssueTests(unittest.TestCase):
    def test_ac1_full_audit_and_issue_mix(self):
        out = build(*FULL)
        audits = read(out, "audit")
        self.assertTrue(68 <= len(audits) <= 82, f"{len(audits)} audits")
        per_year = Counter(a["audit_year"] for a in audits)
        for year in ("2023", "2024", "2025"):
            self.assertGreaterEqual(per_year[year], 20, f"{year}: {per_year[year]} audits")
        issues = read(out, "issue")
        self.assertTrue(225 <= len(issues) <= 275, f"{len(issues)} issues")
        share = Counter(i["source"] for i in issues)
        for source, (low, high) in {"IA": (0.40, 0.60), "Regulator": (0.10, 0.20),
                                    "Self-identified": (0.10, 0.20), "2nd line": (0.10, 0.20)}.items():
            self.assertTrue(low <= share[source] / len(issues) <= high, f"{source} {share[source]}")
        ratings = Counter(i["rating"] for i in issues)
        for rating, (low, high) in {"High": (0.15, 0.35), "Medium": (0.40, 0.60), "Low": (0.15, 0.35)}.items():
            self.assertTrue(low <= ratings[rating] / len(issues) <= high, f"{rating} {ratings[rating]}")
        early = [i for i in issues if i["opened_date"] < "2025-07-01"]
        closed = sum(bool(i["closed_date"]) for i in early) / len(early)
        self.assertTrue(0.40 <= closed <= 0.70, f"closed share {closed:.2f}")
        # full size is the default; too few audits or issues fail loudly; packs default to the sample
        with tempfile.TemporaryDirectory() as tmp:
            run_akg("build", "--seed", "42", "--out", tmp)
            self.assertEqual(len(read(Path(tmp), "risk_erm")), len(read(out, "risk_erm")), "default is full size")
            small = run_akg("build", "--seed", "42", "--out", tmp, "--count", "AUDIT=29", check=False)
            self.assertNotEqual(small.returncode, 0)
            self.assertIn("at least 30 audits", small.stderr)
            pack = Path(tmp) / "pack.md"
            run_akg("sample-pack", "--out", str(pack))
            self.assertIn("# Sample pack", pack.read_text(encoding="utf-8"))
        floor = build(*FULL, "--text", "templated", "--count", "AUDIT=30", "--count", "ISSUE=100")  # new items have no AI text (010)
        planted = Counter(r["scenario"].split(":")[0] for r in answer_key(floor, "scenarios"))
        self.assertGreaterEqual(len({r["scenario"] for r in answer_key(floor, "scenarios")
                                     if r["scenario"].startswith("repeat_finding:")}), 5, "minimum counts: repeats")
        self.assertGreaterEqual(planted["untested_high_risk"], 8, "minimum counts: untested High risks")
        self.assertEqual(planted["rising_category"], 1, "minimum counts: rising category")

    def test_ac3_audit_plan_is_risk_based(self):
        out = build(*FULL)
        a = Audits(out)
        for audit_id, entities in a.covered.items():
            self.assertTrue(1 <= len(entities) <= 3, f"{audit_id} covers {len(entities)} entities")
        checks.linking_rules(self, out)
        with_risk = sorted(a.risks_of_entity)
        unaudited = [e for e in with_risk if not a.audits_of_entity[e]]
        self.assertTrue(0.10 <= len(unaudited) / len(with_risk) <= 0.30, f"{len(unaudited)} of {len(with_risk)}")
        high = [e for e in with_risk if any(a.rating[r] == "High" for r in a.risks_of_entity[e])]
        low = [e for e in with_risk if e not in high]
        mean = lambda es: statistics.mean(a.audits_of_entity[e] for e in es)
        self.assertGreaterEqual(mean(high), 1.25 * mean(low), f"High {mean(high):.2f} vs other {mean(low):.2f}")
        multi = {e for e in with_risk if len(a.risks_of_entity[e]) >= 2}
        audits_of_multi = [(aid, e) for aid, es in a.covered.items() for e in es if e in multi]
        partial = [1 for aid, e in audits_of_multi if a.risks_of_entity[e] - a.tested_risks(aid)]
        self.assertGreaterEqual(len(partial) / len(audits_of_multi), 0.30, "audits must scope, not test everything")
        untested = {r["item_id"] for r in answer_key(out, "scenarios") if r["scenario"] == "untested_high_risk"}
        self.assertTrue(any(a.audits_of_entity[a.entity_of_risk[r]] for r in untested),
                        "some untested High risk must sit in an audited entity (scoping)")

    def test_ac4_planted_scenarios_are_present_and_listed(self):
        out = build(*FULL)
        a = Audits(out)
        rows = answer_key(out, "scenarios")
        listed = defaultdict(set)
        for r in rows:
            listed[r["scenario"]].add(r["item_id"])
        issues = {i["issue_id"]: i for i in read(out, "issue")}
        control_of = {r["issue_id"]: r["control_id"] for r in read(out, "issue_against_control_ia")}

        # (a) repeat findings filed under different names
        groups = {s: ids for s, ids in listed.items() if s.startswith("repeat_finding:")}
        self.assertGreaterEqual(len(groups), 5)
        ia_by_control = defaultdict(set)
        for iid, cid in control_of.items():
            ia_by_control[cid].add(iid)
        control_titles = {r["control_id"]: r["title"].lower() for r in read(out, "control_ia")}
        for name, ids in groups.items():
            with self.subTest(group=name):
                controls = {control_of[i] for i in ids}
                self.assertEqual(len(controls), 1, "one IA control per group")
                self.assertEqual(ids, ia_by_control[next(iter(controls))], "a group holds every issue on its control")
                self.assertTrue(2 <= len(ids) <= 4)
                self.assertGreaterEqual(len({issues[i]["opened_date"][:4] for i in ids}), 2)
                self.assertEqual(len({issues[i]["title"] for i in ids}), len(ids), "titles differ within a group")
        qualifying = {cid for cid, ids in ia_by_control.items()
                      if len({issues[i]["opened_date"][:4] for i in ids}) >= 2}
        listed_controls = {control_of[next(iter(ids))] for ids in groups.values()}
        self.assertEqual(listed_controls, qualifying, "every repeat finding is listed, and only those")
        for iid, cid in control_of.items():
            self.assertNotIn(control_titles[cid], issues[iid]["title"].lower(), "IA title quotes its control")
        ia_ids = [i for i in issues if issues[i]["source"] == "IA"]
        for field, cap in (("title", 0), ("description", 0.5)):
            buckets = defaultdict(set)
            for i in ia_ids:
                buckets[issues[i][field]].add(i)
            found = sum(any(ids <= b for b in buckets.values()) for ids in groups.values())
            self.assertLessEqual(found / len(groups), cap, f"grouping by exact {field} finds planted groups")

        # (b) untested High IA risks: exactly the recomputed set
        tested = a.tested_risks()
        expected = {r for r, rating in a.rating.items() if rating == "High" and r not in tested}
        self.assertEqual(listed["untested_high_risk"], expected)
        self.assertGreaterEqual(len(expected), 8)

        # (c) rising ERM L1 category on non-IA issues, published ERM taxonomy only
        nodes = {n["taxonomy_node_id"]: n for n in read(out, "taxonomy_node_erm")}
        parent = {e["child_id"]: e["parent_id"] for e in read(out, "taxonomy_node_parent_of_taxonomy_node_erm")}
        l1 = lambda node: l1(parent[node]) if node in parent else node
        node_of_risk = {r["risk_id"]: r["taxonomy_node_id"] for r in read(out, "taxonomy_node_classifies_risk_erm")}
        first_risk = {}
        for r in sorted(read(out, "issue_against_risk_erm"), key=lambda r: r["risk_id"]):
            first_risk.setdefault(r["issue_id"], r["risk_id"])
        by_l1_year = Counter((l1(node_of_risk[first_risk[i]]), issues[i]["opened_date"][:4]) for i in first_risk)
        rising = [n for n in {k[0] for k in by_l1_year}
                  if by_l1_year[(n, "2023")] >= 8 and by_l1_year[(n, "2025")] >= 1.5 * by_l1_year[(n, "2023")]]
        self.assertEqual(rising, list(listed["rising_category"]), "exactly the listed ERM L1 rises")
        years = Counter(i["opened_date"][:4] for i in issues.values())
        self.assertLess(abs(years["2025"] - years["2023"]) / years["2023"], 0.15, "total issues stay flat")

        # (d) every regulation reaches a business unit
        unit_of = {r["auditable_entity_id"]: r["business_unit_id"]
                   for r in read(out, "business_unit_owns_auditable_entity")}
        exposed, mitigates = defaultdict(set), defaultdict(set)
        for source in ("erm", "ia"):
            for r in read(out, f"auditable_entity_exposed_to_risk_{source}"):
                exposed[r["risk_id"]].add(r["auditable_entity_id"])
            for r in read(out, f"control_mitigates_risk_{source}"):
                mitigates[r["control_id"]].add(r["risk_id"])
        reach = defaultdict(set)
        for source in ("erm", "ia"):
            for r in read(out, f"regulation_requires_control_{source}"):
                for risk in mitigates[r["control_id"]]:
                    reach[r["regulation_id"]] |= {unit_of[e] for e in exposed[risk]}
        unreached = [g["name"] for g in read(out, "regulation") if not reach[g["regulation_id"]]]
        self.assertEqual(unreached, [], "regulations that reach no business unit")

    def test_ac5_every_entity_and_relationship_is_populated(self):
        out = build(*FULL)
        diagram = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        edges = re.findall(r"^\s+([A-Z_]+) [|}o{]+--[|}o{]+ ([A-Z_]+) : (\w+)", diagram, re.M)
        self.assertGreater(len(edges), 15)
        exempt_entities = {"CANONICAL_RISK", "CANONICAL_CONTROL"}
        exempt_labels = {"maps_to", "ia_maps_to_erm"}
        files = {p.stem for p in out.glob("*.csv")}
        rows = lambda stem: len(read(out, stem)) if stem in files else 0
        for left, right, label in edges:
            if label in exempt_labels or {left, right} & exempt_entities:
                continue
            with self.subTest(edge=f"{left} {label} {right}"):
                stem = f"{left.lower()}_{label}_{right.lower()}"
                self.assertGreater(sum(rows(s) for s in (stem, f"{stem}_erm", f"{stem}_ia")), 0)
        for entity in {e for left, right, _ in edges for e in (left, right)} - exempt_entities:
            with self.subTest(entity=entity):
                stem = entity.lower()
                self.assertGreater(sum(rows(s) for s in (stem, f"{stem}_erm", f"{stem}_ia")), 0)
        dup = Counter(r["cluster_id"] for r in answer_key(out, "risk_clusters")
                      if r["source"] == "ERM" and r["cluster_id"] != "none")
        self.assertTrue(any(v > 1 for v in dup.values()), "no ERM duplicate group at full size")
        from src.features.generator import library
        for source in ("erm", "ia"):
            self.assertLessEqual({r["frequency"] for r in read(out, f"control_{source}")}, set(library.FREQUENCIES))

    def test_ac6_issue_text_keys_are_natural(self):
        from src.features.generator.generate import build as generate

        for size in ("sample", "full"):
            with self.subTest(size=size):
                dataset = generate(size=size)
                control_keys = {i.key.split(":", 1)[1] for i in dataset.text_items if i.file.startswith("control_")}
                issue_keys = [i.key for i in dataset.text_items if i.file == "issue"]
                self.assertEqual(len(issue_keys), len(set(issue_keys)))
                for key in issue_keys:
                    self.assertIsNone(re.fullmatch(r"issue:\d+", key), f"positional key {key}")
                    source, control, ordinal = key.split(":", 1)[1].rsplit(":", 2)
                    self.assertIn(source, ("IA", "Regulator", "Self-identified", "2nd line"))
                    self.assertIn(control, control_keys, key)
                    self.assertTrue(ordinal.isdigit())
        self.assertEqual(run_akg("check-text", check=False).returncode, 0, "sample AI text has orphan keys")
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_akg("build", "--size", "sample", "--text", "ai", "--out", tmp,
                                     check=False).returncode, 0)

    def test_ac7_person_count_leaves_other_files_unchanged(self):
        default = checksums(build(*FULL, "--text", "templated"))  # templated vs templated: overrides have no AI text (010)
        override = build(*FULL, "--text", "templated", "--count", "PERSON=100")
        self.assertEqual(len(read(override, "person")), 100, "the override must take effect")
        changed = checksums(override)
        drift = [p for p in default if "person" not in Path(p).name and default[p] != changed[p]]
        self.assertEqual(drift, [], "--count PERSON changed files that do not name people")


if __name__ == "__main__":
    unittest.main()
