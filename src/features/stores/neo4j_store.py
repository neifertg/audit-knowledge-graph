"""Load `<out>/akg.sqlite` into Neo4j (E3 child b, change 016).

Both stores come from the same typed rows: the graph is loaded from the SQLite file, which holds no
answer key (INV-6). A load REPLACES the whole database except its lock: point NEO4J_URI only at a
database dedicated to this project.

Order: lock (atomic MERGE, server clock, stale after 10 min) -> clear (implicit transaction,
LoadLock kept) -> constraints -> nodes -> edges -> LoadComplete (reconciled checksum) -> release lock
(finally, own token only). A failed load leaves no LoadComplete, so a half-loaded graph is detectable.
"""
import hashlib
import os
import sqlite3
import uuid
from pathlib import Path

from .graph_model import REVIEW_ENDPOINTS, derive, label_of
from .sqlite_store import DATABASE

BATCH = 1000
STALE_MINUTES = 10


class Neo4jLoadError(Exception):
    pass


def configured() -> bool:
    return bool(os.environ.get("NEO4J_URI"))


def connect():
    """A driver from NEO4J_URI, NEO4J_USER and NEO4J_PASSWORD (imported only when used)."""
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable

    uri = os.environ.get("NEO4J_URI")
    if not uri:
        raise Neo4jLoadError("NEO4J_URI is not set")
    driver = GraphDatabase.driver(uri, auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "")))
    try:
        driver.verify_connectivity()
    except (ServiceUnavailable, OSError) as error:
        driver.close()
        raise Neo4jLoadError(f"cannot reach Neo4j at NEO4J_URI={uri}: {error}") from error
    return driver


def reconciled_checksum(build_dir: Path) -> str:
    """SHA-256 over the reconciled CSVs (names and bytes), identifying the build that was loaded."""
    h = hashlib.sha256()
    for p in sorted((Path(build_dir) / "reconciled").glob("*.csv")):
        h.update(p.name.encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def load_complete(driver) -> str | None:
    """The checksum of the last completed load, or None if the graph is empty or half-loaded."""
    records = driver.execute_query("MATCH (c:LoadComplete) RETURN c.checksum AS checksum").records
    return records[0]["checksum"] if len(records) == 1 else None


def _rows(con, table: str) -> list[dict]:
    cur = con.execute(f"SELECT * FROM {table}")
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def _batches(rows: list):
    for i in range(0, len(rows), BATCH):
        yield rows[i:i + BATCH]


def acquire_lock(driver, token: str) -> None:
    driver.execute_query("CREATE CONSTRAINT loadlock_name IF NOT EXISTS FOR (l:LoadLock) REQUIRE l.name IS UNIQUE")
    record = driver.execute_query(
        "MERGE (l:LoadLock {name: 'load'}) ON CREATE SET l.token = $token, l.started = datetime() "
        "WITH l, (l.token <> $token AND l.started < datetime() - duration({minutes: $stale})) AS stale "
        "FOREACH (_ IN CASE WHEN stale THEN [1] ELSE [] END | SET l.token = $token, l.started = datetime()) "
        "RETURN l.token = $token AS ours, duration.inSeconds(l.started, datetime()).seconds AS age",
        token=token, stale=STALE_MINUTES).records[0]
    if not record["ours"]:
        raise Neo4jLoadError(f"another load holds the Neo4j lock (started {record['age']} s ago); "
                             f"it is treated as stale after {STALE_MINUTES} minutes")


def release_lock(driver, token: str) -> None:
    driver.execute_query("MATCH (l:LoadLock {name: 'load', token: $token}) DELETE l", token=token)


def clear(driver) -> None:
    with driver.session() as session:  # CALL ... IN TRANSACTIONS needs an implicit transaction
        session.run("MATCH (n) WHERE NOT n:LoadLock CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 5000 ROWS").consume()


def load_neo4j(build_dir: Path, driver) -> dict:
    """Replace the graph with <build_dir>/akg.sqlite's facts; returns node and edge counts."""
    build_dir = Path(build_dir)
    database = build_dir / DATABASE
    if not database.exists():
        raise Neo4jLoadError(f"{database} is missing: load SQLite first (`python -m akg load --out {build_dir}`)")
    token = uuid.uuid4().hex
    acquire_lock(driver, token)
    con = sqlite3.connect(database)
    try:
        clear(driver)
        nodes, edges = derive()
        for label in sorted({n.label for n in nodes}):
            driver.execute_query(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE")
        label = {n.table: n.label for n in nodes}
        node_count = edge_count = 0
        for n in nodes:
            rows = _rows(con, n.table)
            source = f", n.source = '{n.source}'" if n.source else ""
            for batch in _batches(rows):
                driver.execute_query(f"UNWIND $rows AS r CREATE (n:{n.label}) SET n = r, n.id = r.{n.key}{source}", rows=batch)
            node_count += len(rows)

        def link(rows, from_label, to_label, rel_type, from_key, to_key, props):
            nonlocal edge_count
            for batch in _batches(rows):
                payload = [{"f": r[from_key], "t": r[to_key], "p": {k: r[k] for k in props if r[k] is not None}} for r in batch]
                driver.execute_query(f"UNWIND $rows AS r MATCH (a:{from_label} {{id: r.f}}) MATCH (b:{to_label} {{id: r.t}}) "
                                     f"CREATE (a)-[e:{rel_type}]->(b) SET e = r.p", rows=payload)
            edge_count += len(rows)

        for e in edges:  # each table's rows are read here, after the clear
            link(_rows(con, e.table), label[e.from_table], label[e.to_table], e.type, e.from_column, e.to_column, e.properties)
        link(_rows(con, "canonical_risk"), "CanonicalRisk", "TaxonomyNode", "PLACED_AT", "canonical_risk_id",
             "erm_l3_node_id", ())
        for kind, canonical in (("risk", "CanonicalRisk"), ("control", "CanonicalControl")):
            rows = _rows(con, f"{kind}_maps_to_canonical")
            for source in ("ERM", "IA"):
                link([r for r in rows if r["source"] == source], label_of(f"{kind}_{source.lower()}")[0], canonical,
                     "MAPS_TO", f"{kind}_id", f"canonical_{kind}_id", ("logit",))
        mapping = _rows(con, "ia_maps_to_erm")
        link([r for r in mapping if r["erm_node_id"] is not None], "TaxonomyNode", "TaxonomyNode", "IA_MAPS_TO_ERM",
             "ia_node_id", "erm_node_id", ("score", "basis"))
        unmapped = [r for r in mapping if r["erm_node_id"] is None]
        for batch in _batches(unmapped):
            driver.execute_query("UNWIND $rows AS r MATCH (n:TaxonomyNode {id: r.ia_node_id}) "
                                 "SET n.mapping = 'unmapped', n.mapping_score = r.score, n.mapping_basis = r.basis", rows=batch)
        queue = _rows(con, "review_queue")
        for kind, (a, b) in REVIEW_ENDPOINTS.items():
            link([r for r in queue if r["kind"] == kind], label_of(a)[0], label_of(b)[0], "REVIEW_CANDIDATE",
                 "item_a", "item_b", ("kind", "logit", "reason", "drivers"))
        driver.execute_query("CREATE (:LoadComplete {checksum: $checksum, loaded: datetime()})",
                             checksum=reconciled_checksum(build_dir))
        return {"nodes": node_count, "edges": edge_count, "unmapped": len(unmapped)}
    finally:
        con.close()
        release_lock(driver, token)
