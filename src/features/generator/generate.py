"""Build the synthetic bank in memory: published tables plus the answer key.

Nothing here writes files or touches the network; see writer.py and cli.py.
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from . import library as lib
from .names import load
from .rng import stream

SAMPLE_COUNTS = {
    "REGULATION": 8,
    "PERSON": 20,
    "AUDIT": 6,
    "ISSUE": 15,
    "RISK_ERM": 15,
    "RISK_IA": 15,
}
OVERRIDABLE = {"REGULATION", "PERSON", "AUDIT", "ISSUE"}
WINDOW_START = date(2023, 1, 1)
WINDOW_END = date(2025, 12, 31)


@dataclass
class Table:
    columns: list[str]
    rows: list[tuple] = field(default_factory=list)


@dataclass
class TextItem:
    """A description that AI text may replace, keyed by an internal key never published."""
    key: str
    file: str
    item_id: str
    column: str
    templated: str
    input_hash: str


@dataclass
class Dataset:
    tables: dict[str, Table]
    answer_key: dict[str, Table]
    text_items: list[TextItem]


class GenerationError(Exception):
    pass


def _ids(seed: int, name: str, prefix: str, n: int, lo: int, hi: int) -> list[str]:
    numbers = stream(seed, f"{name}/ids").sample(range(lo, hi), n)
    width = len(str(hi - 1))
    return [f"{prefix}{number:0{width}d}" for number in numbers]


def _hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _lc_first(text: str) -> str:
    if text[:1].isdigit() or text[:2].isupper():
        return text
    return text[:1].lower() + text[1:]


def build(seed: int = 42, counts: dict[str, int] | None = None, text: str = "templated",
          text_dir: Path | None = None) -> Dataset:
    n = dict(SAMPLE_COUNTS)
    for name, value in (counts or {}).items():
        if name not in OVERRIDABLE:
            raise GenerationError(f"--count {name} is fixed at sample size; overridable: {sorted(OVERRIDABLE)}")
        n[name] = value

    t: dict[str, Table] = {}
    key: dict[str, Table] = {}
    texts: list[TextItem] = []

    # --- organization ------------------------------------------------------------------
    seg_id = dict(zip(lib.SEGMENTS, _ids(seed, "segment", "SEG-", len(lib.SEGMENTS), 10, 100)))
    t["segment"] = Table(["segment_id", "name"], [(seg_id[s], s) for s in lib.SEGMENTS])

    bu_names = list(lib.BUSINESS_UNITS)
    bu_id = dict(zip(bu_names, _ids(seed, "business_unit", "BU-", len(bu_names), 100, 1000)))
    t["business_unit"] = Table(["business_unit_id", "name"], [(bu_id[b], b) for b in bu_names])
    t["segment_has_business_unit"] = Table(
        ["segment_id", "business_unit_id"],
        [(seg_id[s], bu_id[b]) for b, s in lib.BUSINESS_UNITS.items()])

    ae_names = list(lib.AUDITABLE_ENTITIES)
    ae_id = dict(zip(ae_names, _ids(seed, "auditable_entity", "AE-", len(ae_names), 100, 1000)))
    t["auditable_entity"] = Table(["auditable_entity_id", "name"], [(ae_id[a], a) for a in ae_names])
    t["business_unit_owns_auditable_entity"] = Table(
        ["business_unit_id", "auditable_entity_id"],
        [(bu_id[b], ae_id[a]) for a, b in lib.AUDITABLE_ENTITIES.items()])

    system_names = list(load("systems"))
    sys_id = dict(zip(system_names, _ids(seed, "system", "SYS-", len(system_names), 100, 1000)))
    t["system"] = Table(
        ["system_id", "name", "vendor", "criticality"],
        [(sys_id[s], s, *lib.SYSTEMS[s]) for s in system_names])

    proc_names = list(lib.PROCESSES)
    proc_id = dict(zip(proc_names, _ids(seed, "process", "PRC-", len(proc_names), 100, 1000)))
    t["process"] = Table(["process_id", "name"], [(proc_id[p], p) for p in proc_names])
    t["auditable_entity_performs_process"] = Table(
        ["auditable_entity_id", "process_id"],
        [(ae_id[a], proc_id[p]) for p, (a, _) in lib.PROCESSES.items()])
    t["process_runs_on_system"] = Table(
        ["process_id", "system_id"],
        [(proc_id[p], sys_id[s]) for p, (_, systems) in lib.PROCESSES.items() for s in systems])

    # --- people ------------------------------------------------------------------------
    rng = stream(seed, "person")
    pairs = [(f, l) for f in load("first_names") for l in load("last_names")]
    if n["PERSON"] > len(pairs):
        raise GenerationError("not enough name combinations for --count PERSON")
    people = [f"{f} {l}" for f, l in rng.sample(pairs, n["PERSON"])]
    titles = list(load("titles"))
    person_titles = [titles[i % len(titles)] for i in range(len(people))]
    person_ids = _ids(seed, "person", "P-", len(people), 1000, 10000)
    t["person"] = Table(["person_id", "name", "title"], list(zip(person_ids, people, person_titles)))

    # --- regulations -------------------------------------------------------------------
    reg_names = list(load("regulations"))
    if n["REGULATION"] > len(reg_names):
        raise GenerationError(f"--count REGULATION is at most {len(reg_names)}")
    reg_names = reg_names[: n["REGULATION"]]
    reg_id = dict(zip(reg_names, _ids(seed, "regulation", "REG-", len(reg_names), 100, 1000)))
    t["regulation"] = Table(
        ["regulation_id", "name", "citation"],
        [(reg_id[r], r, lib.REGULATIONS[r]) for r in reg_names])

    # --- taxonomies --------------------------------------------------------------------
    def taxonomy(source: str, paths: list, prefix: str, lo: int, hi: int) -> dict:
        nodes, parents = [], []
        for path in paths:
            for level in range(1, 4):
                node = (level, path[level - 1])
                if node not in nodes:
                    nodes.append(node)
                    if level > 1:
                        parents.append(((level - 1, path[level - 2]), node))
        ids = dict(zip(nodes, _ids(seed, f"taxonomy_node_{source}", prefix, len(nodes), lo, hi)))
        t[f"taxonomy_node_{source}"] = Table(
            ["taxonomy_node_id", "level", "name"], [(ids[node], node[0], node[1]) for node in nodes])
        t[f"taxonomy_node_parent_of_taxonomy_node_{source}"] = Table(
            ["parent_id", "child_id"], [(ids[p], ids[c]) for p, c in parents])
        return ids

    erm_node = taxonomy("erm", lib.ERM_TAXONOMY, "ERMT-", 100, 1000)
    ia_node = taxonomy("ia", lib.IA_TAXONOMY, "IAT-", 100, 1000)
    erm_path = {path[2]: path for path in lib.ERM_TAXONOMY}

    def misfiled(concept: lib.RiskConcept) -> bool:
        target = lib.IA_TO_ERM[(3, concept.ia_l3)]
        path = erm_path[concept.erm_l3]
        return target is None or path[target[0] - 1] != target[1]

    # --- risk populations --------------------------------------------------------------
    rng = stream(seed, "risk_population")
    concepts = list(lib.RISK_CONCEPTS)
    rng.shuffle(concepts)
    n_shared = round(0.6 * n["RISK_IA"])
    n_dup = max(1, round(0.07 * n["RISK_ERM"]))
    n_erm_only = n["RISK_ERM"] - n_shared - n_dup
    n_ia_only = n["RISK_IA"] - n_shared
    if n_shared + n_erm_only + n_ia_only > len(concepts):
        raise GenerationError("risk concept library too small for the requested sizes")
    shared = concepts[:n_shared]
    erm_only = concepts[n_shared:n_shared + n_erm_only]
    ia_only = concepts[n_shared + n_erm_only:n_shared + n_erm_only + n_ia_only]
    unused = concepts[n_shared + n_erm_only + n_ia_only:]
    if not any(misfiled(c) for c in shared + ia_only):  # the sample must show at least one
        swap = next((i for i, c in enumerate(unused) if misfiled(c)), None)
        if swap is not None and ia_only:
            ia_only[-1], unused[swap] = unused[swap], ia_only[-1]
    duplicated = rng.sample(shared, n_dup)
    erm_concepts = sorted(shared + erm_only, key=lambda c: c.key)
    ia_concepts = sorted(shared + ia_only, key=lambda c: c.key)

    # ERM risks: (concept, ordinal); ordinal 1 is a within-ERM duplicate in other words.
    rng = stream(seed, "risk_erm")
    erm_items = [(c, 0) for c in erm_concepts] + [(c, 1) for c in sorted(duplicated, key=lambda c: c.key)]
    variant = {c.key: rng.randrange(len(lib.ERM_RISK_TEMPLATES)) for c in erm_concepts}
    erm_risk_ids = _ids(seed, "risk_erm", "ERM-R", len(erm_items), 1000, 5000)
    erm_risk = {}  # (concept key, ordinal) -> id
    rows = []
    for (c, k), rid in zip(erm_items, erm_risk_ids):
        v = variant[c.key] if k == 0 else 1 - variant[c.key]
        phrase, title = (c.erm, c.erm_title) if k == 0 else (c.alt, c.alt_title)
        desc = lib.ERM_RISK_TEMPLATES[v].format(phrase=phrase, cause=c.cause, impact=c.impact,
                                                Impact=_cap(c.impact))
        erm_risk[(c.key, k)] = rid
        rows.append((rid, title, desc, c.rating))
        texts.append(TextItem(f"risk_erm:{c.key}:{k}", "risk_erm", rid, "description", desc,
                              _hash("risk_erm", c.key, str(k), title, desc)))
    t["risk_erm"] = Table(["risk_id", "title", "description", "inherent_rating"], rows)

    rng = stream(seed, "risk_ia")
    ia_risk_ids = _ids(seed, "risk_ia", "IAR-", len(ia_concepts), 5000, 10000)
    ia_risk = {}
    rows = []
    for c, rid in zip(ia_concepts, ia_risk_ids):
        v = rng.randrange(len(lib.IA_RISK_TEMPLATES))
        desc = lib.IA_RISK_TEMPLATES[v].format(area=c.ia_l3, title=c.ia_title, focus=c.ia_focus)
        rating = c.rating
        if rng.random() < 0.25:  # IA's own assessment differs by one notch
            i = lib.RATINGS.index(c.rating)
            rating = lib.RATINGS[i + 1 if i == 0 else i - 1]
        ia_risk[c.key] = rid
        rows.append((rid, c.ia_title, desc, rating))
        texts.append(TextItem(f"risk_ia:{c.key}", "risk_ia", rid, "description", desc,
                              _hash("risk_ia", c.key, c.ia_title, desc)))
    t["risk_ia"] = Table(["risk_id", "title", "description", "inherent_rating"], rows)

    t["taxonomy_node_classifies_risk_erm"] = Table(
        ["taxonomy_node_id", "risk_id"],
        [(erm_node[(3, c.erm_l3)], rid) for (c, _), rid in zip(erm_items, erm_risk_ids)])
    t["taxonomy_node_classifies_risk_ia"] = Table(
        ["taxonomy_node_id", "risk_id"], [(ia_node[(3, c.ia_l3)], ia_risk[c.key]) for c in ia_concepts])
    t["auditable_entity_exposed_to_risk_erm"] = Table(
        ["auditable_entity_id", "risk_id"],
        [(ae_id[a], rid) for (c, _), rid in zip(erm_items, erm_risk_ids) for a in c.entities])
    t["auditable_entity_exposed_to_risk_ia"] = Table(
        ["auditable_entity_id", "risk_id"],
        [(ae_id[a], ia_risk[c.key]) for c in ia_concepts for a in c.entities])

    # --- controls ----------------------------------------------------------------------
    # One control per concept in each source. An ERM control for a concept ERM does not
    # hold as a risk mitigates nothing: an orphan control (built-in messiness).
    orphans = sorted(unused[:1], key=lambda c: c.key)
    erm_ctrl_concepts = sorted(erm_concepts + orphans, key=lambda c: c.key)
    erm_ctrl = dict(zip([c.key for c in erm_ctrl_concepts],
                        _ids(seed, "control_erm", "ERM-C", len(erm_ctrl_concepts), 1000, 5000)))
    ia_ctrl = dict(zip([c.key for c in ia_concepts],
                       _ids(seed, "control_ia", "IAC-", len(ia_concepts), 5000, 10000)))
    columns = ["control_id", "title", "description", "control_type", "nature", "frequency", "key_control"]
    rows = []
    for c in erm_ctrl_concepts:
        cc = c.control
        rows.append((erm_ctrl[c.key], cc.erm_title, cc.erm, cc.control_type, cc.nature, cc.frequency,
                     "Y" if c.rating == "High" else "N"))
        texts.append(TextItem(f"control_erm:{c.key}", "control_erm", erm_ctrl[c.key], "description", cc.erm,
                              _hash("control_erm", c.key, cc.erm_title, cc.erm)))
    t["control_erm"] = Table(columns, rows)
    rng = stream(seed, "control_ia")
    rows = []
    for c in ia_concepts:
        cc = c.control
        rows.append((ia_ctrl[c.key], cc.ia_title, cc.ia, cc.control_type, cc.nature, cc.frequency,
                     "Y" if rng.random() < 0.7 else "N"))
        texts.append(TextItem(f"control_ia:{c.key}", "control_ia", ia_ctrl[c.key], "description", cc.ia,
                              _hash("control_ia", c.key, cc.ia_title, cc.ia)))
    t["control_ia"] = Table(columns, rows)

    t["control_mitigates_risk_erm"] = Table(
        ["control_id", "risk_id"],
        [(erm_ctrl[c.key], rid) for (c, _), rid in zip(erm_items, erm_risk_ids)])
    t["control_mitigates_risk_ia"] = Table(
        ["control_id", "risk_id"], [(ia_ctrl[c.key], ia_risk[c.key]) for c in ia_concepts])
    for source, ctrl, cs in (("erm", erm_ctrl, erm_ctrl_concepts), ("ia", ia_ctrl, ia_concepts)):
        t[f"control_depends_on_system_{source}"] = Table(
            ["control_id", "system_id"],
            [(ctrl[c.key], sys_id[s]) for c in cs for s in c.control.systems])
        t[f"regulation_requires_control_{source}"] = Table(
            ["regulation_id", "control_id"],
            [(reg_id[c.control.regulation], ctrl[c.key]) for c in cs if c.control.regulation in reg_id])

    rng = stream(seed, "control_owned_by_person_erm")
    erm_owner = {c.key: rng.choice(person_ids) for c in erm_ctrl_concepts}
    rng = stream(seed, "control_owned_by_person_ia")
    ia_owner = {c.key: rng.choice([p for p in person_ids if p != erm_owner.get(c.key)]) for c in ia_concepts}
    t["control_owned_by_person_erm"] = Table(
        ["control_id", "person_id"], [(erm_ctrl[k], p) for k, p in erm_owner.items()])
    t["control_owned_by_person_ia"] = Table(
        ["control_id", "person_id"], [(ia_ctrl[k], p) for k, p in ia_owner.items()])

    # --- audits (IA tests IA controls only) --------------------------------------------
    rng = stream(seed, "audit")
    ia_controls_for_ae: dict[str, list[str]] = {}
    for c in ia_concepts:
        for a in c.entities:
            ia_controls_for_ae.setdefault(a, []).append(c.key)
    candidates = sorted(ia_controls_for_ae)
    audit_ids = _ids(seed, "audit", "AUD-", n["AUDIT"], 100, 1000)
    audits, covered, tested = [], [], []
    audit_info = []  # (audit id, end date, tested concept keys)
    for i, aid in enumerate(audit_ids):
        year = 2023 + i % 3
        scope = sorted(rng.sample(candidates, rng.choice([1, 1, 2])))
        start = date(year, rng.randint(1, 10), rng.randint(1, 28))
        end = start + timedelta(days=rng.randint(30, 60))
        keys = sorted({k for a in scope for k in ia_controls_for_ae[a]})
        title = f"{' and '.join(scope)} Audit {year}"
        audits.append((aid, title, year, start.isoformat(), end.isoformat(), rng.choice(lib.AUDIT_RATINGS)))
        covered += [(aid, ae_id[a]) for a in scope]
        tested += [(aid, ia_ctrl[k]) for k in keys]
        audit_info.append((aid, end, keys))
    t["audit"] = Table(["audit_id", "title", "audit_year", "start_date", "end_date", "rating"], audits)
    t["audit_covered_auditable_entity"] = Table(["audit_id", "auditable_entity_id"], covered)
    t["audit_tested_control_ia"] = Table(["audit_id", "control_id"], tested)

    # --- issues ------------------------------------------------------------------------
    rng = stream(seed, "issue")
    by_key = {c.key: c for c in lib.RISK_CONCEPTS}
    n_issues = n["ISSUE"]
    n_ia_issues = max(1, round(0.5 * n_issues)) if n_issues else 0
    sources = ["IA"] * n_ia_issues + [lib.ISSUE_SOURCES[1 + i % 3] for i in range(n_issues - n_ia_issues)]
    issue_ids = _ids(seed, "issue", "ISS-", n_issues, 1000, 10000)
    erm_mitigated = [c.key for c in erm_concepts]
    issues, raised, against_c, against_r, owned = [], [], {"erm": [], "ia": []}, {"erm": [], "ia": []}, []
    for j, (iid, source) in enumerate(zip(issue_ids, sources)):
        if source == "IA":
            aid, audit_end, keys = rng.choice(audit_info)
            k = rng.choice(keys)
            opened = audit_end + timedelta(days=rng.randint(0, 20))
            raised.append((aid, iid))
            against_c["ia"].append((iid, ia_ctrl[k]))
            against_r["ia"].append((iid, ia_risk[k]))
        else:
            k = rng.choice(erm_mitigated)
            opened = WINDOW_START + timedelta(days=rng.randint(0, (WINDOW_END - WINDOW_START).days - 60))
            ordinal = rng.choice([o for o in (0, 1) if (k, o) in erm_risk])
            against_c["erm"].append((iid, erm_ctrl[k]))
            against_r["erm"].append((iid, erm_risk[(k, ordinal)]))
        c = by_key[k]
        title_t, desc_t = lib.ISSUE_TEMPLATES[source]
        fields = {"ia_title": c.control.ia_title, "erm_title": c.control.erm_title,
                  "finding": c.control.finding, "finding_lc": _lc_first(c.control.finding)}
        title, desc = title_t.format(**fields), desc_t.format(**fields)
        closed = ""
        if rng.random() < 0.6:
            close_date = opened + timedelta(days=rng.randint(30, 200))
            if close_date <= WINDOW_END:
                closed = close_date.isoformat()
        rating = rng.choices(lib.RATINGS, weights=[2, 5, 3])[0]
        issues.append((iid, title, desc, source, rating, opened.isoformat(), closed))
        owned.append((iid, rng.choice(person_ids)))
        texts.append(TextItem(f"issue:{j}", "issue", iid, "description", desc,
                              _hash("issue", str(j), source, k, title, desc)))
    t["issue"] = Table(["issue_id", "title", "description", "source", "rating", "opened_date", "closed_date"],
                       issues)
    t["audit_raised_issue"] = Table(["audit_id", "issue_id"], raised)
    for source in ("erm", "ia"):
        t[f"issue_against_control_{source}"] = Table(["issue_id", "control_id"], against_c[source])
        t[f"issue_against_risk_{source}"] = Table(["issue_id", "risk_id"], against_r[source])
    t["issue_owned_by_person"] = Table(["issue_id", "person_id"], owned)

    # --- answer key --------------------------------------------------------------------
    erm_by_level_name = {node: nid for node, nid in erm_node.items()}
    key["taxonomy_map"] = Table(
        ["ia_node_id", "erm_node_id"],
        [(nid, erm_by_level_name[lib.IA_TO_ERM[node]] if lib.IA_TO_ERM[node] else "unmapped")
         for node, nid in ia_node.items()])

    risk_count: dict[str, int] = {}
    for c, _ in erm_items:
        risk_count[c.key] = risk_count.get(c.key, 0) + 1
    for c in ia_concepts:
        risk_count[c.key] = risk_count.get(c.key, 0) + 1
    risk_cluster = {k: f"RC-{i:03d}" for i, k in enumerate(sorted(k for k, v in risk_count.items() if v > 1), 1)}
    key["risk_clusters"] = Table(
        ["source", "risk_id", "cluster_id", "true_erm_node_id"],
        [("ERM", rid, risk_cluster.get(c.key, "none"), erm_node[(3, c.erm_l3)])
         for (c, _), rid in zip(erm_items, erm_risk_ids)]
        + [("IA", ia_risk[c.key], risk_cluster.get(c.key, "none"), erm_node[(3, c.erm_l3)])
           for c in ia_concepts])

    in_both = set(erm_ctrl) & set(ia_ctrl)
    control_cluster = {k: f"CC-{i:03d}" for i, k in enumerate(sorted(in_both), 1)}
    key["control_clusters"] = Table(
        ["source", "control_id", "cluster_id"],
        [("ERM", cid, control_cluster.get(k, "none")) for k, cid in erm_ctrl.items()]
        + [("IA", cid, control_cluster.get(k, "none")) for k, cid in ia_ctrl.items()])
    key["scenarios"] = Table(["scenario", "item_id"], [])

    for table in list(t.values()) + list(key.values()):
        table.rows.sort()

    if text == "ai":
        _apply_ai_text(t, texts, text_dir)
    return Dataset(t, key, texts)


AI_TEXT_FILE = "ai_text.jsonl"


def load_ai_text(text_dir: Path) -> dict[str, dict]:
    path = Path(text_dir) / AI_TEXT_FILE
    if not path.exists():
        raise GenerationError(f"no committed AI text at {path}; run write_text.py first")
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            entries[entry["key"]] = entry
    return entries


def _apply_ai_text(tables: dict[str, Table], texts: list[TextItem], text_dir: Path | None) -> None:
    if text_dir is None:
        raise GenerationError("--text ai needs --text-dir")
    entries = load_ai_text(text_dir)
    replacement: dict[tuple[str, str], str] = {}
    for item in texts:
        entry = entries.get(item.key)
        if entry is None:
            raise GenerationError(f"AI text missing for key {item.key}")
        if entry["input_hash"] != item.input_hash:
            raise GenerationError(f"AI text is stale for key {item.key}: its inputs changed; regenerate it")
        replacement[(item.file, item.item_id)] = entry["text"]
    for name, table in tables.items():
        if "description" not in table.columns:
            continue
        col = table.columns.index("description")
        table.rows = [row[:col] + (replacement.get((name, row[0]), row[col]),) + row[col + 1:]
                      for row in table.rows]


def orphan_ai_keys(dataset: Dataset, text_dir: Path) -> list[str]:
    """Committed AI text keys that no generated item uses."""
    used = {item.key for item in dataset.text_items}
    return sorted(k for k in load_ai_text(text_dir) if k not in used)
