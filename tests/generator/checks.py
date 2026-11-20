"""Check logic shared by tests at sample and full size, so each rule is written once."""
import csv
from collections import Counter

from .dictionary import TYPES, denied_in, name_list, parse
from .helpers import answer_key, read, tables

SOURCED = {"taxonomy_node_id": "taxonomy_node", "parent_id": "taxonomy_node", "child_id": "taxonomy_node",
           "risk_id": "risk", "control_id": "control"}
SHARED = {"segment_id": "segment", "business_unit_id": "business_unit",
          "auditable_entity_id": "auditable_entity", "process_id": "process", "system_id": "system",
          "person_id": "person", "regulation_id": "regulation", "audit_id": "audit", "issue_id": "issue"}


def referential(test, out) -> None:
    """AC-12 / INV-10: every relationship ID exists in the right entity file; nothing links ERM to IA."""
    written = tables(out)
    ids = {name: {next(iter(row.values())) for row in rows} for name, rows in written.items()}
    relationships = [n for n, rows in written.items() if rows and len(rows[0]) == 2 and all(
        c in SOURCED or c in SHARED for c in rows[0])]
    test.assertGreater(len(relationships), 20)
    for name in relationships:
        source = name.rsplit("_", 1)[1] if name.endswith(("_erm", "_ia")) else None
        for column in written[name][0]:
            if column in SOURCED:
                test.assertIsNotNone(source, f"{name}.{column} is sourced but the file has no source suffix")
                entity = f"{SOURCED[column]}_{source}"
            else:
                entity = SHARED[column]
            missing = {row[column] for row in written[name]} - ids[entity]
            test.assertFalse(missing, f"{name}.{column} references IDs missing from {entity}: {missing}")


def _rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def data_dictionary(test, out) -> None:
    """AC-9: the README data dictionary lists exactly the files and columns written, with valid values."""
    spec = parse()
    written = {p.relative_to(out).as_posix(): p for p in out.rglob("*.csv")}
    test.assertEqual(set(spec), set(written), "files in README vs files written")
    for name, path in written.items():
        rows, columns = _rows(path)
        test.assertEqual([c for c, _, _ in spec[name]], columns, f"{name}: columns differ from README")
        for column, type_, values in spec[name]:
            test.assertIn(type_, TYPES, f"{name}.{column}: unknown type {type_}")
            if type_ == "text":
                test.assertTrue(values.startswith("name_list: ") or values == "free_text",
                                f"{name}.{column}: text column must be marked name_list or free_text")
            if type_ == "enum":
                allowed = {v.strip() for v in values.split(",")}
                test.assertLessEqual({r[column] for r in rows}, allowed, f"{name}.{column}: values outside the README")


def output_names(test, out, deny) -> None:
    """AC-4 / INV-9, output part: name columns use their lists; no text cell names a real institution."""
    for name, columns in parse().items():
        rows, _ = _rows(out / name)
        for column, type_, values in columns:
            if type_ != "text":
                continue
            cells = [r[column] for r in rows]
            test.assertTrue(values.startswith("name_list: ") or values == "free_text",
                            f"{name}.{column}: text column must be marked name_list or free_text")
            if values.startswith("name_list: "):
                stray = sorted(set(cells) - name_list(values.split(": ", 1)[1]))
                test.assertEqual(stray, [], f"{name}.{column}: values not on the list")
            for cell in cells:
                test.assertEqual(denied_in(cell, deny), [], f"{name}.{column}: real name in {cell!r}")

ALLOWED_TARGET_LEVELS = {1: {1}, 2: {1, 2}, 3: {2, 3}}
ERM_L1 = {"Credit", "Market", "Liquidity", "Operational", "Compliance", "Strategic", "Reputational"}


def taxonomy_map(test, out) -> dict:
    """Every IA node mapped exactly once, to an existing ERM node at an allowed level, or unmapped.

    Returns {ia_node_id: erm_node_id or None}.
    """
    erm_nodes = {r["taxonomy_node_id"]: r for r in read(out, "taxonomy_node_erm")}
    ia_nodes = {r["taxonomy_node_id"]: r for r in read(out, "taxonomy_node_ia")}
    rows = answer_key(out, "taxonomy_map")
    test.assertEqual(sorted(r["ia_node_id"] for r in rows), sorted(ia_nodes), "IA nodes vs taxonomy_map rows")
    target = {}
    for row in rows:
        if row["erm_node_id"] == "unmapped":
            target[row["ia_node_id"]] = None
            continue
        test.assertIn(row["erm_node_id"], erm_nodes)
        ia_level = int(ia_nodes[row["ia_node_id"]]["level"])
        test.assertIn(int(erm_nodes[row["erm_node_id"]]["level"]), ALLOWED_TARGET_LEVELS[ia_level],
                      f"{row['ia_node_id']} maps to a deeper or disallowed ERM level")
        target[row["ia_node_id"]] = row["erm_node_id"]
    return target


def strict_tree(test, out, source: str) -> list[dict]:
    """INV-1 (taxonomy part): a strict three-level tree with names unique per level. Returns the nodes."""
    nodes = {r["taxonomy_node_id"]: r for r in read(out, f"taxonomy_node_{source}")}
    edges = read(out, f"taxonomy_node_parent_of_taxonomy_node_{source}")
    parents = Counter(e["child_id"] for e in edges)
    parent_of = {e["child_id"]: e["parent_id"] for e in edges}
    for nid, node in nodes.items():
        level = int(node["level"])
        test.assertIn(level, (1, 2, 3), f"{source} {nid} has level {level}")
        if level == 1:
            test.assertNotIn(nid, parents, f"{source} L1 node {nid} has a parent")
        else:
            test.assertEqual(parents[nid], 1, f"{source} {nid} needs exactly one parent")
            test.assertEqual(int(nodes[parent_of[nid]]["level"]), level - 1, f"{source} {nid} parent level")
    for level in (1, 2, 3):
        names = Counter(n["name"] for n in nodes.values() if n["level"] == str(level))
        test.assertEqual({n for n, c in names.items() if c > 1}, set(),
                         f"{source} reuses level-{level} names")
    return list(nodes.values())
