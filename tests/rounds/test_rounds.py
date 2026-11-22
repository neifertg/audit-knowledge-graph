"""E3 child c (017): rounds 1-4, paired SQL and Cypher, with agreement, oracle and scenario checks.

Neo4j parts skip without NEO4J_URI and fail instead when AKG_REQUIRE_NEO4J=1. Run them locally with
    .venv\\Scripts\\python -m src.features.stores.with_neo4j -m unittest tests.rounds.test_rounds
"""
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from src.features.rounds import ROUNDS
from src.features.rounds import runner as R
from src.features.rounds import verdict as V
from src.features.rounds.registry import STALE_CUTOFF, VIEWS
from src.features.stores.neo4j_store import load_complete, reconciled_checksum
from src.features.stores.sqlite_store import DATABASE

from tests.generator.helpers import ROOT, akg_env, answer_key, read, run_akg
from tests.stores.test_neo4j import graph
from tests.stores.test_sqlite import loaded

BY_NUMBER = {r.number: r for r in ROUNDS}


# ---------- the oracle: an independent Python computation from the CSVs ----------

def oracle(out: Path, cutoff: str = STALE_CUTOFF) -> dict:
    """Each round's answer computed from the published and reconciled CSVs, never from SQLite."""
    both = lambda stem: read(out, stem + "_erm") + read(out, stem + "_ia")
    exposed, mitigates, mitigated_by = defaultdict(set), defaultdict(set), defaultdict(set)
    for r in both("auditable_entity_exposed_to_risk"):
        exposed[r["risk_id"]].add(r["auditable_entity_id"])
    for r in both("control_mitigates_risk"):
        mitigates[r["control_id"]].add(r["risk_id"])
        mitigated_by[r["risk_id"]].add(r["control_id"])
    owner = {r["auditable_entity_id"]: r["business_unit_id"] for r in read(out, "business_unit_owns_auditable_entity")}
    unit_name = {r["business_unit_id"]: r["name"] for r in read(out, "business_unit")}

    # round 1
    issue_risks = defaultdict(set)
    for r in both("issue_against_risk"):
        issue_risks[r["issue_id"]].add(r["risk_id"])
    open_by = defaultdict(set)
    for i in read(out, "issue"):
        if i["closed_date"] == "":
            for risk in issue_risks[i["issue_id"]]:
                for e in exposed[risk]:
                    open_by[(owner[e], i["rating"])].add(i["issue_id"])
    r1 = [(bu, unit_name[bu], rating, len(ids)) for (bu, rating), ids in open_by.items()]

    # round 2
    rating = {r["risk_id"]: r["inherent_rating"] for r in both("risk")}
    end = {a["audit_id"]: a["end_date"] for a in read(out, "audit")}
    fresh = {t["control_id"] for t in read(out, "audit_tested_control_ia") if end[t["audit_id"]] >= cutoff}
    members = defaultdict(list)
    for m in read(out / "reconciled", "risk_maps_to_canonical"):
        members[m["canonical_risk_id"]].append((m["source"], m["risk_id"]))
    r2 = [(c, "Y" if any(s == "IA" for s, _ in mem) else "N") for c, mem in members.items()
          if any(rating[r] == "High" for _, r in mem)
          and not any(ctrl in fresh for _, r in mem for ctrl in mitigated_by[r])]

    # round 3
    system_name = {s["system_id"]: s["name"] for s in read(out, "system")}
    reach = defaultdict(set)
    for d in both("control_depends_on_system"):
        for risk in mitigates[d["control_id"]]:
            reach[d["system_id"]] |= exposed[risk]
    ranked = sorted(((s, system_name[s], len(es)) for s, es in reach.items() if es), key=lambda t: (-t[2], t[1]))

    # round 4
    paths = Counter()
    for q in both("regulation_requires_control"):
        for risk in mitigates[q["control_id"]]:
            for e in exposed[risk]:
                paths[(q["regulation_id"], owner[e])] += 1
    r4 = [(g, bu, n) for (g, bu), n in paths.items()]
    return {1: r1, 2: r2, 3: ranked[:3], 4: r4, "ranked_systems": ranked, "members": members,
            "mitigated_by": mitigated_by, "rating": rating}


def latest_fresh_test(out: Path, orc: dict) -> tuple[str, str]:
    """(a High canonical risk that is fresh at the default cutoff, D = the latest end date of an audit
    that tested one of its members' controls)."""
    end = {a["audit_id"]: a["end_date"] for a in read(out, "audit")}
    tested = defaultdict(list)
    for t in read(out, "audit_tested_control_ia"):
        tested[t["control_id"]].append(end[t["audit_id"]])
    stale = {c for c, _ in orc[2]}
    for c in sorted(orc["members"]):
        mem = orc["members"][c]
        if c in stale or not any(orc["rating"][r] == "High" for _, r in mem):
            continue
        return c, max(d for _, r in mem for ctrl in orc["mitigated_by"][r] for d in tested[ctrl])
    raise AssertionError("no fresh High canonical risk at seed 42")


def sqlite_rounds(out: Path, **params) -> dict:
    con = R.sqlite_connection(out)
    try:
        return {r.number: R.run_sqlite(r, con, **({k: v for k, v in params.items() if k in r.params})) for r in ROUNDS}
    finally:
        con.close()


def same(rnd, a, b) -> bool:
    return R.comparable(rnd, R.normalise(a)) == R.comparable(rnd, R.normalise(b))


def copy_build(out: Path, tmp: str) -> Path:
    dest = Path(tmp) / "copy"
    shutil.copytree(out, dest, ignore=shutil.ignore_patterns("answer_key"))
    return dest


class RoundTests(unittest.TestCase):
    maxDiff = None

    def test_ac1_registry_files_and_query_style(self):
        self.assertEqual([r.number for r in ROUNDS], [1, 2, 3, 4])
        self.assertEqual({r.number: r.expected for r in ROUNDS}, {1: "SQL", 2: "close", 3: "graph", 4: "graph"})
        files = [VIEWS]
        for r in ROUNDS:
            self.assertTrue(r.sql_path.exists() and r.cypher_path.exists(), r.number)
            files += [r.sql_path, r.cypher_path]
            for column in r.columns:
                self.assertIn(column, r.sql, (r.number, column))
                self.assertIn(column, r.cypher, (r.number, column))
            # no per-source table in a round's SQL, except the IA-only audit_tested_control_ia
            self.assertEqual(set(re.findall(r"\b\w+_(?:erm|ia)\b", r.sql)) - {"audit_tested_control_ia"}, set(),
                             r.number)
        # round 2's cutoff is a parameter in both engines, never a literal
        self.assertIn(":cutoff", BY_NUMBER[2].sql)
        self.assertIn("$cutoff", BY_NUMBER[2].cypher)
        self.assertNotIn(STALE_CUTOFF, BY_NUMBER[2].sql + BY_NUMBER[2].cypher)
        for path in files:
            engine = "sql" if path.suffix == ".sql" else "cypher"
            text = path.read_text(encoding="utf-8")
            marker = V.COMMENT[engine]
            for n, line in enumerate(text.splitlines(), 1):
                self.assertLessEqual(len(line), 100, f"{path.name}:{n} is over 100 characters")
                code = re.sub(r"'[^']*'", "''", line)
                if marker in code:
                    self.assertTrue(line.strip().startswith(marker), f"{path.name}:{n}: comment after code")
            per_line = V.clauses_per_line(text, engine)
            self.assertLessEqual(max(per_line), 1, f"{path.name}: a line holds two clause keywords")
            if engine == "sql":
                self.assertIsNone(re.search(r"\bFROM\s+\w+(?:\s+AS\s+\w+)?\s*,", text, re.I), f"{path.name}: comma join")
        # multi-word tokens and expression keywords, one pure case each
        self.assertEqual(V.clauses_per_line("OPTIONAL MATCH (a)", "cypher"), [1])
        self.assertEqual(V.clauses_per_line("WITH RECURSIVE t(n) AS (", "sql"), [1])
        self.assertEqual(V.clauses_per_line("LEFT JOIN b ON b.id = a.id", "sql"), [1])
        self.assertEqual(V.clauses_per_line("WHERE a.name STARTS WITH 'x' AND a.code ENDS WITH 'y'", "cypher"), [1])
        self.assertEqual(V.clauses_per_line("WHERE any(m IN ms WHERE m.r = 'High')", "cypher"), [1])
        self.assertEqual(V.clauses_per_line("UNION ALL", "sql"), [1])
        self.assertEqual(V.clauses_per_line("SELECT a FROM t", "sql"), [2])

    def test_ac2_measured_verdict_rule(self):
        m = lambda text, engine: V.metrics(text, engine)
        cte = ("WITH x AS (\n  SELECT a.id\n  FROM a\n  JOIN b ON b.id = a.id)\n"
               "SELECT x.id\nFROM x\nJOIN c ON c.id = x.id\nWHERE c.v = 'JOIN FROM'")
        inline = ("SELECT x.id\nFROM (\n  SELECT a.id\n  FROM a\n  JOIN b ON b.id = a.id) AS x\n"
                  "JOIN c ON c.id = x.id\nWHERE c.v = 'JOIN FROM'")
        self.assertEqual(m(cte, "sql"), {"clauses": 8, "steps": 3, "moving_parts": 1})
        self.assertEqual(m(inline, "sql"), {"clauses": 7, "steps": 3, "moving_parts": 1})
        subquery = "SELECT a.id\nFROM a\nWHERE a.id IN (\n  SELECT b.id\n  FROM b)"
        self.assertEqual(m(subquery, "sql"), {"clauses": 5, "steps": 1, "moving_parts": 1})
        correlated = "SELECT a.id\nFROM a\nWHERE EXISTS (\n  SELECT 1\n  FROM b\n  WHERE b.id = a.id)"
        self.assertEqual(m(correlated, "sql"), {"clauses": 6, "steps": 1, "moving_parts": 1})
        union = "SELECT id\nFROM a\nUNION ALL\nSELECT id\nFROM b"
        self.assertEqual(m(union, "sql"), {"clauses": 5, "steps": 1, "moving_parts": 1})
        recursive = ("WITH RECURSIVE t(n) AS (\n  SELECT 1\n  UNION ALL\n  SELECT n + 1\n  FROM t\n  WHERE n < 5)\n"
                     "SELECT n\nFROM t")
        self.assertEqual(m(recursive, "sql"), {"clauses": 8, "steps": 1, "moving_parts": 3})
        ddl = "CREATE TEMP TABLE z AS\nSELECT id\nFROM a"
        self.assertEqual(m(ddl, "sql"), {"clauses": 2, "steps": 0, "moving_parts": 1})
        arrows = "MATCH (a:A)-->(b:B)<--(c)\nMATCH (c)--(d)\nRETURN a.id"
        self.assertEqual(m(arrows, "cypher"), {"clauses": 3, "steps": 3, "moving_parts": 0})
        exists = ("MATCH (a:A)-[:R]->(b:B)\nWITH a, count(b) AS n\nWHERE n > 1 AND EXISTS {\n"
                  "  MATCH (a)<-[:S]-(c:C)\n  WHERE c.x STARTS WITH 'WITH' }\nRETURN a.id, n")
        self.assertEqual(m(exists, "cypher"), {"clauses": 6, "steps": 2, "moving_parts": 2})
        call = "UNWIND $rows AS row\nCALL {\n  WITH row\n  MERGE (v:V {id: row.id})\n  SET v.x = row.x }\nRETURN count(*) AS n"
        self.assertEqual(m(call, "cypher"), {"clauses": 6, "steps": 0, "moving_parts": 4})
        cy_union = "MATCH (a:A)\nRETURN a.id AS id\nUNION\nMATCH (b:B)\nRETURN b.id AS id"
        self.assertEqual(m(cy_union, "cypher"), {"clauses": 5, "steps": 0, "moving_parts": 1})
        self.assertEqual(m("MATCH (a)\nWHERE any(x IN a.l WHERE x > 1)\nRETURN a", "cypher")["clauses"], 3)
        # layout cannot move a score: the same queries re-wrapped
        self.assertEqual(m(exists.replace("<-[:S]-", "\n    <-[:S]-").replace("a.id, n", "a.id,\n  n"), "cypher"),
                         m(exists, "cypher"))
        self.assertEqual(m(cte.replace("JOIN c ON", "JOIN c\n  ON"), "sql"), m(cte, "sql"))
        for r in ROUNDS:
            self.assertEqual(V.metrics(r.cypher.replace("<-[", "\n  <-["), "cypher"), V.metrics(r.cypher, "cypher"))
        # the rule and its boundaries (score = clauses + steps + 5 * moving_parts; margin 1.25)
        s = lambda n: {"clauses": n, "steps": 0, "moving_parts": 0}
        self.assertEqual(V.score({"clauses": 2, "steps": 3, "moving_parts": 1}), 10)
        self.assertEqual(V.measured(s(8), s(10)), "SQL")      # 8 * 1.25 = 10, exactly on the boundary
        self.assertEqual(V.measured(s(8), s(9)), "close")
        self.assertEqual(V.measured(s(10), s(8)), "graph")    # on the boundary the other way
        self.assertEqual(V.measured(s(9), s(8)), "close")
        self.assertEqual(V.measured(s(7), s(7)), "close")
        # a two-source UNION ALL against the shared view: the view saves 5 clauses, 2 steps, 2 moving parts
        view = "SELECT m.risk_id\nFROM mitigates AS m\nJOIN risk AS r ON r.risk_id = m.risk_id"
        unioned = ("SELECT m.risk_id\nFROM (\n  SELECT risk_id\n  FROM control_mitigates_risk_erm\n  UNION ALL\n"
                   "  SELECT risk_id\n  FROM control_mitigates_risk_ia) AS m\nJOIN risk AS r ON r.risk_id = m.risk_id")
        self.assertEqual(m(view, "sql"), {"clauses": 3, "steps": 1, "moving_parts": 0})
        self.assertEqual(m(unioned, "sql"), {"clauses": 8, "steps": 3, "moving_parts": 2})
        # views.sql is never scored: a round's metrics come from its own file alone
        for r in ROUNDS:
            self.assertNotIn("CREATE", r.sql.upper())

    def test_ac3_sqlite_answers_match_oracle_and_scenarios(self):
        out, _ = loaded()
        got, orc = sqlite_rounds(out), oracle(out)
        con = R.sqlite_connection(out)
        try:
            for r in ROUNDS:
                with self.subTest(round=r.number):
                    self.assertTrue(same(r, got[r.number], orc[r.number]), f"round {r.number} differs from the oracle")
                    cursor = con.execute(r.sql, r.params)
                    self.assertEqual(tuple(d[0] for d in cursor.description), r.columns)
        finally:
            con.close()
        scenarios = defaultdict(set)
        for row in answer_key(out, "scenarios"):
            scenarios[row["scenario"]].add(row["item_id"])
        # round 3: exactly the planted shared systems, and the third beats the fourth outright
        self.assertEqual({row[0] for row in got[3]}, scenarios["shared_system"])
        ranked = orc["ranked_systems"]
        self.assertGreater(ranked[2][2], ranked[3][2])
        # round 2: contains every untested High IA risk's canonical risk
        canon = {m["risk_id"]: m["canonical_risk_id"] for m in read(out / "reconciled", "risk_maps_to_canonical")}
        answer2 = {c for c, _ in got[2]}
        self.assertTrue(scenarios["untested_high_risk"])
        self.assertLessEqual({canon[r] for r in scenarios["untested_high_risk"]}, answer2)
        # round 4: every regulation reaches a business unit
        self.assertEqual({g for g, _, _ in got[4]}, {g["regulation_id"] for g in read(out, "regulation")})
        # not "everything": each answer is a strict subset of what it could be
        self.assertLess(len(answer2), len(orc["members"]))
        self.assertLess(sum(1 for _ in got[3]), len(read(out, "system")))
        # round 2's inclusive boundary, on real data: fresh at cutoff D, stale at D + 1 day
        c, d = latest_fresh_test(out, orc)
        after = (date.fromisoformat(d) + timedelta(days=1)).isoformat()
        at_d, at_after = sqlite_rounds(out, cutoff=d)[2], sqlite_rounds(out, cutoff=after)[2]
        self.assertNotIn(c, {x for x, _ in at_d})
        self.assertIn(c, {x for x, _ in at_after})
        self.assertTrue(same(BY_NUMBER[2], at_d, oracle(out, d)[2]))
        self.assertTrue(same(BY_NUMBER[2], at_after, oracle(out, after)[2]))
        print(f"\n[017 AC-3] seed 42: round 1 {len(got[1])} rows; round 2 {len(answer2)} rows "
              f"({sum(f == 'N' for _, f in got[2])} without an IA member); round 3 {got[3]} (4th {ranked[3][2]}); "
              f"round 4 {len(got[4])} pairs, {sum(n for *_, n in got[4])} paths; boundary {c} at {d}")

    def test_ac4_sql_and_cypher_agree_and_the_guard_refuses(self):
        driver, out = graph()
        results = R.run_rounds(out, driver)
        for res in results:
            with self.subTest(round=res.round.number):
                self.assertTrue(res.agree, f"round {res.round.number}: SQL and Cypher differ")
                records = driver.execute_query(res.round.cypher, res.round.params)
                self.assertEqual(tuple(records.keys), res.round.columns)
        # round 2 agrees at the boundary cutoffs too, so a '>' in the Cypher fails
        c, d = latest_fresh_test(out, oracle(out))
        after = (date.fromisoformat(d) + timedelta(days=1)).isoformat()
        con = R.sqlite_connection(out)
        try:
            for cutoff in (d, after):
                self.assertTrue(same(BY_NUMBER[2], R.run_sqlite(BY_NUMBER[2], con, cutoff=cutoff),
                                     R.run_neo4j(BY_NUMBER[2], driver, cutoff=cutoff)), cutoff)
        finally:
            con.close()
        # the guard refuses a build whose reconciled checksum differs, and leaves the graph untouched
        before = load_complete(driver)
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_build(out, tmp)
            target = sorted((copy / "reconciled").glob("*.csv"))[0]
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaises(R.RoundsError) as caught:
                R.run_rounds(copy, driver)
            self.assertIn("checksum", str(caught.exception))
            result = run_akg("rounds", "--out", str(copy), check=False, neo4j=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("checksum", result.stderr)
            self.assertNotIn("not run", result.stdout)
        self.assertEqual(load_complete(driver), before)

    def test_ac5_cli_exit_codes_and_build_step(self):
        out, _ = loaded()
        # SQLite only: every round printed, Neo4j not run, exit 0
        result = run_akg("rounds", "--out", str(out))
        self.assertEqual(result.returncode, 0)
        for r in ROUNDS:
            self.assertRegex(result.stdout, rf"round {r.number}: SQLite \d+ rows; Neo4j: not run; measured verdict "
                                            rf"(SQL|close|graph)")
        # a missing database: exit 1, saying to run akg load
        with tempfile.TemporaryDirectory() as tmp:
            result = run_akg("rounds", "--out", tmp, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("akg load", result.stderr)
        # Neo4j configured but unreachable: exit 1 naming NEO4J_URI, never "not run" (no server needed)
        env = {**akg_env(), "NEO4J_URI": "bolt://127.0.0.1:1", "NEO4J_USER": "neo4j", "NEO4J_PASSWORD": "x"}
        result = subprocess.run([sys.executable, "-m", "akg", "rounds", "--out", str(out)], cwd=ROOT,
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("NEO4J_URI", result.stderr)
        self.assertNotIn("not run", result.stdout)
        # the build step: rounds follow the load (one sample build; the sample answers may be small)
        with tempfile.TemporaryDirectory() as tmp:
            result = run_akg("build", "--size", "sample", "--out", tmp)
            lines = result.stdout.splitlines()
            load_at = next(i for i, line in enumerate(lines) if line.startswith("loaded "))
            self.assertEqual([line.split(":")[0] for line in lines if line.startswith("round ")],
                             [f"round {r.number}" for r in ROUNDS])
            self.assertTrue(all(i > load_at for i, line in enumerate(lines) if line.startswith("round ")))
        # disagreement, for real: close one open issue in a copy's SQLite; the graph is unchanged
        driver, out = graph()
        open_issue = next(i["issue_id"] for i in read(out, "issue") if i["closed_date"] == "")
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_build(out, tmp)
            con = sqlite3.connect(copy / DATABASE)
            try:
                with con:  # commits; closing is separate, and Windows cannot delete an open file
                    con.execute("UPDATE issue SET closed_date = '2025-12-31' WHERE issue_id = ?", (open_issue,))
            finally:
                con.close()
            result = run_akg("rounds", "--out", str(copy), check=False, neo4j=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("round(s) 1", result.stderr)
            self.assertIn("round 1: SQLite", result.stdout)
            self.assertIn("DISAGREE", result.stdout)
        self.assertEqual(load_complete(driver), reconciled_checksum(out), "the shared graph stays valid")

    def test_ac6_docs_describe_the_rounds(self):
        out, _ = loaded()
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        readme = (ROOT / "src" / "features" / "rounds" / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("TODO", readme)
        results = R.run_rounds(out)
        for text in (doc, readme):
            for phrase in ("views.sql", "on or after", "2023-12-31", "clauses + steps + 5", "1.25",
                           "agreement", "oracle", "scenario", "has_ia_member", "LoadComplete"):
                self.assertIn(phrase, text, phrase)
        for res in results:
            n = res.round.number
            line = re.search(rf"Round {n}\b.*", doc)
            self.assertIsNotNone(line, f"docs have no 'Round {n}' entry")
            entry = doc[line.start():line.start() + 1500]
            self.assertIn(f"{len(res.sqlite)} rows", entry, n)
            self.assertIn(f"measured `{res.measured}`", entry, n)
            self.assertIn(f"expected `{res.round.expected}`", entry, n)
            self.assertIn(f"SQL {V.score(res.sql_metrics)} vs Cypher {V.score(res.cypher_metrics)}", entry, n)
        no_ia = sum(f == "N" for _, f in results[1].sqlite)
        self.assertIn(f"{no_ia} of them have no IA member", doc)
        self.assertIn("more than one unit", doc)


if __name__ == "__main__":
    unittest.main()
