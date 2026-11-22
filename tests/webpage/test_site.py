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

# 022's approved copy: the fixed text of the rounds intro, the verdict rule, the operating model and the appendix.
COPY_022 = [
    "Each planning question was asked in SQL and in Cypher over the same facts. Each answer is checked: the SQL and "
    "Cypher answers must agree, an independent Python computation must agree, and where a scenario was planted, the "
    "answer must find it.", "The verdict compares how much query each language needs; it is not a measure of speed.",
    "sit within a point of the line, so a single extra clause would change their verdict.",
    "Each side scores clauses plus steps plus", "times its moving parts; the side whose score times",
    "is at most the other's wins, and otherwise the round is close. Moving parts follow a single rule on both sides, with",
    "disclosed exceptions; clauses and steps measure what each language writes.",
    "SQL gets the ERM and IA tables merged in a single place, in", "lines with", "unions, as the graph database gets them "
    "merged by its labels; the views are published as setup and never scored.",
    "Cypher needed less query in rounds", ": with the same number of stages on both sides, SQL needed more joins than "
    "Cypher needed hops, to fetch a name or to join a grouped result back. The languages came out close in rounds",
    ", where SQL's joins were no more than Cypher's hops, and in round", ", where Cypher needed an extra stage. SQL needed "
    "less query in round", ", the question of exposure through fourth parties, of unknown depth: asked on its own, the "
    "question was shorter in Cypher,", "but bringing the new register in cost the graph", "against SQL's",
    "because a new table had to become nodes and edges.",
    "When auditors explore rather than report, as in clicking through a blast radius; when the same entities are linked "
    "from many systems; when new relationship types keep arriving and the data is already in the graph; and at larger "
    "scale, which is the M2 benchmark's question.",
    "The measured rounds say: when the joins a question needs are no more than the hops, and when new data arrives as tables.",
    "Most audit and data teams already read SQL, which matters as much as query length.",
    "Reconcile first: a graph of unreconciled data only draws the confusion more vividly. Keep the graph an analysis layer "
    "over the system of record, not a replacement. Prove both stores hold the same facts on every load. Keep a human "
    "review queue for uncertain matches. Publish every answer with its checks.",
    "Re-run the mapping, clear the review queue, regenerate.", "Map it into both stores and extend the parity test.",
    "Retrain on the training bank and rescore.", "Write it in both languages with an oracle and an agreement test.",
    "This project's change log, closed epics:", "Each change was planned, critiqued, tested and reviewed.",
    "For a team with clean ERM and IA exports, expect the reconciliation to be most of the work and the graph the smaller part.",
    "entity files and", "relationship files are published; each entity with its rows at seed",
    "The bank is synthetic and seeded: seed", "rebuilds every file byte for byte. Its descriptions were written by an AI "
    "model ahead of time and committed, so the build never calls an API.",
    "Risks: merged precision", ", merged recall", "if a reviewer resolves the queue correctly. Controls:",
    "The review queue holds", "pairs; IA risks placed in the right ERM category:",
    "Every round's answer must agree between the engines, match an independent Python computation, and find its planted "
    "scenario where a scenario was planted. The full suite runs against a real graph database on every push:",
    "The data is synthetic, from a single generator and a single bank, with small samples. The matcher's thresholds are "
    "deliberately conservative, so most true matches wait in the review queue. The training bank comes from the same "
    "generator, so its weights know the generator's habits.", "No speed or scale claim is made.",
    "The graph informs auditor judgment; it does not score risk or set the plan.",
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
        self.labels = []              # data-label values of the open elements (022)
        self.labelled = defaultdict(list)   # label -> visible text inside elements carrying it

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag in ("script", "link", "img", "iframe") and (a.get("src") or (tag == "link" and a.get("href"))):
            self.resources.append((tag, a))
        if tag in ("script", "style"):
            self.skip += 1
            self.scripts.append([a, ""]) if tag == "script" else None
        flags = (tag in ("script", "style"), "data-source" in a, a.get("data-disclosure") == "no-speed-claims",
                 a.get("data-label"))
        if "data-source" in a:
            self.marked_depth += 1
            self.marked.append([a["data-source"], a.get("data-format", "plain"), ""])
        if flags[2]:
            self.disclosure_depth += 1
        if flags[3]:
            self.labels.append(flags[3])
        self.stack.append((tag, flags))

    def handle_endtag(self, tag):
        while self.stack:
            open_tag, (is_skip, is_marked, is_disclosure, label) = self.stack.pop()
            self.skip -= is_skip
            self.marked_depth -= is_marked
            self.disclosure_depth -= is_disclosure
            if label:
                self.labels.pop()
            if open_tag == tag:
                break

    def handle_data(self, data):
        if self.skip:
            if self.scripts and self.stack and self.stack[-1][0] == "script":
                self.scripts[-1][1] += data
            return
        self.visible.append(data)
        for label in set(self.labels):
            self.labelled[label].append(data)
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
        # derived figures, recomputed here without calling derived.py (extended in 022)
        r = rounds()
        counts = {"SQL": 0, "graph": 0, "close": 0}
        for x in r["rounds"]:
            counts[x["measured_verdict"]] += 1
        mp = lambda x, side: x["metrics"][side]["moving_parts"]
        st = lambda x, side: x["metrics"][side]["steps"]
        site = json.loads(X.SITE_JSON.read_text(encoding="utf-8"))
        independent = {"derived:rounds_count": len(r["rounds"]),
                       **{f"derived:verdict_counts.{k}": v for k, v in counts.items()},
                       "derived:near_the_line": [x["number"] for x in r["rounds"] if abs(x["margin"]) <= 1],
                       "derived:disclosed_count": sum(1 for row in site["symmetry"] if row["disclosed"]),
                       "derived:graph_rule": [x["number"] for x in r["rounds"] if mp(x, "sql") == mp(x, "cypher") and st(x, "sql") > st(x, "cypher")],
                       "derived:close_steps": [x["number"] for x in r["rounds"] if x["measured_verdict"] == "close" and st(x, "sql") <= st(x, "cypher")],
                       "derived:close_moving": [x["number"] for x in r["rounds"] if x["measured_verdict"] == "close" and mp(x, "cypher") > mp(x, "sql")],
                       "derived:rounds_by_verdict.SQL": [x["number"] for x in r["rounds"] if x["measured_verdict"] == "SQL"],
                       **{f"derived:shown_rows.{x['number']}": [min(5, len(x["rows"])), x["row_count"]]
                          for x in r["rounds"] + r["supporting"]}}
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
        self.assertEqual(names_and([1, 6, 7]), "1, 6 and 7")
        # 022's formatters
        self.assertEqual([FORMATTERS["verdict"](v) for v in ("graph", None)], ["graph", "none (supporting query)"])
        self.assertEqual([FORMATTERS["check"](v) for v in (True, False, "not run")], ["passed", "failed", "not run"])
        self.assertEqual(FORMATTERS["scenario"](None), "none planted")
        self.assertEqual(FORMATTERS["scenario"]({"planted": "shared_system", "rule": "equal", "verified_by": "t"}),
                         "shared_system (equal)")
        self.assertEqual(FORMATTERS["triple"]([5, 1, 1]), "5 / 1 / 1")

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

    # ---------------- 022: rounds, operating model and appendix ----------------

    def test_ac1_022_rounds_section(self):
        _, text, page = built()
        r = rounds()
        sources = {s for s, _, _ in page.marked}
        articles = dict(re.findall(r'<article class="round" id="round-([^"]+)">(.*?)</article>', text, re.S))
        entries = [(f"rounds.json:rounds[{i}]", x) for i, x in enumerate(r["rounds"])]
        entries += [(f"rounds.json:supporting[{i}]", x) for i, x in enumerate(r["supporting"])]
        self.assertEqual(set(articles), {str(x["number"]) for _, x in entries})
        for base, x in entries:
            with self.subTest(round=x["number"]):
                body = articles[str(x["number"])]
                for field in ("question", "sql", "cypher", "scores.sql", "scores.cypher", "margin", "measured_verdict",
                              "expected_verdict", "checks.agreement", "checks.oracle"):
                    self.assertIn(f"{base}.{field}", sources, field)
                for j, _ in enumerate(x["columns"]):
                    self.assertIn(f"{base}.columns[{j}]", sources)          # headers are marked (l1_node_id holds a digit)
                for i in range(min(5, len(x["rows"]))):
                    self.assertIn(f"{base}.rows[{i}][0]", sources)
                self.assertNotIn(f"{base}.rows[5][0]", sources)
                differs = x["expected_verdict"] is not None and x["expected_verdict"] != x["measured_verdict"]
                self.assertEqual("differs from expected" in body, differs)
                self.assertEqual('href="rounds.json"' in body, len(x["rows"]) < x["row_count"])
                if x["supporting"]:
                    self.assertIn("derived (supporting query)", body)
                    self.assertIn("none (supporting query)", body)
                else:
                    self.assertIn(f"{base}.checks.scenario", sources)
                    if x["checks"]["scenario"] is None:
                        self.assertIn("none planted", body)
                if x.get("top_riser"):
                    self.assertIn(f"{base}.top_riser.l1_name", sources)
        self.assertEqual({str(x["number"]) for _, x in entries if len(x["rows"]) < x["row_count"]}, {"1", "2", "4", "7"})

    def test_ac2_022_verdict_rule_and_symmetry(self):
        _, text, page = built()
        sources = {s for s, _, _ in page.marked}
        r, site = rounds(), json.loads(X.SITE_JSON.read_text(encoding="utf-8"))
        for i, _ in enumerate(r["verdict_rule"]["counting"]):
            self.assertIn(f"rounds.json:verdict_rule.counting[{i}]", sources)
        for i, row in enumerate(site["symmetry"]):
            for field in ("construct", "sql", "cypher", "sql_metrics", "cypher_metrics"):
                self.assertIn(f"site.json:symmetry[{i}].{field}", sources)
        disclosed_tags = re.findall(r'<th scope="row">.*?</th>', text.split('class="data symmetry"')[1].split("</table>")[0], re.S)
        self.assertEqual(sum('class="tag">disclosed<' in t for t in disclosed_tags), sum(row["disclosed"] for row in site["symmetry"]))
        for field in ("rounds.json:views.sql", "rounds.json:views.lines", "rounds.json:views.unions",
                      "rounds.json:verdict_rule.weight", "rounds.json:verdict_rule.margin", "derived:disclosed_count"):
            self.assertIn(field, sources)

    def test_ac3_022_operating_model(self):
        _, _, page = built()
        r = rounds()
        mp = lambda x, side: x["metrics"][side]["moving_parts"]
        st = lambda x, side: x["metrics"][side]["steps"]
        by = defaultdict(set)
        for x in r["rounds"]:
            by[x["measured_verdict"]].add(x["number"])
        # the measured explanations cover exactly the measured sets
        self.assertEqual({x["number"] for x in r["rounds"] if mp(x, "sql") == mp(x, "cypher") and st(x, "sql") > st(x, "cypher")},
                         by["graph"], "the graph-win rule picks out exactly the graph rounds")
        close_steps = {x["number"] for x in r["rounds"] if x["number"] in by["close"] and st(x, "sql") <= st(x, "cypher")}
        close_moving = {x["number"] for x in r["rounds"] if x["number"] in by["close"] and mp(x, "cypher") > mp(x, "sql")}
        self.assertEqual(close_steps | close_moving, by["close"], "every close round is explained")
        # round 5's split: parts add up to the published metrics, and the split reverses the verdict
        from src.features.rounds import verdict as V
        from src.features.rounds.registry import ALL
        five = next(x for x in ALL if x.number == 5)
        sc = lambda t, e: V.score(V.metrics(t, e))
        split = json.loads(X.SITE_JSON.read_text(encoding="utf-8"))["round5_split"]
        self.assertEqual(split, {"query": {"sql": sc(five.sql, "sql"), "cypher": sc(five.cypher, "cypher")},
                                 "setup": {"sql": sc(five.sql_setup, "sql"), "cypher": sc(five.cypher_setup, "cypher")}})
        five_r = next(x for x in r["rounds"] if x["number"] == 5)
        self.assertEqual(V.score(V.metrics(five.scored("sql"), "sql")), five_r["scores"]["sql"])
        self.assertEqual(V.score(V.metrics(five.scored("cypher"), "cypher")), five_r["scores"]["cypher"])
        self.assertLess(split["query"]["cypher"], split["query"]["sql"], "asked on its own, round 5 is shorter in Cypher")
        self.assertGreater(five_r["scores"]["cypher"], five_r["scores"]["sql"], "with its setup, SQL wins round 5")
        # every unmeasured claim sits in an expected element; the practice paragraphs are labelled
        expected = norm(" ".join(page.labelled["expected-not-measured"]))
        for claim in ("explore rather than report", "linked from many systems", "new relationship types keep arriving",
                      "larger scale", "already read SQL", "most of the work"):
            self.assertIn(claim, expected, claim)
        self.assertEqual(expected.count("expected, not measured in M1"), 3)
        practice = norm(" ".join(page.labelled["practice"]))
        for claim in ("Reconcile first", "Re-run the mapping", "extend the parity test", "Retrain on the training bank"):
            self.assertIn(claim, practice, claim)
        measured = norm(" ".join(page.labelled["measured"]))
        self.assertNotIn("expected", measured)
        for phrase in COPY_022:
            self.assertIn(norm(phrase), norm(" ".join(page.visible)), phrase)
        # 'each change was planned, critiqued, tested and reviewed': every counted change has both files
        for epic in json.loads(X.SITE_JSON.read_text(encoding="utf-8"))["project"]:
            children = [p.parent for p in (ROOT / "changes").glob("*/plan.md") if X.plan_json(p).get("epic") == epic["epic"]]
            self.assertEqual(len(children), epic["changes"])
            for child in children:
                self.assertTrue((child / "critique.md").exists() and (child / "review.md").exists(), child.name)

    def test_ac4_022_appendix(self):
        _, text, page = built()
        sources = {s for s, _, _ in page.marked}
        site = json.loads(X.SITE_JSON.read_text(encoding="utf-8"))
        for i, _ in enumerate(site["inventory"]["entities"]):
            self.assertIn(f"site.json:inventory.entities[{i}].rows", sources)
        for field in ("risk.precision.count", "risk.recall.count", "risk.recall_if_resolved.count", "control.precision.count",
                      "control.recall.count", "control.recall_if_resolved.count", "review_queue.total", "placement.all.count"):
            self.assertIn(f"scores.json:{field}", sources, field)
        caveats = json.loads(B.SCORES.read_text(encoding="utf-8"))["caveats"]
        self.assertEqual({s for s in sources if s.startswith("scores.json:caveats.")}, {f"scores.json:caveats.{k}" for k in caveats})
        self.assertIn('href="https://github.com/neifertg/audit-knowledge-graph/actions"', text)
        self.assertIn("rounds.json:seed", sources)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        reproduce = text.split("<h3>Reproduce</h3>")[1].split("</code>")[0].split("<code>")[1]
        for command in reproduce.splitlines():
            self.assertIn(command.strip(), readme, command)

    def test_ac5_022_story_inventory_and_project_oracle(self):
        out, _ = loaded()
        site = json.loads(X.SITE_JSON.read_text(encoding="utf-8"))
        # repeat finding: IA controls whose issues were opened in two or more calendar years
        issue = {i["issue_id"]: i for i in read(out, "issue")}
        years, issues = defaultdict(set), defaultdict(set)
        for row in read(out, "issue_against_control_ia"):
            years[row["control_id"]].add(issue[row["issue_id"]]["opened_date"][:4])
            issues[row["control_id"]].add(row["issue_id"])
        repeat = [c for c, ys in years.items() if len(ys) >= 2]
        self.assertEqual(site["repeat_finding"], {"controls": len(repeat), "issues": sum(len(issues[c]) for c in repeat)})
        # owner concentration: the top tie group's key controls and the units they reach
        both = lambda stem: read(out, stem + "_erm") + read(out, stem + "_ia")
        key = {c["control_id"] for c in both("control") if c["key_control"] == "Y"}
        owned = defaultdict(set)
        for row in both("control_owned_by_person"):
            if row["control_id"] in key:
                owned[row["person_id"]].add(row["control_id"])
        mit, exp = defaultdict(set), defaultdict(set)
        for row in both("control_mitigates_risk"):
            mit[row["control_id"]].add(row["risk_id"])
        for row in both("auditable_entity_exposed_to_risk"):
            exp[row["risk_id"]].add(row["auditable_entity_id"])
        unit_of = {row["auditable_entity_id"]: row["business_unit_id"] for row in read(out, "business_unit_owns_auditable_entity")}
        for person in site["owners"]["top"]:
            cs = owned[person["person_id"]]
            units = {unit_of[e] for c in cs for rk in mit[c] for e in exp[rk]}
            self.assertEqual((len(cs), len(units)), (site["owners"]["key_controls"], site["owners"]["units"]))
        # inventory: the 15 named entity files, each counted from its CSV; relationship files from the dictionary
        from tests.generator.dictionary import parse
        names = ["audit", "auditable_entity", "business_unit", "control_erm", "control_ia", "issue", "person", "process",
                 "regulation", "risk_erm", "risk_ia", "segment", "system", "taxonomy_node_erm", "taxonomy_node_ia"]
        inv = site["inventory"]
        self.assertEqual([e["file"] for e in inv["entities"]], names)
        for e in inv["entities"]:
            self.assertEqual(e["rows"], len(read(out, e["file"])), e["file"])
        published = [f for f in parse() if not f.startswith("answer_key")]
        self.assertEqual((inv["entity_files"], inv["relationship_files"]), (len(names), len(published) - len(names)))
        # project: closed epics from changes/*/epic.md, children counted by their plan's epic field
        closed = []
        for epic_md in sorted((ROOT / "changes").glob("*/epic.md")):
            meta = json.loads(epic_md.read_text(encoding="utf-8").split("```json plan", 1)[1].split("```", 1)[0])
            if meta["status"] == "done":
                count = 0
                for plan in (ROOT / "changes").glob("*/plan.md"):
                    pm = json.loads(plan.read_text(encoding="utf-8").split("```json plan", 1)[1].split("```", 1)[0])
                    count += pm.get("epic") == meta["id"]
                closed.append((meta["id"], count))
        self.assertEqual([(e["epic"], e["changes"]) for e in site["project"]], closed)

    # ---------------- 023: 022's parked findings, each a named test (L-023) ----------------

    def test_ac1_023_round5_split_adds_up(self):
        split = json.loads(X.SITE_JSON.read_text(encoding="utf-8"))["round5_split"]
        five = next(x for x in rounds()["rounds"] if x["number"] == 5)
        for side in ("sql", "cypher"):
            self.assertEqual(split["query"][side] + split["setup"][side], five["scores"][side], side)

    def test_ac1_023_owner_scenario_through_formatter(self):
        _, text, page = built()
        body = text.split('id="round-owners"')[1].split("</article>")[0]
        self.assertIn('data-source="rounds.json:supporting[0].checks.scenario" data-format="scenario_supporting"', body)
        marked = {s: t for s, f, t in page.marked if s == "rounds.json:supporting[0].checks.scenario"}
        self.assertEqual(marked, {"rounds.json:supporting[0].checks.scenario": "derived (supporting query)"})
        self.assertEqual(FORMATTERS["scenario_supporting"](None), "derived (supporting query)")

    def test_ac1_023_project_titles(self):
        for epic in json.loads(X.SITE_JSON.read_text(encoding="utf-8"))["project"]:
            epic_md = ROOT / "changes" / epic["epic"] / "epic.md"
            heading = epic_md.read_text(encoding="utf-8").splitlines()[0]
            self.assertTrue(heading.startswith("# "), epic["epic"])
            self.assertEqual(epic["title"], heading[2:].strip())

    def test_ac1_023_each_close_rule_nonempty(self):
        r = rounds()
        mp = lambda x, side: x["metrics"][side]["moving_parts"]
        st = lambda x, side: x["metrics"][side]["steps"]
        close = [x for x in r["rounds"] if x["measured_verdict"] == "close"]
        self.assertTrue([x for x in close if st(x, "sql") <= st(x, "cypher")], "SQL steps no more than Cypher's")
        self.assertTrue([x for x in close if mp(x, "cypher") > mp(x, "sql")], "Cypher needs more moving parts")

    def test_ac7_docs(self):
        readme = (B.HERE / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("TODO", readme)
        for phrase in ("python -m src.features.site.build", "python -m src.features.site.export", "data-source",
                       "data-format", "http.server", "no digit", "allow"):
            self.assertIn(phrase, readme, phrase)
        for phrase in ("#rounds", "#operating-model", "#appendix", "expected-not-measured", "practice",
                       "measured results"):   # 022
            self.assertIn(phrase, readme, phrase)
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        self.assertIn("site.json", doc)
        for phrase in ("inventory", "project", "round5_split"):   # 022
            self.assertIn(phrase, doc, phrase)
        self.assertIn("src/features/rounds/symmetry.py", doc)
        self.assertNotIn("is in `changes/020-verdict-rule-count-cypher-writes-once-as/plan.md`", doc)


if __name__ == "__main__":
    unittest.main()
