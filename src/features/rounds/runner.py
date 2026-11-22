"""Run the rounds on SQLite and, when configured, on Neo4j, and compare (E3 child c, change 017).

    python -m akg rounds --out <dir>     (also step 4 of `python -m akg build`)

SQLite gets `views.sql` as temporary views on each connection: each merges the ERM and IA tables
of one kind, as Neo4j's shared labels do. The views are never part of the store schema.

The Neo4j guard refuses a graph with no LoadComplete node, or one whose checksum differs from
`reconciled_checksum(<dir>)`. It catches a failed load and a graph from a different reconciled
build; it does NOT catch a changed akg.sqlite or changed published CSVs.

Exit codes: 0 all ran and agree; 1 a round disagrees, akg.sqlite is missing, the guard refused,
or Neo4j is configured but unreachable. A configured Neo4j that fails is never "not run".
"""
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from src.features.stores.sqlite_store import DATABASE

from . import verdict
from .registry import ROUNDS, VIEWS, Round


class RoundsError(Exception):
    pass


def normalise(rows) -> list[tuple]:
    """Each value as int or str (None kept), so both drivers' rows compare equal."""
    def value(v):
        if v is None or isinstance(v, (int, str)):
            return v
        if isinstance(v, float) and v.is_integer():
            return int(v)
        return str(v)
    return [tuple(value(v) for v in row) for row in rows]


def comparable(rnd: Round, rows: list[tuple]) -> list[tuple]:
    return rows if rnd.ordered else sorted(rows, key=repr)


def sqlite_connection(build_dir: Path) -> sqlite3.Connection:
    """A read-only connection to <dir>/akg.sqlite with the shared temporary views."""
    path = Path(build_dir) / DATABASE
    if not path.exists():
        raise RoundsError(f"{path} is missing; run `python -m akg load --out {build_dir}` first")
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    con.executescript(VIEWS.read_text(encoding="utf-8"))
    return con


def run_sqlite(rnd: Round, con: sqlite3.Connection, **params) -> list[tuple]:
    return normalise(con.execute(rnd.sql, {**rnd.params, **params}).fetchall())


def check_graph(driver, build_dir: Path) -> None:
    """Refuse a half-loaded graph or one loaded from a different reconciled build."""
    from src.features.stores.neo4j_store import load_complete, reconciled_checksum

    loaded = load_complete(driver)
    if loaded is None:
        raise RoundsError("the Neo4j graph has no LoadComplete node (empty or half-loaded); run `akg load`")
    if loaded != reconciled_checksum(build_dir):
        raise RoundsError("the Neo4j graph's LoadComplete checksum differs from this build's reconciled "
                          "checksum (loaded from a different build); run `akg load`")


def run_neo4j(rnd: Round, driver, **params) -> list[tuple]:
    records = driver.execute_query(rnd.cypher, {**rnd.params, **params}).records
    return normalise(tuple(r.values()) for r in records)


@dataclass
class Result:
    round: Round
    sqlite: list[tuple]
    neo4j: list[tuple] | None      # None: Neo4j not run
    sql_metrics: dict
    cypher_metrics: dict

    @property
    def agree(self) -> bool | None:
        if self.neo4j is None:
            return None
        return comparable(self.round, self.sqlite) == comparable(self.round, self.neo4j)

    @property
    def measured(self) -> str:
        return verdict.measured(self.sql_metrics, self.cypher_metrics)


def run_rounds(build_dir: Path, driver=None, rounds=ROUNDS) -> list[Result]:
    """Every round on SQLite, and on Neo4j when a driver is given (after the guard)."""
    con = sqlite_connection(build_dir)
    try:
        if driver is not None:
            check_graph(driver, build_dir)
        return [Result(r, run_sqlite(r, con), run_neo4j(r, driver) if driver is not None else None,
                       verdict.metrics(r.sql, "sql"), verdict.metrics(r.cypher, "cypher")) for r in rounds]
    finally:
        con.close()


def main(build_dir: Path) -> int:
    """Print one line per round; exit codes as in the module docstring."""
    from src.features.stores.neo4j_store import Neo4jLoadError, configured

    driver = None
    try:
        if configured():
            from src.features.stores.neo4j_store import connect

            driver = connect()
        results = run_rounds(build_dir, driver)
    except (RoundsError, Neo4jLoadError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    finally:
        if driver is not None:
            driver.close()
    disagree = []
    for res in results:
        if res.agree is None:
            neo = "Neo4j: not run"
        else:
            neo = f"Neo4j: {len(res.neo4j)} rows, {'agree' if res.agree else 'DISAGREE'}"
            if not res.agree:
                disagree.append(res.round.number)
        print(f"round {res.round.number}: SQLite {len(res.sqlite)} rows; {neo}; measured verdict "
              f"{res.measured} (SQL {verdict.score(res.sql_metrics)}, Cypher {verdict.score(res.cypher_metrics)})")
    if disagree:
        print(f"error: SQL and Cypher disagree on round(s) {', '.join(map(str, disagree))}", file=sys.stderr)
        return 1
    return 0
