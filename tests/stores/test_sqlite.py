"""E3 child a (015): SQLite schema generated from the dictionaries, and the loader."""
import csv
import shutil
import sqlite3
import tempfile
import time
import unittest
from functools import cache
from pathlib import Path

from src.features.stores import schema as S
from src.features.stores import sqlite_store as L

from tests.generator.helpers import ROOT, run_akg
from tests.reconciliation.helpers import full_build


@cache
def loaded() -> tuple[Path, float]:
    """The cached seed-42 build (reconciled, not loaded), loaded once; returns (dir, seconds)."""
    out = full_build(42)
    start = time.time()
    L.load(out)
    return out, time.time() - start


def rows_of(con, table: str) -> list[tuple]:
    return sorted(con.execute(f"SELECT * FROM {table}").fetchall(), key=repr)


class SqliteTests(unittest.TestCase):
    def test_ac1_schema_is_generated_from_the_dictionaries(self):
        self.assertEqual(S.SCHEMA.read_text(encoding="utf-8"), S.generate(),
                         "regenerate: .venv\\Scripts\\python -m src.features.stores.schema")
        tables = {t.path for t in S.load_tables()}
        out = full_build(42)
        published = {p.relative_to(out).as_posix() for p in out.rglob("*.csv")}
        self.assertEqual(tables, {p for p in published if not p.startswith("answer_key/")})
        self.assertEqual(len(tables), 47)
        self.assertFalse(any(t.startswith("answer_key/") for t in tables))

    def test_ac2_type_and_key_rules(self):
        fixture = """### `team.csv`

| column | type | values |
|---|---|---|
| `team_id` | id | primary key |
| `size` | int | 1-9 |
| `budget` | decimal | money |
| `tier` | enum | A, B, C's |

### `member.csv`

| column | type | values |
|---|---|---|
| `member_id` | id | primary key |
| `team_id` | id | `team.csv` |
| `left_on` | date | ISO 8601, blank while active |

### `member_owns_team.csv`

| column | type | values |
|---|---|---|
| `member_id` | id | `member.csv` |
| `item_id` | id | `team.csv` or `member.csv` by `kind` |

### `answer_key/secret.csv`

| column | type | values |
|---|---|---|
| `x` | id | primary key |
"""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "dict.md"
            d.write_text(fixture, encoding="utf-8")
            tables = S.load_tables([d])
            self.assertEqual([t.name for t in tables], ["team", "member", "member_owns_team"], "dependency order")
            sql = S.generate([d])
        self.assertIn("team_id TEXT NOT NULL PRIMARY KEY", sql)
        self.assertIn("size INTEGER NOT NULL", sql)
        self.assertIn("budget REAL NOT NULL", sql)
        self.assertIn("CHECK (tier IN ('A', 'B', 'C''s'))", sql)
        self.assertIn("left_on TEXT,", sql.replace("left_on TEXT\n", "left_on TEXT,\n"))
        self.assertIn("FOREIGN KEY (team_id) REFERENCES team(team_id)", sql)
        self.assertIn("PRIMARY KEY (member_id, item_id)", sql, "relationship table: composite key over id columns")
        self.assertNotIn("FOREIGN KEY (item_id)", sql, "two-file values get no foreign key")
        self.assertNotIn("secret", sql, "answer-key sections are skipped")
        con = sqlite3.connect(":memory:")
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(sql)
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("INSERT INTO team VALUES ('T1', 3, 1.5, 'Z')")  # enum CHECK

    def test_ac3_every_row_lands_once_and_keys_hold(self):
        out, seconds = loaded()
        print(f"\nseed-42 load: {seconds:.2f}s")
        self.assertLess(seconds, 5.0)
        con = sqlite3.connect(out / L.DATABASE)
        total = 0
        for table in S.load_tables():
            with self.subTest(table=table.name):
                expected = sorted(L.read_rows(out, table), key=repr)  # cast by dictionary type
                self.assertEqual(rows_of(con, table.name), expected)
                total += len(expected)
        print(f"rows: {total}")
        self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(con.execute("SELECT count(*) FROM ia_maps_to_erm WHERE erm_node_id IS NULL").fetchone()[0],
                         sum(1 for r in csv.DictReader(open(out / "reconciled" / "ia_maps_to_erm.csv", encoding="utf-8"))
                             if r["erm_node_id"] == "unmapped"))
        ids = lambda t, c: {r[0] for r in con.execute(f"SELECT {c} FROM {t}")}
        targets = {"ERM": ids("risk_erm", "risk_id"), "IA": ids("risk_ia", "risk_id")}
        for source, item in con.execute("SELECT source, risk_id FROM risk_maps_to_canonical"):
            self.assertIn(item, targets[source])
        ctargets = {"ERM": ids("control_erm", "control_id"), "IA": ids("control_ia", "control_id")}
        for source, item in con.execute("SELECT source, control_id FROM control_maps_to_canonical"):
            self.assertIn(item, ctargets[source])
        by_kind = {"risk": (targets["ERM"], targets["IA"]), "duplicate": (targets["ERM"], targets["ERM"]),
                   "control": (ctargets["ERM"], ctargets["IA"])}
        for kind, a, b in con.execute("SELECT kind, item_a, item_b FROM review_queue"):
            self.assertIn(a, by_kind[kind][0])
            self.assertIn(b, by_kind[kind][1])
        con.close()

    def test_ac4_build_and_load_commands_idempotent_and_answer_key_free(self):
        out, _ = loaded()
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "copy"
            shutil.copytree(out, copy, ignore=shutil.ignore_patterns("answer_key", L.DATABASE))
            run_akg("load", "--out", str(copy))
            run_akg("load", "--out", str(copy))  # twice: idempotent
            a, b = sqlite3.connect(out / L.DATABASE), sqlite3.connect(copy / L.DATABASE)
            names = lambda con: [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            self.assertEqual(names(a), names(b))
            self.assertFalse(any(n.startswith("answer_key") or n in ("risk_clusters", "control_clusters", "scenarios",
                                                                         "taxonomy_map") for n in names(b)))
            for table in names(a):
                self.assertEqual(rows_of(a, table), rows_of(b, table), table)
            a.close()
            b.close()
            self.assertFalse((copy / (L.DATABASE + ".partial")).exists())
            # no stale database: reconcile, --no-load and --no-reconcile remove it
            run_akg("reconcile", "--out", str(copy))
            self.assertFalse((copy / L.DATABASE).exists())
            # a missing reconciled/ fails clearly, and leaves no database
            shutil.rmtree(copy / "reconciled")
            result = run_akg("load", "--out", str(copy), check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reconciled", result.stderr)
            self.assertFalse((copy / L.DATABASE).exists())
        with tempfile.TemporaryDirectory() as tmp:
            run_akg("build", "--size", "sample", "--out", tmp)
            self.assertTrue((Path(tmp) / L.DATABASE).exists(), "build loads by default")
            result = run_akg("build", "--size", "sample", "--out", tmp, "--no-load")
            self.assertFalse((Path(tmp) / L.DATABASE).exists())
            self.assertNotIn("round 1:", result.stdout, "--no-load skips the rounds (017)")
            run_akg("build", "--size", "sample", "--out", tmp)
            result = run_akg("build", "--size", "sample", "--out", tmp, "--no-reconcile")
            self.assertFalse((Path(tmp) / L.DATABASE).exists())
            self.assertNotIn("round 1:", result.stdout, "--no-reconcile skips the rounds (017)")

    def test_ac5_docs_describe_the_sqlite_store(self):
        doc = (ROOT / "docs" / "data-model.md").read_text(encoding="utf-8")
        readme = (ROOT / "src" / "features" / "stores" / "README.md").read_text(encoding="utf-8")
        for text in (doc, readme):
            for phrase in ("akg.sqlite", "schema.sql", "reconciled_dictionary.md", "answer key"):
                self.assertIn(phrase, text)
        self.assertIn("not golden", doc)
        self.assertNotIn("TODO", readme)
        self.assertIn("python -m src.features.stores.schema", readme)


if __name__ == "__main__":
    unittest.main()
