"""E3 child b (016): the Neo4j graph model, loader, lock and INV-8 parity with SQLite.

Neo4j tests skip without NEO4J_URI and fail instead when AKG_REQUIRE_NEO4J=1. Run them locally with
    .venv\\Scripts\\python -m src.features.stores.with_neo4j -m unittest discover -s tests
"""
import hashlib
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from collections import Counter
from pathlib import Path

from src.features.stores import graph_model as G
from src.features.stores import neo4j_store as N
from src.features.stores.sqlite_store import DATABASE

from tests.generator.helpers import ROOT, akg_env, run_akg
from tests.stores.test_sqlite import loaded

_DRIVER = None


def neo4j_driver():
    """A driver for NEO4J_URI; skips without it, fails instead when AKG_REQUIRE_NEO4J=1."""
    global _DRIVER
    if not os.environ.get("NEO4J_URI"):
        if os.environ.get("AKG_REQUIRE_NEO4J") == "1":
            raise AssertionError("AKG_REQUIRE_NEO4J=1 but NEO4J_URI is not set")
        raise unittest.SkipTest("NEO4J_URI is not set (run through src.features.stores.with_neo4j)")
    if _DRIVER is None:
        _DRIVER = N.connect()
    return _DRIVER


def graph():
    """(driver, build dir) with the seed-42 graph loaded and complete; reloads if missing or different."""
    driver = neo4j_driver()
    out, _ = loaded()
    if N.load_complete(driver) != N.reconciled_checksum(out):
        N.load_neo4j(out, driver)
    return driver, out


def q(driver, cypher, **params):
    return driver.execute_query(cypher, **params).records


def snapshot(driver) -> dict:
    """Every node (label set, id, props) and edge (type, ends, props), as multisets."""
    nodes = Counter((tuple(sorted(r["labels"])), r["id"], tuple(sorted(r["props"].items())))
                    for r in q(driver, "MATCH (n) WHERE NOT n:LoadLock AND NOT n:LoadComplete "
                                       "RETURN labels(n) AS labels, n.id AS id, properties(n) AS props"))
    edges = Counter((r["t"], r["a"], r["b"], tuple(sorted(r["props"].items())))
                    for r in q(driver, "MATCH (a)-[e]->(b) RETURN type(e) AS t, a.id AS a, b.id AS b, properties(e) AS props"))
    return {"nodes": nodes, "edges": edges}


def where(alias, source):
    return f" AND {alias}.source = '{source}'" if source else ""


class Neo4jTests(unittest.TestCase):
    # --- AC-1 (pure) ------------------------------------------------------------------------
    def test_ac1_graph_model_from_the_schema(self):
        c = G.counts()
        self.assertEqual((c["node_tables"], c["labels"], c["relationship_tables"], c["special_tables"]), (17, 14, 26, 4))
        self.assertEqual(len(c["relationship_types"]), 15)
        nodes, edges = G.derive()
        by_table = {n.table: n for n in nodes}
        self.assertEqual((by_table["risk_ia"].label, by_table["risk_ia"].source), ("Risk", "IA"))
        self.assertEqual((by_table["canonical_risk"].label, by_table["canonical_risk"].source), ("CanonicalRisk", None))
        self.assertEqual(by_table["business_unit"].label, "BusinessUnit")
        self.assertNotIn("ia_maps_to_erm", by_table, "special tables are not node tables")
        e = {x.table: x for x in edges}
        self.assertEqual((e["control_mitigates_risk_ia"].type, e["control_mitigates_risk_ia"].from_table,
                          e["control_mitigates_risk_ia"].to_table), ("MITIGATES", "control_ia", "risk_ia"))
        self.assertEqual(e["issue_owned_by_person"].type, "OWNED_BY")
        self.assertEqual(e["taxonomy_node_parent_of_taxonomy_node_erm"].type, "PARENT_OF")
        # (type, from label+source, to label+source) is unique per table, so parity can tell shared types apart
        keys = [(x.type, G.label_of(x.from_table), G.label_of(x.to_table)) for x in edges]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(G.REVIEW_ENDPOINTS["risk"], ("risk_erm", "risk_ia"))

    # --- AC-2 --------------------------------------------------------------------------------
    def test_ac2_load_is_idempotent_locked_and_answer_key_free(self):
        driver, out = graph()
        first = snapshot(driver)
        started = time.time()
        N.load_neo4j(out, driver)
        seconds = time.time() - started
        print(f"\nseed-42 Neo4j load: {seconds:.1f}s")
        self.assertLess(seconds, 30.0, "the plan's load bar")
        self.assertEqual(snapshot(driver), first, "loading twice gives identical multisets")
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "copy"
            shutil.copytree(out, copy, ignore=shutil.ignore_patterns("answer_key"))
            N.load_neo4j(copy, driver)
            self.assertEqual(snapshot(driver), first, "no answer key: identical graph")
            # a fresh foreign lock blocks the load
            q(driver, "MERGE (l:LoadLock {name: 'load'}) SET l.token = 'someone-else', l.started = datetime()")
            with self.assertRaises(N.Neo4jLoadError):
                N.load_neo4j(out, driver)
            # a stale lock (11 minutes old) is replaced
            q(driver, "MATCH (l:LoadLock {name: 'load'}) SET l.started = datetime() - duration({minutes: 11})")
            N.load_neo4j(out, driver)
            self.assertEqual(q(driver, "MATCH (l:LoadLock) RETURN count(l) AS c")[0]["c"], 0, "lock released")
            # a real mid-load failure: one edge table missing from the SQLite file
            broken = Path(tmp) / "broken"
            shutil.copytree(out, broken, ignore=shutil.ignore_patterns("answer_key"))
            con = sqlite3.connect(broken / DATABASE)
            con.execute("PRAGMA foreign_keys = OFF")
            con.execute("DROP TABLE control_mitigates_risk_ia")
            con.commit()
            con.close()
            with self.assertRaises(Exception):
                N.load_neo4j(broken, driver)
            self.assertIsNone(N.load_complete(driver), "a failed load leaves no LoadComplete")
            self.assertEqual(q(driver, "MATCH (l:LoadLock) RETURN count(l) AS c")[0]["c"], 0, "lock released on failure")
            self.assertGreater(q(driver, "MATCH (n:Risk) RETURN count(n) AS c")[0]["c"], 0, "it failed midway")
        N.load_neo4j(out, driver)
        self.assertEqual(snapshot(driver), first, "the next good load restores the graph")
        # an unreachable server fails clearly, naming NEO4J_URI
        saved = os.environ.get("NEO4J_URI")
        try:
            os.environ["NEO4J_URI"] = "bolt://127.0.0.1:1"
            with self.assertRaisesRegex(N.Neo4jLoadError, "NEO4J_URI"):
                N.connect()
        finally:
            os.environ["NEO4J_URI"] = saved

    # --- AC-3 --------------------------------------------------------------------------------
    def test_ac3_inv8_sqlite_and_neo4j_hold_the_same_facts(self):
        driver, out = graph()
        con = sqlite3.connect(out / DATABASE)
        sql = lambda query: sorted(con.execute(query).fetchall(), key=repr)
        nodes, edges = G.derive()
        total = 0
        for n in nodes:
            with self.subTest(table=n.table):
                expected = sql(f"SELECT {n.key} FROM {n.table}")
                actual = sorted(((r["id"],) for r in q(driver, f"MATCH (n:{n.label}) WHERE true{where('n', n.source)} RETURN n.id AS id")), key=repr)
                self.assertEqual(actual, expected)
                total += len(expected)
        print(f"\nnodes compared: {total}")
        self.assertEqual(total, 2821)
        label = {n.table: G.label_of(n.table) for n in nodes}
        for e in edges:
            with self.subTest(table=e.table):
                (la, sa), (lb, sb) = label[e.from_table], label[e.to_table]
                expected = sql(f"SELECT {e.from_column}, {e.to_column} FROM {e.table}")
                actual = sorted(((r["a"], r["b"]) for r in q(driver, f"MATCH (a:{la})-[:{e.type}]->(b:{lb}) WHERE true"
                                f"{where('a', sa)}{where('b', sb)} RETURN a.id AS a, b.id AS b")), key=repr)
                self.assertEqual(actual, expected, "multiset of (from, to) pairs")
        pairs = lambda cypher: sorted((tuple(r.values()) for r in q(driver, cypher)), key=repr)
        self.assertEqual(pairs("MATCH (c:CanonicalRisk)-[:PLACED_AT]->(t:TaxonomyNode) RETURN c.id, t.id"),
                         sql("SELECT canonical_risk_id, erm_l3_node_id FROM canonical_risk"))
        for kind, canonical in (("risk", "CanonicalRisk"), ("control", "CanonicalControl")):
            for source, lab in (("ERM", kind.capitalize()), ("IA", kind.capitalize())):
                self.assertEqual(
                    pairs(f"MATCH (a:{lab} {{source: '{source}'}})-[:MAPS_TO]->(b:{canonical}) RETURN a.id, b.id"),
                    sql(f"SELECT {kind}_id, canonical_{kind}_id FROM {kind}_maps_to_canonical WHERE source = '{source}'"))
        self.assertEqual(pairs("MATCH (a:TaxonomyNode)-[:IA_MAPS_TO_ERM]->(b:TaxonomyNode) RETURN a.id, b.id"),
                         sql("SELECT ia_node_id, erm_node_id FROM ia_maps_to_erm WHERE erm_node_id IS NOT NULL"))
        self.assertEqual(pairs("MATCH (n:TaxonomyNode {mapping: 'unmapped'}) RETURN n.id"),
                         sql("SELECT ia_node_id FROM ia_maps_to_erm WHERE erm_node_id IS NULL"))
        self.assertEqual(pairs("MATCH (a)-[e:REVIEW_CANDIDATE]->(b) RETURN a.id, b.id, e.kind"),
                         sql("SELECT item_a, item_b, kind FROM review_queue"))
        # properties: the lowest-key row per table, plus a NULL row per nullable column; NULL == absent
        for n in nodes:
            cols = [d[1] for d in con.execute(f"PRAGMA table_info({n.table})")]
            nullable = [d[1] for d in con.execute(f"PRAGMA table_info({n.table})") if not d[3]]
            keys = {con.execute(f"SELECT min({n.key}) FROM {n.table}").fetchone()[0]}
            for col in nullable:
                row = con.execute(f"SELECT min({n.key}) FROM {n.table} WHERE {col} IS NULL").fetchone()[0]
                if row is not None:
                    keys.add(row)
            for key in keys:
                with self.subTest(table=n.table, key=key):
                    row = dict(zip(cols, con.execute(f"SELECT * FROM {n.table} WHERE {n.key} = ?", (key,)).fetchone()))
                    props = q(driver, f"MATCH (n:{n.label} {{id: $id}}) RETURN properties(n) AS p", id=key)[0]["p"]
                    self.assertEqual({k: v for k, v in row.items() if v is not None},
                                     {k: v for k, v in props.items() if k in cols})
        edge_props = q(driver, "MATCH (a)-[e:REVIEW_CANDIDATE]->(b) RETURN a.id AS a, b.id AS b, properties(e) AS p "
                               "ORDER BY a, b LIMIT 1")[0]
        row = con.execute("SELECT kind, logit, reason, drivers FROM review_queue WHERE item_a = ? AND item_b = ?",
                          (edge_props["a"], edge_props["b"])).fetchone()
        self.assertEqual(edge_props["p"], dict(zip(("kind", "logit", "reason", "drivers"), row)))
        # reconciled-layer properties: the lowest-key row, plus the lowest row where each nullable column is NULL
        for kind in ("risk", "control"):
            for condition in ("logit IS NOT NULL", "logit IS NULL"):
                with self.subTest(table=f"{kind}_maps_to_canonical", rows=condition):
                    item, logit = con.execute(f"SELECT {kind}_id, logit FROM {kind}_maps_to_canonical WHERE {condition} "
                                              f"ORDER BY {kind}_id LIMIT 1").fetchone()
                    props = q(driver, "MATCH (a {id: $id})-[e:MAPS_TO]->() RETURN properties(e) AS p", id=item)[0]["p"]
                    self.assertEqual(props, {} if logit is None else {"logit": logit})
        for condition in ("erm_node_id IS NOT NULL", "erm_node_id IS NULL"):
            with self.subTest(table="ia_maps_to_erm", rows=condition):
                node, target, score, basis = con.execute(
                    f"SELECT ia_node_id, erm_node_id, score, basis FROM ia_maps_to_erm WHERE {condition} "
                    "ORDER BY ia_node_id LIMIT 1").fetchone()
                if target is not None:
                    props = q(driver, "MATCH (a:TaxonomyNode {id: $id})-[e:IA_MAPS_TO_ERM]->(b) "
                                      "RETURN b.id AS b, properties(e) AS p", id=node)[0]
                    self.assertEqual((props["b"], props["p"]), (target, {"score": score, "basis": basis}))
                else:
                    props = q(driver, "MATCH (n:TaxonomyNode {id: $id}) RETURN properties(n) AS p", id=node)[0]["p"]
                    self.assertEqual({k: props.get(k) for k in ("mapping", "mapping_score", "mapping_basis")},
                                     {"mapping": "unmapped", "mapping_score": score, "mapping_basis": basis})
        for kind in ("risk", "duplicate", "control"):  # review_queue has no nullable columns; one row per kind
            with self.subTest(table="review_queue", kind=kind):
                a, b, logit, reason, drivers = con.execute(
                    "SELECT item_a, item_b, logit, reason, drivers FROM review_queue WHERE kind = ? "
                    "ORDER BY item_a, item_b LIMIT 1", (kind,)).fetchone()
                props = q(driver, "MATCH (x {id: $a})-[e:REVIEW_CANDIDATE]->(y {id: $b}) RETURN properties(e) AS p",
                          a=a, b=b)[0]["p"]
                self.assertEqual(props, {"kind": kind, "logit": logit, "reason": reason, "drivers": drivers})
        # ERM and IA IDs never collide within a shared label
        for lab in ("Risk", "Control", "TaxonomyNode"):
            ids = Counter(r["id"] for r in q(driver, f"MATCH (n:{lab}) RETURN n.id AS id"))
            self.assertEqual([i for i, k in ids.items() if k > 1], [], lab)
        self.assertIsNotNone(N.load_complete(driver))
        con.close()

    # --- AC-4 --------------------------------------------------------------------------------
    def test_ac4_pipeline_env_helper_skip_and_require(self):
        # isolation: test subprocesses never see NEO4J_*, so an unreachable URI cannot break them
        saved = {k: os.environ.get(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD")}
        try:
            os.environ["NEO4J_URI"] = "bolt://127.0.0.1:1"
            with tempfile.TemporaryDirectory() as tmp:
                result = run_akg("build", "--size", "sample", "--out", tmp)
                self.assertNotIn("Neo4j: loaded", result.stdout)
                self.assertIn("Neo4j: skipped (NEO4J_URI is not set)", result.stdout, "says so when skipping")
                self.assertTrue((Path(tmp) / DATABASE).exists())
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        for name in ("test_batch.py", "test_offline.py"):
            source = (ROOT / "tests" / "generator" / name).read_text(encoding="utf-8")
            self.assertRegex(source, r"from \.helpers import [^\n]*akg_env", name)
            envs = re.findall(r"\benv=([A-Za-z_][\w.]*)", source)
            runs = source.count("subprocess.run(")
            self.assertTrue(envs and all(e == "akg_env" for e in envs), f"{name}: every env= is akg_env(): {envs}")
            akg_runs = len(re.findall(r'subprocess\.run\(\[sys\.executable, "-(?:m", "akg|c", GUARDED_BUILD)', source))
            self.assertEqual(len(envs), akg_runs, f"{name}: every akg subprocess ({akg_runs} of {runs}) passes env=akg_env()")
        # skip and require
        probe = ("import os, unittest, sys\nsys.path.insert(0, '.')\nfrom tests.stores.test_neo4j import neo4j_driver\n"
                 "try:\n    neo4j_driver()\nexcept unittest.SkipTest:\n    print('SKIP')\nexcept AssertionError:\n    print('FAIL')\n")
        base = akg_env()
        self.assertEqual(subprocess.run([sys.executable, "-c", probe], cwd=ROOT, env=base, capture_output=True,
                                        text=True).stdout.strip(), "SKIP")
        self.assertEqual(subprocess.run([sys.executable, "-c", probe], cwd=ROOT, env={**base, "AKG_REQUIRE_NEO4J": "1"},
                                        capture_output=True, text=True).stdout.strip(), "FAIL")
        # a build without NEO4J_URI never imports neo4j
        with tempfile.TemporaryDirectory() as tmp:
            code = ("import sys; sys.path.insert(0, '.'); from akg.__main__ import main; "
                    f"main(['build', '--size', 'sample', '--out', r'{tmp}']); print('neo4j' in sys.modules)")
            self.assertEqual(subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=base, capture_output=True,
                                            text=True).stdout.strip().splitlines()[-1], "False")
        # with_neo4j: hermetic, with a dummy secrets file under a fake home (HOME and USERPROFILE)
        with tempfile.TemporaryDirectory() as home:
            env = {**base, "HOME": home, "USERPROFILE": home}
            show = ("import hashlib, os; print(' '.join(hashlib.sha256(os.environ.get(k, '').encode()).hexdigest()[:12] "
                    "for k in ('NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD')))")
            missing = subprocess.run([sys.executable, "-m", "src.features.stores.with_neo4j", "-c", show], cwd=ROOT,
                                     env=env, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            self.assertIn("not found", missing.stderr)
            (Path(home) / ".claude").mkdir()
            dummy = {"uri": "bolt://dummy:7687", "username": "dummy-user", "password": "dummy-pass-9f3k"}
            (Path(home) / ".claude" / "secrets.yaml").write_text(
                "databases:\n  akg_neo4j:\n" + "".join(f'    {k}: "{v}"\n' for k, v in dummy.items()), encoding="utf-8")
            result = subprocess.run([sys.executable, "-m", "src.features.stores.with_neo4j", "-c", show], cwd=ROOT,
                                    env=env, capture_output=True, text=True)
            digest = lambda v: hashlib.sha256(v.encode()).hexdigest()[:12]
            self.assertEqual(result.stdout.split(), [digest(dummy[k]) for k in ("uri", "username", "password")])
            self.assertNotIn(dummy["password"], result.stdout + result.stderr)
        # the pipeline loads Neo4j when opted in (last: leaves the shared fixture complete)
        driver, out = graph()
        result = run_akg("load", "--out", str(out), neo4j=True)
        self.assertIn("Neo4j: loaded 2821 nodes", result.stdout)
        self.assertEqual(N.load_complete(driver), N.reconciled_checksum(out))

    # --- AC-5 (no server) ---------------------------------------------------------------------
    def test_ac5_docs_describe_the_graph_model(self):
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        readme = (ROOT / "src" / "features" / "stores" / "README.md").read_text(encoding="utf-8")
        for phrase in ("PLACED_AT", "MAPS_TO", "IA_MAPS_TO_ERM", "REVIEW_CANDIDATE", "mapping = 'unmapped'", "source",
                       "stores.test_neo4j.Neo4jTests.test_ac3_inv8_sqlite_and_neo4j_hold_the_same_facts"):
            self.assertIn(phrase, doc)
        for phrase in ("with_neo4j", "AKG_REQUIRE_NEO4J", "replaces the whole", "yaml", "concurrent"):
            self.assertIn(phrase, readme)


if __name__ == "__main__":
    unittest.main()
