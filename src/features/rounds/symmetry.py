"""The measured symmetry table: one minimal SQL and Cypher snippet per construct (changes 020, 021).

`table()` runs the verdict rule on each pair, so the published table always comes from the code
(L-021). The expected figures are pinned as literals in rounds.test_rounds_5_7, never derived from
this module, so the code is not checked only against itself.
"""
from . import verdict

# construct -> (SQL snippet, Cypher snippet, disclosed difference?)
SNIPPETS = {
    "read": ("SELECT a.x\nFROM a\nWHERE a.y = 1", "MATCH (a:A)\nWHERE a.y = 1\nRETURN a.x", False),
    "join or hop": ("SELECT a.x\nFROM a\nJOIN b ON b.id = a.id", "MATCH (a:A)-[:R]->(b:B)\nRETURN a.x", False),
    "fixed path *2": ("SELECT a.x\nFROM a\nJOIN b ON b.id = a.id\nJOIN c ON c.id = b.id",
                      "MATCH (a:A)-[:R*2]->(c:C)\nRETURN a.x", False),
    "recursion (anchored on a literal)": (
        "WITH RECURSIVE up(v) AS (\n  SELECT :v\n  UNION\n  SELECT r.v\n  FROM r\n  JOIN up ON r.w = up.v)\n"
        "SELECT up.v\nFROM up", "MATCH (a:V)-[:R*0..]->(:V {name: $v})\nRETURN a.name", False),
    "recursion (anchored on a table)": (
        "WITH RECURSIVE up(v) AS (\n  SELECT s.v\n  FROM s\n  UNION\n  SELECT r.v\n  FROM r\n  JOIN up ON r.w = up.v)\n"
        "SELECT up.v\nFROM up", "MATCH (a:V)-[:R*0..]->(:V {name: $v})\nRETURN a.name", False),
    "stage": ("WITH x AS (\n  SELECT a.id\n  FROM a)\nSELECT x.id\nFROM x", "MATCH (a:A)\nWITH a\nRETURN a.id", False),
    "subquery": ("SELECT a.id\nFROM a\nWHERE a.id IN (\n  SELECT b.id\n  FROM b)",
                 "MATCH (a:A)\nWHERE EXISTS {\n  MATCH (a)-[:R]->(:B) }\nRETURN a.id", False),
    "union": ("SELECT id\nFROM a\nUNION ALL\nSELECT id\nFROM b",
              "MATCH (a:A)\nRETURN a.id AS id\nUNION ALL\nMATCH (b:B)\nRETURN b.id AS id", False),
    "write": ("INSERT INTO t (v)\nVALUES (:v)", "MERGE (t:T {v: $v})", False),
    "setup": ("CREATE TEMP TABLE t (v TEXT);\nINSERT INTO t (v)\nVALUES (:v)",
              "UNWIND $rows AS row\nMERGE (t:T {v: row.v})\nCREATE (t)-[:R]->(t)", False),
    "optional": ("SELECT a.x\nFROM a\nLEFT JOIN b ON b.id = a.id",
                 "MATCH (a:A)\nOPTIONAL MATCH (a)-[:R]->(b:B)\nRETURN a.x", False),
    "filter after an aggregate": ("SELECT a.k, COUNT(*) AS n\nFROM a\nGROUP BY a.k\nHAVING COUNT(*) > 1",
                                  "MATCH (a:A)\nWITH a.k AS k, count(*) AS n\nWHERE n > 1\nRETURN k, n", True),
    "upsert": ("INSERT INTO t (v)\nVALUES (:v)\nON CONFLICT (v) DO UPDATE SET n = n + 1",
               "MERGE (t:T {v: $v})\nON CREATE SET t.n = 1\nON MATCH SET t.n = t.n + 1", True),
    "select inside a write": ("INSERT INTO t (v)\nSELECT a.v\nFROM a", "MATCH (a:A)\nCREATE (:T {v: a.v})", False),
}

FIELDS = ("clauses", "steps", "moving_parts")


def triple(text: str, engine: str) -> list[int]:
    m = verdict.metrics(text, engine)
    return [m[f] for f in FIELDS]


def table() -> list[dict]:
    """One row per construct: the snippets and their measured (clauses, steps, moving parts)."""
    return [{"construct": name, "sql": sql, "cypher": cypher, "disclosed": disclosed,
             "sql_metrics": triple(sql, "sql"), "cypher_metrics": triple(cypher, "cypher")}
            for name, (sql, cypher, disclosed) in SNIPPETS.items()]
