"""Check logic shared by tests at sample and full size, so each rule is written once."""
import csv
import re
import statistics
from collections import Counter, defaultdict

from .dictionary import TYPES, denied_in, name_list, parse
from .helpers import answer_key, cosine_by_id, read, sentences, tables

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


def clusters(rows: list[dict], id_col: str) -> dict[str, list[dict]]:
    grouped = defaultdict(list)
    for row in rows:
        if row["cluster_id"] != "none":
            grouped[row["cluster_id"]].append(row)
    return grouped


def hard_negative_exists(out, kind: str, cluster_rows: list[dict]) -> bool:
    id_col = f"{kind}_id"
    erm, ia = read(out, f"{kind}_erm"), read(out, f"{kind}_ia")
    sims = cosine_by_id(erm, ia, id_col)
    cluster_of = {r[id_col]: r["cluster_id"] for r in cluster_rows}
    same = lambda a, b: cluster_of[a] != "none" and cluster_of[a] == cluster_of[b]
    pairs = [(e[id_col], i[id_col]) for e in erm for i in ia]
    matched = [sims[p] for p in pairs if same(*p)]
    median = statistics.median(matched)
    return any(sims[p] >= median for p in pairs if not same(*p))


def answer_key_rules(test, out) -> None:
    """005 AC-2: the answer key is consistent and holds every reconciliation case (any size)."""
    erm_nodes = {r["taxonomy_node_id"]: r for r in read(out, "taxonomy_node_erm")}
    ia_nodes = {r["taxonomy_node_id"]: r for r in read(out, "taxonomy_node_ia")}
    erm_parent = {r["child_id"]: r["parent_id"] for r in read(out, "taxonomy_node_parent_of_taxonomy_node_erm")}

    # taxonomy map: every IA node exactly once, valid targets at allowed levels
    target = taxonomy_map(test, out)
    test.assertGreaterEqual(sum(t is None for t in target.values()), 1, "no unmapped IA node")

    # risk clusters: every risk exactly once, true node an ERM L3, clusters share a node
    risks = {("ERM", r["risk_id"]) for r in read(out, "risk_erm")} | {("IA", r["risk_id"]) for r in read(out, "risk_ia")}
    rc = answer_key(out, "risk_clusters")
    test.assertEqual(sorted((r["source"], r["risk_id"]) for r in rc), sorted(risks))
    for row in rc:
        test.assertEqual(erm_nodes[row["true_erm_node_id"]]["level"], "3")
    risk_clusters = clusters(rc, "risk_id")
    for members in risk_clusters.values():
        test.assertEqual(len({m["true_erm_node_id"] for m in members}), 1, "cluster spans ERM nodes")
    cross = [m for m in risk_clusters.values() if {x["source"] for x in m} == {"ERM", "IA"}]
    dup = [m for m in risk_clusters.values() if sum(x["source"] == "ERM" for x in m) >= 2]
    test.assertGreaterEqual(len(cross), 5, "fewer than 5 cross-source risk matches")
    test.assertGreaterEqual(len(dup), 1, "no within-ERM duplicate")

    # misfiled IA risk: true node not under its IA node's mapped target
    ia_node_of = {r["risk_id"]: r["taxonomy_node_id"] for r in read(out, "taxonomy_node_classifies_risk_ia")}

    def ancestors(node):
        chain = [node]
        while chain[-1] in erm_parent:
            chain.append(erm_parent[chain[-1]])
        return chain

    misfiled = [r for r in rc if r["source"] == "IA"
                and target[ia_node_of[r["risk_id"]]] not in ancestors(r["true_erm_node_id"])]
    test.assertGreaterEqual(len(misfiled), 1, "no misfiled IA risk")

    # control clusters: every control exactly once, at least 5 cross-source matches
    controls = {("ERM", r["control_id"]) for r in read(out, "control_erm")} | {("IA", r["control_id"]) for r in read(out, "control_ia")}
    cc = answer_key(out, "control_clusters")
    test.assertEqual(sorted((r["source"], r["control_id"]) for r in cc), sorted(controls))
    cross_c = [m for m in clusters(cc, "control_id").values() if {x["source"] for x in m} == {"ERM", "IA"}]
    test.assertGreaterEqual(len(cross_c), 5, "fewer than 5 cross-source control matches")

    # scenarios: empty at sample size; at full size child d writes shared_system rows (e appends more)
    known_ids = {r[f"{k}_id"] for k in ("system", "risk", "control", "issue", "audit", "auditable_entity")
                 for name in ([k] if k in ("system", "issue", "audit", "auditable_entity") else [f"{k}_erm", f"{k}_ia"])
                 for r in read(out, name)}
    for row in answer_key(out, "scenarios"):
        test.assertIn(row["item_id"], known_ids, f"scenario {row['scenario']} names an unknown item")
    test.assertTrue(hard_negative_exists(out, "risk", rc), "no hard negative among risks")
    test.assertTrue(hard_negative_exists(out, "control", cc), "no hard negative among controls")


def spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        r = [0.0] * len(values)
        for rank, i in enumerate(order):
            r[i] = float(rank)
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    var = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return cov / var if var else 0.0


def leakage(test, out, kind: str) -> None:
    """005 AC-7: matched items share no ID number, sentence, near-copy text, attributes or order."""
    id_col = f"{kind}_id"
    erm, ia = read(out, f"{kind}_erm"), read(out, f"{kind}_ia")
    by_id = {r[id_col]: r for r in erm + ia}
    position = {r[id_col]: i for rows in (erm, ia) for i, r in enumerate(rows)}
    sims = cosine_by_id(erm, ia, id_col)

    members = defaultdict(list)
    for row in answer_key(out, f"{kind}_clusters"):
        if row["cluster_id"] != "none":
            members[row["cluster_id"]].append((row["source"], row[id_col]))

    owner = {}
    if kind == "control":
        for source in ("erm", "ia"):
            owner.update({r["control_id"]: r["person_id"] for r in read(out, f"control_owned_by_person_{source}")})

    pair_sims = []
    for cluster, items in members.items():
        for i, (source_a, a) in enumerate(items):
            for source_b, b in items[i + 1:]:
                if source_a == source_b == "IA":
                    # Two IA documents of one enterprise control (008: one ERM control, several IA
                    # controls per cluster) are copies of each other by design; leakage concerns the
                    # pairs a matcher must find: ERM to IA, and ERM duplicates.
                    continue
                test.assertFalse(set(re.findall(r"\d+", a)) & set(re.findall(r"\d+", b)),
                                 f"{a} and {b} share an ID number")
                shared = sentences(by_id[a]["description"]) & sentences(by_id[b]["description"])
                test.assertFalse(shared, f"{a} and {b} share a sentence: {shared}")
                test.assertLess(sims[(a, b)], 0.90, f"{a} and {b} are near-copies")
                pair_sims.append(sims[(a, b)])
                if kind == "control":
                    ra, rb = by_id[a], by_id[b]
                    same = (owner[a] == owner[b], ra["frequency"] == rb["frequency"],
                            ra["control_type"] == rb["control_type"])
                    test.assertFalse(all(same), f"{a} and {b} have identical owner, frequency and type")
    test.assertLess(statistics.median(pair_sims), 0.70)

    cross = [items for items in members.values() if {s for s, _ in items} == {"ERM", "IA"}]
    erm_pos = [min(position[i] for s, i in items if s == "ERM") for items in cross]
    ia_pos = [min(position[i] for s, i in items if s == "IA") for items in cross]
    test.assertLess(abs(spearman(erm_pos, ia_pos)), 0.8, "matched items sit in the same order in both files")
