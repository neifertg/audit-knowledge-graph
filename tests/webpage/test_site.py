"""E4 child a (021): the site export, the builder, and the rules that keep every figure traceable.

Standard library only: html.parser, json and re. Visual checks are the owner's, on a local preview.
"""
import json
import re
import tempfile
import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

from src.features.site import build as B
from src.features.site import export as X
from src.features.site.formatters import FORMATTERS, count_word, fraction, names_and, plain, rows_shown, signed, times_word

from tests.generator.dictionary import denied_in, deny_entries
from tests.generator.helpers import ROOT, read
from tests.stores.test_sqlite import loaded

ALLOWED_TOKENS = {"60", "1.25", "M1", "M2", "L1"}
NUMBER_WORDS = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
                          r"fifteen|sixteen|seventeen|eighteen|nineteen|twenty|dozen|half|once|twice)\b", re.I)
SPEED_WORDS = re.compile(r"\b(faster|slower|speed|speedup|latency|milliseconds|ms)\b", re.I)
CDN = "https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.34.4/cytoscape.min.js"
SRI = "sha512-9oWrVcc9R1+KL87uqCWwsamtDPJknyeNh/xCFh5SHEsgvV7Icb5Vgungsyljhdeyt+LNKGC9bhwKKQ0C6TiPOw=="
# The approved copy's fixed text: the words between the figures (021 plan, "Top-section copy").
COPY = [
    "Audit risk hides between the tables. This is what it looks like when you connect them.",
    "A synthetic US regional bank keeps its risks in the ERM register and in Internal Audit's risk and control "
    "matrices. They describe the same business in different words. Reconciled into a single framework and connected "
    "as a graph, they show exposure no table holds on its own.",
    "Synthetic data throughout; descriptions AI-written ahead of time and committed; no real institution, person or vendor.",
    "A shared system, a wide blast radius", "fails,", "controls that depend on it are affected; between them they "
    "protect risks in", "auditable entities across", "business units.", "Plan coverage by dependency, not by org chart.",
    "A repeat finding in disguise", "controls failed in different years under different titles:",
    "issues a text search would treat as unrelated, linked through the control and the dates.",
    "Repeat findings should escalate, not reset.",
    "Concentrated ownership", "derived from the data, not planted", "each own", "key controls whose risks reach",
    "Key-person risk is visible before it becomes an issue.",
    "Does a graph beat SQL?", "planning questions in both, with the same facts and answers proved equal: SQL wins",
    "the graph", "are close.", "The difference is how much query each needs, not speed: no speed claims are made at demo scale.",
    "The graph informs auditor judgment; it does not score risk or set the audit plan.",
]


class Page(HTMLParser):
    """Visible text, marked figures and the disclosure, from a rendered page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0                 # inside <script> or <style>
        self.marked_depth = 0         # inside a data-source element
        self.disclosure_depth = 0     # inside data-disclosure="no-speed-claims"
        self.stack = []
        self.marked = []              # [source, format, text]
        self.visible, self.unmarked, self.speed_scope = [], [], []
        self.scripts = []             # (attrs, text) for <script>
        self.resources = []           # external src/href of resource tags
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag in ("script", "link", "img", "iframe") and (a.get("src") or (tag == "link" and a.get("href"))):
            self.resources.append((tag, a))
        if tag in ("script", "style"):
            self.skip += 1
            self.scripts.append([a, ""]) if tag == "script" else None
        flags = (tag in ("script", "style"), "data-source" in a, a.get("data-disclosure") == "no-speed-claims")
        if "data-source" in a:
            self.marked_depth += 1
            self.marked.append([a["data-source"], a.get("data-format", "plain"), ""])
        if flags[2]:
            self.disclosure_depth += 1
        self.stack.append((tag, flags))

    def handle_endtag(self, tag):
        while self.stack:
            open_tag, (is_skip, is_marked, is_disclosure) = self.stack.pop()
            self.skip -= is_skip
            self.marked_depth -= is_marked
            self.disclosure_depth -= is_disclosure
            if open_tag == tag:
                break

    def handle_data(self, data):
        if self.skip:
            if self.scripts and self.stack and self.stack[-1][0] == "script":
                self.scripts[-1][1] += data
            return
        self.visible.append(data)
        if self.marked_depth:
            self.marked[-1][2] += data
        else:
            self.unmarked.append(data)
            if not self.disclosure_depth:
                self.speed_scope.append(data)


def built() -> tuple[Path, str, Page]:
    if not hasattr(built, "cache"):
        tmp = tempfile.mkdtemp(prefix="akg-site-")
        B.build(Path(tmp))
        text = (Path(tmp) / "index.html").read_text(encoding="utf-8")
        page = Page()
        page.feed(text)
        built.cache = (Path(tmp), text, page)
    return built.cache


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def rounds() -> dict:
    return json.loads(B.ROUNDS_JSON.read_text(encoding="utf-8"))


class SiteTests(unittest.TestCase):
    maxDiff = None

    def test_ac1_site_export_subgraph_and_currency(self):
        out, _ = loaded()
        doc = X.document(out)
        self.assertEqual(X.render(doc), X.SITE_JSON.read_text(encoding="utf-8"),
                         "site.json is stale: run python -m src.features.site.export --out <seed-42 build>")
        # an independent computation of the subgraph from the CSVs
        both = lambda stem: read(out, stem + "_erm") + read(out, stem + "_ia")
        system = next(r for r in rounds()["rounds"] if r["number"] == 3)["rows"][0][0]
        controls = {r["control_id"] for r in both("control_depends_on_system") if r["system_id"] == system}
        mit = {(r["control_id"], r["risk_id"]) for r in both("control_mitigates_risk") if r["control_id"] in controls}
        risks = {r for _, r in mit}
        exp = {(r["risk_id"], r["auditable_entity_id"]) for r in both("auditable_entity_exposed_to_risk") if r["risk_id"] in risks}
        entities = {e for _, e in exp}
        owns = {(r["auditable_entity_id"], r["business_unit_id"]) for r in read(out, "business_unit_owns_auditable_entity")
                if r["auditable_entity_id"] in entities}
        units = {u for _, u in owns}
        nodes = {(system, "system")} | {(i, k) for k, ids in (("control", controls), ("risk", risks), ("entity", entities),
                                                               ("unit", units)) for i in ids}
        edges = ({(system, c, "depends_on") for c in controls} | {(c, r, "mitigates") for c, r in mit}
                 | {(r, e, "exposes") for r, e in exp} | {(e, u, "owned_by") for e, u in owns})
        self.assertEqual({(n["id"], n["kind"]) for n in doc["subgraph"]["nodes"]}, nodes)
        self.assertEqual({(e["source"], e["target"], e["kind"]) for e in doc["subgraph"]["edges"]}, edges)
        b = doc["blast_radius"]
        self.assertEqual((b["controls"], b["controls_with_risks"], b["risks"], b["entities"], b["units"]),
                         (len(controls), len({c for c, _ in mit}), len(risks), len(entities), len(units)))
        per_unit = defaultdict(set)
        for e, u in owns:
            per_unit[u].add(e)
        self.assertEqual({x["unit_id"]: x["entities"] for x in b["by_unit"]}, {u: len(es) for u, es in per_unit.items()})
        # the owner tie group is exactly the top tie in rounds.json's owner-concentration rows
        owner_rows = rounds()["supporting"][0]["rows"]
        top = [r[0] for r in owner_rows if (r[1], r[2]) == (owner_rows[0][1], owner_rows[0][2])]
        self.assertEqual([p["person_id"] for p in doc["owners"]["top"]], top)
        names = {p["person_id"]: p["name"] for p in read(out, "person")}
        self.assertEqual([p["name"] for p in doc["owners"]["top"]], [names[p] for p in top])
        print(f"\n[021 AC-1] subgraph {len(nodes)} nodes, {len(edges)} edges; blast radius {b['controls']} controls "
              f"({b['controls_with_risks']} with risks), {b['entities']} entities, {b['units']} units; owners {top}")

    def test_ac3_every_marked_figure_matches_its_source(self):
        _, _, page = built()
        sources = B.load_sources()
        self.assertGreater(len(page.marked), 20)
        for source, fmt, text in page.marked:
            with self.subTest(source=source):
                self.assertIn(fmt, FORMATTERS)
                self.assertEqual(text, FORMATTERS[fmt](B.resolve(source, sources)))
        # derived figures, recomputed here without calling derived.py
        r = rounds()
        counts = {"SQL": 0, "graph": 0, "close": 0}
        for x in r["rounds"]:
            counts[x["measured_verdict"]] += 1
        independent = {"derived:rounds_count": len(r["rounds"]),
                       **{f"derived:verdict_counts.{k}": v for k, v in counts.items()}}
        derived = {s: t for s, _, t in page.marked if s.startswith("derived:")}
        self.assertEqual(set(derived), set(independent))
        fmt_of = {s: f for s, f, _ in page.marked}
        for source, value in independent.items():
            self.assertEqual(derived[source], FORMATTERS[fmt_of[source]](value), source)
        # the copy says the answers are proved equal: every round's agreement check must be true
        self.assertTrue(all(x["checks"]["agreement"] is True for x in r["rounds"] + r["supporting"]))

    def test_ac3_formatters(self):
        self.assertEqual(plain(44), "44")
        self.assertEqual([count_word(n) for n in (1, 3, 7, 12, 13)], ["one", "three", "seven", "twelve", "13"])
        self.assertEqual([times_word(n) for n in (1, 2, 3)], ["once", "twice", "three times"])
        self.assertEqual([signed(x) for x in (4.75, -0.75, 0.0)], ["+4.75", "-0.75", "+0.00"])
        self.assertEqual(fraction([33, 33]), "33/33")
        self.assertEqual([rows_shown([20, 61]), rows_shown([14, 14])], ["20 of 61 rows", "14 rows"])
        self.assertEqual([names_and(["A"]), names_and(["A", "B"]), names_and(["A", "B", "C"])], ["A", "A and B", "A, B and C"])

    def test_ac4_no_typed_figures_and_js_carries_none(self):
        out, text, page = built()
        unmarked = norm(" ".join(page.unmarked))
        stray = [t for t in re.findall(r"\S*\d\S*", unmarked) if t.strip(".,;:()") not in ALLOWED_TOKENS]
        self.assertEqual(stray, [], "a digit outside a marked figure")
        self.assertEqual(NUMBER_WORDS.findall(unmarked), [], "a number word outside a marked figure")
        js = (B.HERE / "site.js").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"\d", js), "site.js holds a digit")
        for banned in ("fetch", "XMLHttpRequest", "import(", "innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
            self.assertNotIn(banned, js, banned)
        self.assertIsNone(re.search(r"(textContent|innerText)\s*=(?!=)", js), "site.js writes text into the page")
        embedded = [s for a, s in page.scripts if a.get("id") == "site-data"]
        self.assertEqual(len(embedded), 1)
        self.assertEqual(json.loads(embedded[0]), json.loads(X.SITE_JSON.read_text(encoding="utf-8"))["subgraph"])

    def test_ac5_required_statements_and_no_speed_claims(self):
        _, text, page = built()
        visible = norm(" ".join(page.visible))
        for segment in COPY:
            self.assertIn(norm(segment), visible, segment)
        self.assertIn('data-disclosure="synthetic"', text)
        self.assertIn('data-label="derived"', text)
        self.assertIn('data-statement="judgment"', text)
        self.assertIn('data-disclosure="no-speed-claims"', text)
        self.assertEqual(SPEED_WORDS.findall(norm(" ".join(page.speed_scope))), [], "speed language outside the disclosure")
        self.assertEqual(denied_in(visible, deny_entries()), [], "a real name on the page (INV-9)")

    def test_ac6_skeleton_pins_and_sections(self):
        out, text, page = built()
        self.assertIn('<meta name="viewport"', text)
        self.assertLessEqual({"top", "rounds", "operating-model", "appendix", "graph", "theme-toggle", "site-data"}, page.ids)
        external = [(t, a) for t, a in page.resources if (a.get("src") or a.get("href", "")).startswith(("http:", "https:", "//"))]
        self.assertEqual(len(external), 1, external)
        tag, attrs = external[0]
        self.assertEqual((tag, attrs["src"], attrs["integrity"], attrs["crossorigin"]), ("script", CDN, SRI, "anonymous"))
        css = (B.HERE / "site.css").read_text(encoding="utf-8")
        self.assertIn("prefers-color-scheme: dark", css)
        self.assertIn(':root[data-theme="dark"]', css)
        for name in ("index.html", "site.css", "site.js", "site.json", "rounds.json", "scores.json"):
            self.assertTrue((out / name).exists(), name)
        rows = [s for s, _, _ in page.marked if s.startswith("site.json:blast_radius.by_unit[")]
        self.assertEqual(len(rows), 2 * json.loads(X.SITE_JSON.read_text(encoding="utf-8"))["blast_radius"]["units"])

    def test_ac7_docs(self):
        readme = (B.HERE / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("TODO", readme)
        for phrase in ("python -m src.features.site.build", "python -m src.features.site.export", "data-source",
                       "data-format", "http.server", "no digit", "allow"):
            self.assertIn(phrase, readme, phrase)
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        self.assertIn("site.json", doc)
        self.assertIn("src/features/rounds/symmetry.py", doc)
        self.assertNotIn("is in `changes/020-verdict-rule-count-cypher-writes-once-as/plan.md`", doc)


if __name__ == "__main__":
    unittest.main()
