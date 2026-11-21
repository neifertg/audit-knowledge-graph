"""The Neo4j graph model, derived from the schema metadata (E3 child b, change 016, AC-1).

Pure: no server needed. Rules:
- Node tables: every table with a `primary key` column, except the four SPECIAL reconciled tables.
  Label = CamelCase of the table name; per-source tables share a label and carry `source`.
- Relationship tables: no primary key and two single-file foreign keys. Type = the file name's
  middle: strip `_erm`/`_ia`, then `<first target base>_` from the front and `_<second target base>`
  from the end (control_mitigates_risk_ia -> MITIGATES). Edges run first FK -> second FK.
- SPECIAL reconciled tables map to MAPS_TO, IA_MAPS_TO_ERM (+ `unmapped` IA node properties) and
  REVIEW_CANDIDATE; canonical_risk.erm_l3_node_id also becomes PLACED_AT.
"""
import re
from dataclasses import dataclass

from .schema import Table, load_tables

SOURCED = {"risk_erm": ("Risk", "ERM"), "risk_ia": ("Risk", "IA"),
           "control_erm": ("Control", "ERM"), "control_ia": ("Control", "IA"),
           "taxonomy_node_erm": ("TaxonomyNode", "ERM"), "taxonomy_node_ia": ("TaxonomyNode", "IA")}
SPECIAL = ("ia_maps_to_erm", "risk_maps_to_canonical", "control_maps_to_canonical", "review_queue")
# review_queue endpoints by kind: (from table, to table)
REVIEW_ENDPOINTS = {"risk": ("risk_erm", "risk_ia"), "duplicate": ("risk_erm", "risk_erm"),
                    "control": ("control_erm", "control_ia")}
SOURCE_SUFFIX = re.compile(r"_(erm|ia)$")


def label_of(table_name: str) -> tuple[str, str | None]:
    """(label, source or None) for a node table."""
    if table_name in SOURCED:
        return SOURCED[table_name]
    return "".join(w.capitalize() for w in table_name.split("_")), None


@dataclass(frozen=True)
class NodeSpec:
    table: str
    label: str
    source: str | None
    key: str          # primary key column, also stored as `id`


@dataclass(frozen=True)
class EdgeSpec:
    table: str
    type: str
    from_table: str
    to_table: str
    from_column: str
    to_column: str
    properties: tuple[str, ...]


def edge_type(table: Table) -> str:
    refs = [c.references for c in table.columns if c.references]
    first, second = (SOURCE_SUFFIX.sub("", r) for r in refs[:2])
    middle = SOURCE_SUFFIX.sub("", table.name)
    if not middle.startswith(first + "_") or not middle.endswith("_" + second):
        raise ValueError(f"{table.name}: cannot derive a relationship type from {first!r} and {second!r}")
    return middle[len(first) + 1:-(len(second) + 1)].upper()


def derive(tables: list[Table] | None = None) -> tuple[list[NodeSpec], list[EdgeSpec]]:
    tables = tables or load_tables()
    nodes, edges = [], []
    for t in tables:
        if t.name in SPECIAL:
            continue
        if any(c.primary for c in t.columns):
            label, source = label_of(t.name)
            nodes.append(NodeSpec(t.name, label, source, t.primary_key[0]))
        else:
            fks = [c for c in t.columns if c.references]
            if len(fks) != 2:
                raise ValueError(f"{t.name}: a relationship table needs exactly two single-file foreign keys")
            edges.append(EdgeSpec(t.name, edge_type(t), fks[0].references, fks[1].references, fks[0].name,
                                  fks[1].name, tuple(c.name for c in t.columns if c not in fks)))
    return nodes, edges


def counts() -> dict:
    nodes, edges = derive()
    return {"node_tables": len(nodes), "labels": len({n.label for n in nodes}),
            "relationship_tables": len(edges), "special_tables": len(SPECIAL),
            "relationship_types": sorted({e.type for e in edges})}
