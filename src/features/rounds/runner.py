"""Run the rounds on SQLite and, when configured, on Neo4j, compare, and export (E3 c and d; 017, 018).

    python -m akg rounds --out <dir>     (also steps 4 and 5 of `python -m akg build`)

SQLite gets `views.sql` as temporary views on each connection: each merges the ERM and IA tables
of one kind, as Neo4j's shared labels do. The views are never part of the store schema.

A round with setup (round 5) runs in a transaction that is always rolled back: on SQLite a TEMP
table on a read-only connection inside BEGIN ... ROLLBACK, so the store file cannot change; on Neo4j
one explicit transaction, closed (rolled back) in a `finally`, with no schema changes. Neo4j keeps
label and type names in its token store; the data is unchanged.

The Neo4j guard refuses a graph with no LoadComplete node, or one whose checksum differs from
`reconciled_checksum(<dir>)`. It catches a failed load and a graph from a different reconciled
build; it does NOT catch a changed akg.sqlite or changed published CSVs.

Exit codes: 0 all ran and agree; 1 a round disagrees, akg.sqlite is missing, the guard refused,
or Neo4j is configured but unreachable or fails. A configured Neo4j that fails is never "not run".
"""
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from src.features.stores.sqlite_store import DATABASE

from . import verdict
from .registry import ALL, REGISTER, VIEWS, Round


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


def statements(text: str, marker: str) -> list[str]:
    """A setup file's statements, comments dropped, split on ';'."""
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith(marker))
    return [s.strip() for s in code.split(";") if s.strip()]


def sqlite_connection(build_dir: Path) -> sqlite3.Connection:
    """A read-only connection to <dir>/akg.sqlite with the shared temporary views (autocommit, so
    a setup round controls its own transaction)."""
    path = Path(build_dir) / DATABASE
    if not path.exists():
        raise RoundsError(f"{path} is missing; run `python -m akg load --out {build_dir}` first")
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, isolation_level=None)
    con.executescript(VIEWS.read_text(encoding="utf-8"))
    return con


def run_sqlite(rnd: Round, con: sqlite3.Connection, query: str | None = None, register=None, **params) -> list[tuple]:
    query, params = query or rnd.sql, {**rnd.params, **params}
    if not rnd.has_setup:
        return normalise(con.execute(query, params).fetchall())
    register = REGISTER if register is None else register
    con.execute("BEGIN")
    try:
        for stmt in statements(rnd.sql_setup, "--"):
            if re.search(r":\w+", stmt):
                con.executemany(stmt, register)
            else:
                con.execute(stmt)
        return normalise(con.execute(query, params).fetchall())
    finally:
        con.execute("ROLLBACK")


def check_graph(driver, build_dir: Path) -> None:
    """Refuse a half-loaded graph or one loaded from a different reconciled build."""
    from src.features.stores.neo4j_store import load_complete, reconciled_checksum

    loaded = load_complete(driver)
    if loaded is None:
        raise RoundsError("the Neo4j graph has no LoadComplete node (empty or half-loaded); run `akg load`")
    if loaded != reconciled_checksum(build_dir):
        raise RoundsError("the Neo4j graph's LoadComplete checksum differs from this build's reconciled "
                          "checksum (loaded from a different build); run `akg load`")


def run_neo4j(rnd: Round, driver, query: str | None = None, register=None, **params) -> list[tuple]:
    query, params = query or rnd.cypher, {**rnd.params, **params}
    if not rnd.has_setup:
        return normalise(tuple(r.values()) for r in driver.execute_query(query, params).records)
    register = REGISTER if register is None else register
    with driver.session() as session:
        tx = session.begin_transaction()
        try:
            for stmt in statements(rnd.cypher_setup, "//"):
                tx.run(stmt, rows=list(register)).consume()
            return normalise(tuple(r.values()) for r in tx.run(query, params))
        finally:
            tx.close()  # never committed: closing an open transaction rolls it back


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

    @property
    def margin(self) -> float:
        return verdict.margin(self.sql_metrics, self.cypher_metrics)


def run_rounds(build_dir: Path, driver=None, rounds=ALL) -> list[Result]:
    """Every round and the supporting query on SQLite, and on Neo4j when a driver is given."""
    con = sqlite_connection(build_dir)
    try:
        if driver is not None:
            check_graph(driver, build_dir)
        return [Result(r, run_sqlite(r, con), run_neo4j(r, driver) if driver is not None else None,
                       verdict.metrics(r.scored("sql"), "sql"), verdict.metrics(r.scored("cypher"), "cypher"))
                for r in rounds]
    finally:
        con.close()


def _is_driver_error(error: Exception) -> bool:
    return type(error).__module__.split(".")[0] == "neo4j"


def main(build_dir: Path, seed: int | None = None) -> int:
    """Print one line per round, write <dir>/rounds.json; exit codes as in the module docstring."""
    from src.features.stores.neo4j_store import Neo4jLoadError, configured

    from .export import write_export

    driver = None
    try:
        if configured():
            from src.features.stores.neo4j_store import connect

            driver = connect()
        results = run_rounds(build_dir, driver)
    except (RoundsError, Neo4jLoadError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # a driver error (bad password, Cypher error): a clean line, not a traceback
        if not _is_driver_error(error):
            raise
        print(f"error: Neo4j failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    finally:
        if driver is not None:
            driver.close()
    disagree = []
    for res in results:
        label = f"round {res.round.number}" if not res.round.supporting else str(res.round.number)
        if res.agree is None:
            neo = "Neo4j: not run"
        else:
            neo = f"Neo4j: {len(res.neo4j)} rows, {'agree' if res.agree else 'DISAGREE'}"
            if not res.agree:
                disagree.append(str(res.round.number))
        print(f"{label}: SQLite {len(res.sqlite)} rows; {neo}; measured verdict {res.measured} "
              f"(SQL {verdict.score(res.sql_metrics)}, Cypher {verdict.score(res.cypher_metrics)})")
    path = write_export(results, Path(build_dir), Path(build_dir) / "rounds.json", seed)
    print(f"wrote {path.name}")
    if disagree:
        print(f"error: SQL and Cypher disagree on round(s) {', '.join(disagree)}", file=sys.stderr)
        return 1
    return 0
