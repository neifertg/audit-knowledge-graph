"""Independent Python answers to every round, from the CSVs (E3 children c and d; 017, 018).

Reads the published files, `reconciled/` and round 5's register; never SQLite, Neo4j or the answer
key (INV-6). A query that returns everything, or the wrong thing, differs from these.
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

from .fourth_party import read_register
from .registry import REGISTER, STALE_CUTOFF


def read(folder: Path, name: str) -> list[dict]:
    with open(Path(folder) / f"{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def answers(out: Path, cutoff: str = STALE_CUTOFF, vendor: str | None = None, register=None) -> dict:
    """{round number or 'owners': rows}, plus helper tables the tests use."""
    out = Path(out)
    register = REGISTER if register is None else register
    both = lambda stem: read(out, stem + "_erm") + read(out, stem + "_ia")
    exposed, mitigates, mitigated_by = defaultdict(set), defaultdict(set), defaultdict(set)
    for r in both("auditable_entity_exposed_to_risk"):
        exposed[r["risk_id"]].add(r["auditable_entity_id"])
    for r in both("control_mitigates_risk"):
        mitigates[r["control_id"]].add(r["risk_id"])
        mitigated_by[r["risk_id"]].add(r["control_id"])
    owner = {r["auditable_entity_id"]: r["business_unit_id"] for r in read(out, "business_unit_owns_auditable_entity")}
    unit_name = {r["business_unit_id"]: r["name"] for r in read(out, "business_unit")}
    issues = read(out, "issue")
    reached_units = lambda control: {owner[e] for risk in mitigates[control] for e in exposed[risk]}

    # round 1: open issues by business unit and rating
    issue_risks = defaultdict(set)
    for r in both("issue_against_risk"):
        issue_risks[r["issue_id"]].add(r["risk_id"])
    open_by = defaultdict(set)
    for i in issues:
        if i["closed_date"] == "":
            for risk in issue_risks[i["issue_id"]]:
                for e in exposed[risk]:
                    open_by[(owner[e], i["rating"])].add(i["issue_id"])
    r1 = [(bu, unit_name[bu], rating, len(ids)) for (bu, rating), ids in open_by.items()]

    # round 2: High canonical risks with stale coverage
    rating = {r["risk_id"]: r["inherent_rating"] for r in both("risk")}
    end = {a["audit_id"]: a["end_date"] for a in read(out, "audit")}
    fresh = {t["control_id"] for t in read(out, "audit_tested_control_ia") if end[t["audit_id"]] >= cutoff}
    members = defaultdict(list)
    for m in read(out / "reconciled", "risk_maps_to_canonical"):
        members[m["canonical_risk_id"]].append((m["source"], m["risk_id"]))
    r2 = [(c, "Y" if any(s == "IA" for s, _ in mem) else "N") for c, mem in members.items()
          if any(rating[r] == "High" for _, r in mem)
          and not any(ctrl in fresh for _, r in mem for ctrl in mitigated_by[r])]

    # round 3: shared-system blast radius
    systems = read(out, "system")
    system_name = {s["system_id"]: s["name"] for s in systems}
    reach = defaultdict(set)
    for d in both("control_depends_on_system"):
        for risk in mitigates[d["control_id"]]:
            reach[d["system_id"]] |= exposed[risk]
    ranked = sorted(((s, system_name[s], len(es)) for s, es in reach.items() if es), key=lambda t: (-t[2], t[1]))

    # round 4: regulation-to-business-unit paths
    paths = Counter()
    for q in both("regulation_requires_control"):
        for risk in mitigates[q["control_id"]]:
            for e in exposed[risk]:
                paths[(q["regulation_id"], owner[e])] += 1
    r4 = [(g, bu, n) for (g, bu), n in paths.items()]

    # round 5: exposure to a vendor, directly or only through fourth parties
    from .fourth_party import most_relied_on, upstream
    vendor = vendor or most_relied_on(register)
    chain = upstream(vendor, register) | {vendor}
    vendor_of = {s["system_id"]: s["vendor"] for s in systems}
    process_systems = defaultdict(set)
    for r in read(out, "process_runs_on_system"):
        process_systems[r["process_id"]].add(r["system_id"])
    exposure = {}
    for p in read(out, "auditable_entity_performs_process"):
        for s in process_systems[p["process_id"]]:
            if vendor_of[s] == vendor:
                exposure[p["auditable_entity_id"]] = "direct"
            elif vendor_of[s] in chain:
                exposure.setdefault(p["auditable_entity_id"], "fourth_party_only")
    r5 = list(exposure.items())

    # round 6: IA controls with issues in two or more years, and all their issues
    issue = {i["issue_id"]: i for i in issues}
    by_control = defaultdict(list)
    for r in read(out, "issue_against_control_ia"):
        by_control[r["control_id"]].append(issue[r["issue_id"]])
    r6 = [(c, i["issue_id"], i["opened_date"], i["title"]) for c, group in by_control.items()
          if len({i["opened_date"][:4] for i in group}) >= 2 for i in group]

    # round 7: non-IA issues by ERM L1 and year
    parent = {r["child_id"]: r["parent_id"] for r in read(out, "taxonomy_node_parent_of_taxonomy_node_erm")}
    node_name = {n["taxonomy_node_id"]: n["name"] for n in read(out, "taxonomy_node_erm")}
    l3_of = {r["risk_id"]: r["taxonomy_node_id"] for r in read(out, "taxonomy_node_classifies_risk_erm")}
    counted = defaultdict(set)
    erm_risks = defaultdict(set)
    for r in read(out, "issue_against_risk_erm"):
        erm_risks[r["issue_id"]].add(r["risk_id"])
    for i in issues:
        if i["source"] != "IA":
            for risk in erm_risks[i["issue_id"]]:
                counted[(parent[parent[l3_of[risk]]], i["opened_date"][:4])].add(i["issue_id"])
    r7 = [(l1, node_name[l1], year, len(ids)) for (l1, year), ids in counted.items()]

    # owner concentration: key controls per person and the business units they reach
    key = {c["control_id"] for c in both("control") if c["key_control"] == "Y"}
    owned = defaultdict(set)
    for r in both("control_owned_by_person"):
        if r["control_id"] in key:
            owned[r["person_id"]].add(r["control_id"])
    owners = sorted(((p, len(cs), len(set().union(*(reached_units(c) for c in cs)))) for p, cs in owned.items()),
                    key=lambda t: (-t[1], -t[2], t[0]))[:10]

    return {1: r1, 2: r2, 3: ranked[:3], 4: r4, 5: r5, 6: r6, 7: r7, "owners": owners,
            "ranked_systems": ranked, "members": members, "mitigated_by": mitigated_by, "rating": rating}


def top_riser(rows) -> tuple | None:
    """Round 7's derived figure: the L1 with the largest 2025 minus 2023 increase (a missing year
    counts as 0), ties by node ID. Rows are (l1_node_id, l1_name, year, issues)."""
    by = defaultdict(dict)
    for node, name, year, n in rows:
        by[(node, name)][str(year)] = n
    if not by:
        return None
    (node, name), years = min(by.items(), key=lambda kv: (-(kv[1].get("2025", 0) - kv[1].get("2023", 0)), kv[0][0]))
    return {"l1_node_id": node, "l1_name": name, "2023": years.get("2023", 0), "2025": years.get("2025", 0)}


__all__ = ["answers", "read", "read_register", "top_riser"]
