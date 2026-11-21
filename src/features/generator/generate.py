"""Build the synthetic bank in memory: published tables plus the answer key.

Nothing here writes files or touches the network; see writer.py and cli.py.
"""
import hashlib
import json
from collections import defaultdict
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
FULL_COUNTS = {
    **SAMPLE_COUNTS,
    "REGULATION": 15,
    "PERSON": 120,
    "RISK_ERM": 180,  # child c (007)
    "RISK_IA": 150,
    "AUDIT": 75,      # child e (009)
    "ISSUE": 250,
}
SIZES = {"sample", "full"}
SAMPLE_NAME_POOL = 30   # sample mode draws people from the first 30 first and last names
SAMPLE_TITLE_POOL = 20  # and cycles through the first 20 titles
OVERRIDABLE = {"REGULATION", "PERSON", "AUDIT", "ISSUE", "RISK_ERM", "RISK_IA"}
STALE_LINK_RATE = 0.35  # share of full-size ERM risks with one stale exposure link
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
          text_dir: Path | None = None, size: str = "sample") -> Dataset:
    if size not in SIZES:
        raise GenerationError(f"unknown size {size}; choose from {sorted(SIZES)}")
    full = size == "full"
    if full and text == "ai":
        # AC-9 (006): sample AI text must never leak into a full-size build. Children c-e
        # narrow this guard as they add full-size AI text, and e removes it.
        raise GenerationError("AI-written text exists only at sample size so far (children c-e add it at full "
                              "size); build full size with --text templated")
    n = dict(FULL_COUNTS if full else SAMPLE_COUNTS)
    for name, value in (counts or {}).items():
        if name not in OVERRIDABLE:
            raise GenerationError(f"--count {name} is fixed; overridable: {sorted(OVERRIDABLE)}")
        n[name] = value

    t: dict[str, Table] = {}
    key: dict[str, Table] = {}
    texts: list[TextItem] = []

    # --- organization ------------------------------------------------------------------
    # Full size reads the FULL_* structures; sample reads the original ones, so sample
    # output does not change when full-size content is added.
    business_units = lib.FULL_BUSINESS_UNITS if full else lib.BUSINESS_UNITS
    entities = lib.FULL_AUDITABLE_ENTITIES if full else lib.AUDITABLE_ENTITIES
    processes = lib.FULL_PROCESSES if full else lib.PROCESSES
    systems_info = lib.FULL_SYSTEMS if full else lib.SYSTEMS

    seg_id = dict(zip(lib.SEGMENTS, _ids(seed, "segment", "SEG-", len(lib.SEGMENTS), 10, 100)))
    t["segment"] = Table(["segment_id", "name"], [(seg_id[s], s) for s in lib.SEGMENTS])

    bu_names = list(business_units)
    bu_id = dict(zip(bu_names, _ids(seed, "business_unit", "BU-", len(bu_names), 100, 1000)))
    t["business_unit"] = Table(["business_unit_id", "name"], [(bu_id[b], b) for b in bu_names])
    t["segment_has_business_unit"] = Table(
        ["segment_id", "business_unit_id"],
        [(seg_id[s], bu_id[b]) for b, s in business_units.items()])

    ae_names = list(entities)
    ae_id = dict(zip(ae_names, _ids(seed, "auditable_entity", "AE-", len(ae_names), 100, 1000)))
    t["auditable_entity"] = Table(["auditable_entity_id", "name"], [(ae_id[a], a) for a in ae_names])
    t["business_unit_owns_auditable_entity"] = Table(
        ["business_unit_id", "auditable_entity_id"],
        [(bu_id[b], ae_id[a]) for a, b in entities.items()])

    system_names = [s for s in load("systems") if s in systems_info]
    sys_id = dict(zip(system_names, _ids(seed, "system", "SYS-", len(system_names), 100, 1000)))
    t["system"] = Table(
        ["system_id", "name", "vendor", "criticality"],
        [(sys_id[s], s, *systems_info[s]) for s in system_names])

    proc_names = list(processes)
    proc_id = dict(zip(proc_names, _ids(seed, "process", "PRC-", len(proc_names), 100, 1000)))
    t["process"] = Table(["process_id", "name"], [(proc_id[p], p) for p in proc_names])
    t["auditable_entity_performs_process"] = Table(
        ["auditable_entity_id", "process_id"],
        [(ae_id[a], proc_id[p]) for p, (a, _) in processes.items()])
    t["process_runs_on_system"] = Table(
        ["process_id", "system_id"],
        [(proc_id[p], sys_id[s]) for p, (_, systems) in processes.items() for s in systems])

    # --- people ------------------------------------------------------------------------
    rng = stream(seed, "person")
    pool = None if full else SAMPLE_NAME_POOL
    pairs = [(f, l) for f in load("first_names")[:pool] for l in load("last_names")[:pool]]
    if n["PERSON"] > len(pairs):
        raise GenerationError("not enough name combinations for --count PERSON")
    people = [f"{f} {l}" for f, l in rng.sample(pairs, n["PERSON"])]
    titles = list(load("titles"))
    if full:
        # one-per-bank titles (C-suite, heads, Treasurer, Controller...) go to exactly one person each
        unique = [x for x in titles if lib.one_per_bank(x)]
        repeatable = [x for x in titles if not lib.one_per_bank(x)]
        if len(people) < len(unique):
            raise GenerationError(f"--count PERSON must be at least {len(unique)} at full size")
        trng = stream(seed, "person/titles")
        person_titles = unique + [trng.choice(repeatable) for _ in range(len(people) - len(unique))]
        trng.shuffle(person_titles)
    else:
        person_titles = [titles[i % SAMPLE_TITLE_POOL] for i in range(len(people))]
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
        [(reg_id[r], r, lib.FULL_REGULATIONS[r]) for r in reg_names])

    # --- taxonomies --------------------------------------------------------------------
    def taxonomy(source: str, paths: list, prefix: str, lo: int, hi: int) -> dict:
        nodes, parents, seen_parent = [], [], {}
        for path in paths:
            for level in range(1, 4):
                node = (level, path[level - 1])
                parent = (level - 1, path[level - 2]) if level > 1 else None
                if node not in nodes:
                    nodes.append(node)
                    seen_parent[node] = parent
                    if parent:
                        parents.append((parent, node))
                elif seen_parent[node] != parent:
                    # nodes are keyed by (level, name): a name reused at one level would merge branches
                    raise GenerationError(f"{source} taxonomy reuses level-{level} name {node[1]!r}")
        ids = dict(zip(nodes, _ids(seed, f"taxonomy_node_{source}", prefix, len(nodes), lo, hi)))
        t[f"taxonomy_node_{source}"] = Table(
            ["taxonomy_node_id", "level", "name"], [(ids[node], node[0], node[1]) for node in nodes])
        t[f"taxonomy_node_parent_of_taxonomy_node_{source}"] = Table(
            ["parent_id", "child_id"], [(ids[p], ids[c]) for p, c in parents])
        return ids

    erm_paths = lib.FULL_ERM_TAXONOMY if full else lib.ERM_TAXONOMY
    erm_node = taxonomy("erm", erm_paths, "ERMT-", 100, 1000)
    ia_node = taxonomy("ia", lib.FULL_IA_TAXONOMY if full else lib.IA_TAXONOMY, "IAT-", 100, 1000)
    erm_path = {path[2]: path for path in erm_paths}
    ia_to_erm = lib.FULL_IA_TO_ERM  # a superset; sample nodes map exactly as before

    def misfiled(concept: lib.RiskConcept) -> bool:
        target = ia_to_erm[(3, concept.ia_l3)]
        path = erm_path[concept.erm_l3]
        return target is None or path[target[0] - 1] != target[1]

    # --- risk populations --------------------------------------------------------------
    rng = stream(seed, "risk_population")
    concepts = lib.full_instances() if full else list(lib.RISK_CONCEPTS)
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
    # Full size: a theme's inherent rating varies by where it occurs (own stream, L-005).
    rating_of = {c.key: c.rating for c in concepts}
    if full:
        rrng = stream(seed, "risk_rating")
        for c in sorted(concepts, key=lambda c: c.key):
            draw = rrng.random()
            if c.rating == "High" and draw < 0.5:
                rating_of[c.key] = "Medium"
            elif c.rating == "Medium" and draw < 0.42:
                rating_of[c.key] = "Low"
            elif c.rating == "Medium" and draw > 0.9:
                rating_of[c.key] = "High"
            elif c.rating == "Low" and draw < 0.2:
                rating_of[c.key] = "Medium"
    ia_concepts = sorted(shared + ia_only, key=lambda c: c.key)

    # ERM risks: (concept, ordinal); ordinal 1 is a within-ERM duplicate in other words.
    rng = stream(seed, "risk_erm")
    erm_items = [(c, 0) for c in erm_concepts] + [(c, 1) for c in sorted(duplicated, key=lambda c: c.key)]
    erm_templates = lib.FULL_ERM_RISK_TEMPLATES if full else lib.ERM_RISK_TEMPLATES
    variant = {c.key: rng.randrange(len(erm_templates)) for c in erm_concepts}
    # full size: each team states the risk in the main or the alternative wording
    use_alt = {c.key: rng.random() < 0.5 for c in erm_concepts} if full else {}
    erm_risk_ids = _ids(seed, "risk_erm", "ERM-R", len(erm_items), 1000, 5000)
    erm_risk = {}  # (concept key, ordinal) -> id
    rows = []
    for (c, k), rid in zip(erm_items, erm_risk_ids):
        # sample: a duplicate uses the other template; full size: the same one-sentence frame
        v = variant[c.key] if k == 0 or full else 1 - variant[c.key]
        phrase, title = (c.erm, c.erm_title) if k == 0 else (c.alt, c.alt_title)
        cause = c.cause
        if full:
            main, other = (c.alt, c.erm) if use_alt[c.key] else (c.erm, c.alt)
            phrase = main
            if k == 1:
                # A full-size duplicate is the same risk re-entered by another team: it keeps the
                # original statement, frame and context and words the cause differently.
                cause = other
        desc = erm_templates[v].format(phrase=phrase, cause=cause, impact=c.impact,
                                                Impact=_cap(c.impact))
        erm_risk[(c.key, k)] = rid
        rows.append((rid, title, desc, rating_of[c.key]))
        texts.append(TextItem(f"risk_erm:{c.key}:{k}", "risk_erm", rid, "description", desc,
                              _hash("risk_erm", c.key, str(k), title, desc)))
    t["risk_erm"] = Table(["risk_id", "title", "description", "inherent_rating"], rows)

    rng = stream(seed, "risk_ia")
    ia_risk_ids = _ids(seed, "risk_ia", "IAR-", len(ia_concepts), 5000, 10000)
    ia_risk = {}
    rows = []
    for c, rid in zip(ia_concepts, ia_risk_ids):
        v = rng.randrange(len(lib.IA_RISK_TEMPLATES))
        desc = lib.IA_RISK_TEMPLATES[v].format(area=c.area or c.ia_l3, title=c.ia_title, focus=c.ia_focus)
        rating = rating_of[c.key]
        if rng.random() < 0.25:  # IA's own assessment differs by one notch
            i = lib.RATINGS.index(rating)
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
    # Exposure. Sample: each source names the concept's entities. Full size: IA names the
    # specific entity; ERM records the whole owning business unit, and some links point to an
    # entity of another unit in the same segment, as a stale register would (007 AC-5).
    if full:
        rng = stream(seed, "auditable_entity_exposed_to_risk_erm")
        unit_entities: dict[str, list[str]] = {}
        for a, b in entities.items():
            unit_entities.setdefault(b, []).append(a)
        erm_exposure = []
        for (c, _), rid in zip(erm_items, erm_risk_ids):
            unit = entities[c.entities[0]]
            erm_exposure += [(ae_id[a], rid) for a in unit_entities[unit]]
            if rng.random() < STALE_LINK_RATE:
                others = sorted(a for a, b in entities.items()
                                if b != unit and business_units[b] == business_units[unit])
                if others:
                    erm_exposure.append((ae_id[rng.choice(others)], rid))
    else:
        erm_exposure = [(ae_id[a], rid) for (c, _), rid in zip(erm_items, erm_risk_ids) for a in c.entities]
    t["auditable_entity_exposed_to_risk_erm"] = Table(["auditable_entity_id", "risk_id"], erm_exposure)
    t["auditable_entity_exposed_to_risk_ia"] = Table(
        ["auditable_entity_id", "risk_id"],
        [(ae_id[a], ia_risk[c.key]) for c in ia_concepts for a in c.entities])

    # --- controls ----------------------------------------------------------------------
    control_cluster_rows = scenario_rows = None
    if full:
        fc = _full_controls(seed, t, concepts, erm_items, erm_risk_ids, ia_concepts, ia_risk, unused, sys_id,
                            reg_id, person_ids, texts)
        erm_ctrl, ia_ctrl = fc["erm_ctrl"], fc["ia_ctrl"]
        t.update(fc["tables"])
        control_cluster_rows, scenario_rows = fc["clusters"], fc["scenarios"]
    else:
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

    # --- audits and issues --------------------------------------------------------------
    if full:
        fai = _full_audits_issues(seed, n, t, concepts, ia_concepts, ia_risk, ia_ctrl, erm_ctrl, erm_risk, ae_id,
                                  erm_path, erm_node, person_ids, texts)
        t.update(fai["tables"])
        scenario_rows = (scenario_rows or []) + fai["scenarios"]
    else:
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
        by_key = {c.key: c for c in concepts + unused}
        n_issues = n["ISSUE"]
        n_ia_issues = max(1, round(0.5 * n_issues)) if n_issues else 0
        sources = ["IA"] * n_ia_issues + [lib.ISSUE_SOURCES[1 + i % 3] for i in range(n_issues - n_ia_issues)]
        issue_ids = _ids(seed, "issue", "ISS-", n_issues, 1000, 10000)
        erm_mitigated = [c.key for c in erm_concepts]
        issues, raised, against_c, against_r, owned = [], [], {"erm": [], "ia": []}, {"erm": [], "ia": []}, []
        pending_issue_text = []
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
            pending_issue_text.append((source, k, opened.isoformat(), title, iid, desc))
        t["issue"] = Table(["issue_id", "title", "description", "source", "rating", "opened_date", "closed_date"],
                           issues)
        # natural text keys (009): source, control key, ordinal by opened date then title; no global index
        seen: dict[tuple, int] = {}
        for source, k, opened_iso, title, iid, desc in sorted(pending_issue_text):
            ordinal = seen.get((source, k), 0)
            seen[(source, k)] = ordinal + 1
            texts.append(TextItem(f"issue:{source}:{k}:{ordinal}", "issue", iid, "description", desc,
                                  _hash("issue", source, k, title, desc)))
        t["audit_raised_issue"] = Table(["audit_id", "issue_id"], raised)
        for source in ("erm", "ia"):
            t[f"issue_against_control_{source}"] = Table(["issue_id", "control_id"], against_c[source])
            t[f"issue_against_risk_{source}"] = Table(["issue_id", "risk_id"], against_r[source])
        t["issue_owned_by_person"] = Table(["issue_id", "person_id"], owned)

    # --- answer key --------------------------------------------------------------------
    erm_by_level_name = {node: nid for node, nid in erm_node.items()}
    key["taxonomy_map"] = Table(
        ["ia_node_id", "erm_node_id"],
        [(nid, erm_by_level_name[ia_to_erm[node]] if ia_to_erm[node] else "unmapped")
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

    if control_cluster_rows is None:
        in_both = set(erm_ctrl) & set(ia_ctrl)
        control_cluster = {k: f"CC-{i:03d}" for i, k in enumerate(sorted(in_both), 1)}
        control_cluster_rows = ([("ERM", cid, control_cluster.get(k, "none")) for k, cid in erm_ctrl.items()]
                                + [("IA", cid, control_cluster.get(k, "none")) for k, cid in ia_ctrl.items()])
    key["control_clusters"] = Table(["source", "control_id", "cluster_id"], control_cluster_rows)
    key["scenarios"] = Table(["scenario", "item_id"], scenario_rows or [])

    for table in list(t.values()) + list(key.values()):
        table.rows.sort()

    if text == "ai":
        _apply_ai_text(t, texts, text_dir, size)
    return Dataset(t, key, texts)


P_IA_KIND_FROM_ERM = 0.6   # the overlap dial (008): IA tests the enterprise control this often
P_IA_OTHER_FREQUENCY = 0.22  # IA records a neighbouring frequency for this share of its controls
P_ERM_LISTS_SYSTEMS = 0.5   # RCSAs name systems for only some controls
ORPHAN_RATE = 0.045


def _weighted(rng, keys: list[str]) -> str:
    kinds = {k.key: k for k in lib.CONTROL_KINDS}
    return rng.choices(keys, weights=[kinds[k].weight for k in keys])[0]


def orphan_twins(erm_specific, erm_generic, ia_specific, ia_generic, erm_held, ia_held, erm_slots, ia_slots):
    """Orphans that have a counterpart in the other source (must be none, or the answer key would lie).

    Specific orphans are instance keys; generic orphans map key -> (theme, kind) for ERM and
    key -> (instance, kind) for IA. *_held are instances each source holds as risks; *_slots are
    (theme, kind) pairs each source uses for linked generic controls.
    """
    theme = lambda key: key.split("@")[0]
    bad = [k for k in erm_specific if k in ia_held or k in ia_specific]
    bad += [k for k in ia_specific if k in erm_held or k in erm_specific]
    ia_orphan_slots = {(theme(i), kind) for i, kind in ia_generic.values()}
    erm_orphan_slots = set(erm_generic.values())
    bad += [k for k, slot in erm_generic.items() if slot in ia_slots | ia_orphan_slots]
    bad += [k for k, (i, kind) in ia_generic.items() if (theme(i), kind) in erm_slots | erm_orphan_slots]
    return sorted(bad)


def _full_controls(seed, t, concepts, erm_items, erm_risk_ids, ia_concepts, ia_risk, unused, sys_id, reg_id,
                   person_ids, texts) -> dict:
    """Full-size controls (008): specific controls per risk instance, generic controls at two levels.

    ERM records generic controls bank-wide per theme and kind; IA records them per risk instance,
    taking ERM's kinds for the theme with probability P_IA_KIND_FROM_ERM. A cluster is one ERM
    control plus every IA control with the same instance (specific) or theme and kind (generic).
    """
    kinds = {k.key: k for k in lib.CONTROL_KINDS}
    kind_keys = [k.key for k in lib.CONTROL_KINDS]
    theme = lambda key: key.split("@")[0]
    themes = {th.key: th for th in lib.RISK_CONCEPTS + lib.FULL_ONLY_THEMES}
    by_instance = {c.key: c for c in concepts}

    erm_risks_of = defaultdict(list)
    for (c, _), rid in zip(erm_items, erm_risk_ids):
        erm_risks_of[c.key].append(rid)
    erm_instances = sorted(erm_risks_of)
    ia_instances = sorted(c.key for c in ia_concepts)

    # ERM generic kinds per theme, bank-wide (own stream; drawn for every theme so draws never shift)
    rng = stream(seed, "control_erm/kinds")
    erm_kinds = {}
    for th in sorted(themes):
        n = rng.choice([1, 2, 2, 3])
        chosen = []
        for _ in range(n):
            chosen.append(_weighted(rng, [k for k in kind_keys if k not in chosen]))
        erm_kinds[th] = chosen
    erm_themes = sorted({theme(k) for k in erm_instances})

    # IA generic kinds per IA risk instance
    rng = stream(seed, "control_ia/kinds")
    ia_generic = {}  # control key -> (instance key, kind)
    for inst in ia_instances:
        chosen = []
        for _ in range(rng.choice([1, 2])):
            from_erm = [k for k in erm_kinds[theme(inst)] if k not in chosen]
            pool = from_erm if from_erm and rng.random() < P_IA_KIND_FROM_ERM else [k for k in kind_keys
                                                                                    if k not in chosen]
            chosen.append(_weighted(rng, pool))
        for kind in chosen:
            ia_generic[f"{inst}#{kind}"] = (inst, kind)

    erm_generic = {f"{th}#{kind}": (th, kind) for th in erm_themes for kind in erm_kinds[th]}

    # Orphans: controls with no counterpart in the other source, never a twin of a real control
    rng = stream(seed, "control_orphans")
    erm_used = {v for v in erm_generic.values()}
    ia_used = {(theme(inst), kind) for inst, kind in ia_generic.values()}
    free = [(th, kind) for th in sorted(themes) for kind in kind_keys if (th, kind) not in erm_used | ia_used]
    rng.shuffle(free)
    unused_keys = sorted(c.key for c in unused)
    erm_orphan_specific = unused_keys[0::2]
    ia_orphan_specific = unused_keys[1::2]
    target = lambda linked: round(linked * ORPHAN_RATE / (1 - ORPHAN_RATE))
    n_erm_orphans = target(len(erm_instances) + len(erm_generic))
    n_ia_orphans = target(len(ia_instances) + len(ia_generic))
    erm_orphan_generic = {}
    while len(erm_orphan_specific) + len(erm_orphan_generic) < n_erm_orphans and free:
        th, kind = free.pop()
        erm_orphan_generic[f"{th}#{kind}"] = (th, kind)
    ia_orphan_generic = {}
    held_by_ia = set(ia_instances)
    for th, kind in list(free):
        if len(ia_orphan_specific) + len(ia_orphan_generic) >= n_ia_orphans:
            break
        hosts = sorted(c.key for c in concepts if theme(c.key) == th and c.key not in held_by_ia)
        if hosts:
            inst = rng.choice(hosts)
            ia_orphan_generic[f"{inst}#{kind}"] = (inst, kind)
    twins = orphan_twins(erm_orphan_specific, erm_orphan_generic, ia_orphan_specific, ia_orphan_generic,
                         set(erm_risks_of), held_by_ia, erm_used, ia_used)
    if twins:
        raise GenerationError("orphan control with a twin in the other source: " + ", ".join(twins))

    erm_keys = sorted(set(erm_instances) | set(erm_generic) | set(erm_orphan_specific) | set(erm_orphan_generic))
    ia_keys = sorted(set(ia_instances) | set(ia_generic) | set(ia_orphan_specific) | set(ia_orphan_generic))
    erm_ctrl = dict(zip(erm_keys, _ids(seed, "control_erm", "ERM-C", len(erm_keys), 1000, 5000)))
    ia_ctrl = dict(zip(ia_keys, _ids(seed, "control_ia", "IAC-", len(ia_keys), 5000, 10000)))

    def counterpart(ia_key: str) -> str | None:
        if ia_key in ia_generic:
            inst, kind = ia_generic[ia_key]
            erm_key = f"{theme(inst)}#{kind}"
            return erm_key if erm_key in erm_generic else None
        return ia_key if ia_key in erm_risks_of else None

    def text_of(source: str, key: str):
        if "#" not in key:  # specific control of a risk instance
            cc = by_instance[key].control
            return (cc.erm_title, cc.erm) if source == "erm" else (cc.ia_title, cc.ia)
        left, kind = key.split("#")
        k = kinds[kind]
        erm_subject, ia_subject = lib.THEME_SUBJECT[theme(left)]
        if source == "erm":
            return f"{_cap(erm_subject)}: {k.erm_label}", k.erm.format(subject=erm_subject)
        entity = by_instance[left].entities[0]
        desc = k.ia.format(entity=entity, subject=ia_subject)
        # IA RCMs cite the enterprise standard a local procedure implements, in ERM's wording
        desc += f" The procedure implements the {lib.IA_CITATION[kind]} on {erm_subject}."
        return f"{_cap(k.ia_label)} for {ia_subject} ({entity})", desc

    def attributes(key: str):
        if "#" not in key:
            cc = by_instance[key].control
            return cc.control_type, cc.nature, cc.frequency
        k = kinds[key.split("#")[1]]
        return k.control_type, k.nature, k.frequency

    columns = ["control_id", "title", "description", "control_type", "nature", "frequency", "key_control"]
    out: dict[str, Table] = {}
    rows = []
    for key in erm_keys:
        title, desc = text_of("erm", key)
        ctype, nature, freq = attributes(key)
        high = "#" not in key and by_instance[key].rating == "High"
        rows.append((erm_ctrl[key], title, desc, ctype, nature, freq, "Y" if high else "N"))
        texts.append(TextItem(f"control_erm:{key}", "control_erm", erm_ctrl[key], "description", desc,
                              _hash("control_erm", key, title, desc)))
    out["control_erm"] = Table(columns, rows)
    rng = stream(seed, "control_ia")
    frng = stream(seed, "control_ia/frequency")
    rows = []
    for key in ia_keys:
        title, desc = text_of("ia", key)
        ctype, nature, freq = attributes(key)
        if frng.random() < P_IA_OTHER_FREQUENCY:  # IA records a neighbouring frequency
            i = lib.FREQUENCIES.index(freq)
            freq = lib.FREQUENCIES[i + 1 if i + 1 < len(lib.FREQUENCIES) - 1 else i - 1]
        rows.append((ia_ctrl[key], title, desc, ctype, nature, freq, "Y" if rng.random() < 0.7 else "N"))
        texts.append(TextItem(f"control_ia:{key}", "control_ia", ia_ctrl[key], "description", desc,
                              _hash("control_ia", key, title, desc)))
    out["control_ia"] = Table(columns, rows)

    erm_by_theme = defaultdict(list)
    for inst, rids in erm_risks_of.items():
        erm_by_theme[theme(inst)] += rids
    out["control_mitigates_risk_erm"] = Table(
        ["control_id", "risk_id"],
        [(erm_ctrl[k], rid) for k in erm_instances for rid in erm_risks_of[k]]
        + [(erm_ctrl[k], rid) for k, (th, _) in erm_generic.items() for rid in erm_by_theme[th]])
    out["control_mitigates_risk_ia"] = Table(
        ["control_id", "risk_id"],
        [(ia_ctrl[k], ia_risk[k]) for k in ia_instances]
        + [(ia_ctrl[k], ia_risk[inst]) for k, (inst, _) in ia_generic.items()])

    def systems_of(key: str) -> list[str]:
        if "#" not in key:
            return by_instance[key].control.systems
        th_or_inst, kind = key.split("#")
        own = themes[theme(th_or_inst)].control.systems
        return own[:1] if kinds[kind].uses_system else []

    srng = stream(seed, "control_depends_on_system_erm")
    erm_systems = {k: (systems_of(k) if srng.random() < P_ERM_LISTS_SYSTEMS else []) for k in erm_keys}
    out["control_depends_on_system_erm"] = Table(
        ["control_id", "system_id"], [(erm_ctrl[k], sys_id[s]) for k in erm_keys for s in erm_systems[k]])
    out["control_depends_on_system_ia"] = Table(
        ["control_id", "system_id"], [(ia_ctrl[k], sys_id[s]) for k in ia_keys for s in systems_of(k)])

    def regulation_of(key: str) -> str | None:
        if "#" not in key:
            return by_instance[key].control.regulation
        th_or_inst, kind = key.split("#")
        return themes[theme(th_or_inst)].control.regulation if kind == "policy" else None

    for source, ctrl, keys in (("erm", erm_ctrl, erm_keys), ("ia", ia_ctrl, ia_keys)):
        out[f"regulation_requires_control_{source}"] = Table(
            ["regulation_id", "control_id"],
            [(reg_id[regulation_of(k)], ctrl[k]) for k in keys if regulation_of(k) in reg_id])

    rng = stream(seed, "control_owned_by_person_erm")
    erm_owner = {k: rng.choice(person_ids) for k in erm_keys}
    rng = stream(seed, "control_owned_by_person_ia")
    ia_owner = {k: rng.choice([p for p in person_ids if p != erm_owner.get(counterpart(k) or "")])
                for k in ia_keys}
    out["control_owned_by_person_erm"] = Table(["control_id", "person_id"], [(erm_ctrl[k], p)
                                                                            for k, p in erm_owner.items()])
    out["control_owned_by_person_ia"] = Table(["control_id", "person_id"], [(ia_ctrl[k], p)
                                                                           for k, p in ia_owner.items()])

    # answer key: one ERM control per cluster, plus every IA control that matches it
    members = defaultdict(list)
    for k in ia_instances + sorted(ia_generic):
        erm_key = counterpart(k)
        if erm_key:
            members[erm_key].append(k)
    cluster_id = {erm_key: f"CC-{i:03d}" for i, erm_key in enumerate(sorted(members), 1)}
    ia_cluster = {ia_key: cluster_id[erm_key] for erm_key, ia_keys_ in members.items() for ia_key in ia_keys_}
    clusters = ([("ERM", erm_ctrl[k], cluster_id.get(k, "none")) for k in erm_keys]
                + [("IA", ia_ctrl[k], ia_cluster.get(k, "none")) for k in ia_keys])

    # shared-system scenario: reach = union over both sources of control -> risk -> exposed entity
    exposed = defaultdict(set)
    for source in ("erm", "ia"):
        for entity_id, risk_id in t[f"auditable_entity_exposed_to_risk_{source}"].rows:
            exposed[risk_id].add(entity_id)
    risks_of_control = defaultdict(set)
    for source in ("erm", "ia"):
        for control_id, risk_id in out[f"control_mitigates_risk_{source}"].rows:
            risks_of_control[control_id].add(risk_id)
    reach = defaultdict(set)
    for source in ("erm", "ia"):
        for control_id, system_id in out[f"control_depends_on_system_{source}"].rows:
            for risk_id in risks_of_control[control_id]:
                reach[system_id] |= exposed[risk_id]
    name_of = {v: k for k, v in sys_id.items()}
    ranked = sorted(reach, key=lambda s: (-len(reach[s]), name_of[s]))
    scenarios = [("shared_system", s) for s in ranked[:3]]
    return {"erm_ctrl": erm_ctrl, "ia_ctrl": ia_ctrl, "tables": out, "clusters": clusters,
            "scenarios": scenarios}


MIN_FULL_AUDITS, MIN_FULL_ISSUES = 30, 100
UNAUDITED_SHARE = 0.10     # of entities with IA risk, left out of the three-year plan
SCOPE_SHARE = 0.67          # share of a covered entity's IA risks an audit scopes in
REPEAT_GROUPS = 6           # planted repeat-finding groups (each one IA control, several years)
RISING_YEARS = (8, 10, 13)  # rising ERM L1 category: non-IA issues opened in 2023, 2024, 2025
ISSUE_SHARES = {"IA": 0.50, "Regulator": 0.15, "Self-identified": 0.15, "2nd line": 0.20}


def _full_audits_issues(seed, n, t, concepts, ia_concepts, ia_risk, ia_ctrl, erm_ctrl, erm_risk, ae_id,
                        erm_path, erm_node, person_ids, texts) -> dict:
    """Full-size audit plan and issues (009). Every per-row choice draws from its own stream."""
    if n["AUDIT"] < MIN_FULL_AUDITS or n["ISSUE"] < MIN_FULL_ISSUES:
        raise GenerationError(f"full size needs at least {MIN_FULL_AUDITS} audits and {MIN_FULL_ISSUES} issues "
                              "to plant the scenarios")
    by_instance = {c.key: c for c in ia_concepts}
    theme = lambda key: key.split("@")[0]
    rating_of = {row[0]: row[3] for row in t["risk_ia"].rows}

    # IA controls per IA risk instance (orphans mitigate nothing and are never tested)
    controls_of_instance = defaultdict(list)
    for key in sorted(ia_ctrl):
        inst = key.split("#")[0]
        if inst in ia_risk:
            controls_of_instance[inst].append(key)
    instances_of_entity = defaultdict(list)
    for c in ia_concepts:
        instances_of_entity[c.entities[0]].append(c.key)
    risk_entities = sorted(instances_of_entity)
    high = lambda inst: rating_of[ia_risk[inst]] == "High"

    # --- audit plan: some entities fall outside the plan; the rest are sampled by risk ----
    rng = stream(seed, "audit/plan")
    n_out = round(UNAUDITED_SHARE * len(risk_entities))
    out_weights = [1.0 if any(high(i) for i in instances_of_entity[a]) else 3.0 for a in risk_entities]
    unaudited = set()
    while len(unaudited) < n_out:
        unaudited.add(rng.choices(risk_entities, weights=out_weights)[0])
    in_plan = [a for a in risk_entities if a not in unaudited]
    weight = {a: 1 + 2 * sum(high(i) for i in instances_of_entity[a]) for a in in_plan}

    srng = stream(seed, "audit/scope")
    drng = stream(seed, "audit/dates")
    audit_ids = _ids(seed, "audit", "AUD-", n["AUDIT"], 100, 1000)
    audits, covered, tested_rows, audit_info = [], [], [], []
    for i, aid in enumerate(audit_ids):
        year = 2023 + i % 3
        scope, size = [], rng.choice([1, 1, 2, 2, 3])
        while len(scope) < min(size, len(in_plan)):
            pick = rng.choices(in_plan, weights=[weight[a] for a in in_plan])[0]
            if pick not in scope:
                scope.append(pick)
        scope.sort()
        tested = []
        for a in scope:
            insts = instances_of_entity[a]
            k = max(1, round(SCOPE_SHARE * len(insts)))
            for inst in sorted(srng.sample(insts, k)):
                tested += controls_of_instance[inst]
        start = date(year, drng.randint(1, 10), drng.randint(1, 28))
        end = min(start + timedelta(days=drng.randint(30, 60)), WINDOW_END)
        audits.append((aid, f"{' and '.join(scope)} Audit {year}", year, start.isoformat(), end.isoformat(),
                       drng.choice(lib.AUDIT_RATINGS)))
        covered += [(aid, ae_id[a]) for a in scope]
        tested_rows += [(aid, ia_ctrl[k]) for k in sorted(set(tested))]
        audit_info.append((aid, year, end, sorted(set(tested))))
    out = {"audit": Table(["audit_id", "title", "audit_year", "start_date", "end_date", "rating"], audits),
           "audit_covered_auditable_entity": Table(["audit_id", "auditable_entity_id"], covered),
           "audit_tested_control_ia": Table(["audit_id", "control_id"], tested_rows)}

    tested_controls = {k for _, _, _, ks in audit_info for k in ks}
    untested_high = sorted(ia_risk[c.key] for c in ia_concepts
                           if high(c.key) and not set(controls_of_instance[c.key]) & tested_controls)

    # --- issue counts per source ------------------------------------------------------------
    total = n["ISSUE"]
    counts = {s: round(share * total) for s, share in ISSUE_SHARES.items()}
    counts["IA"] += total - sum(counts.values())

    def finding(control_key: str, subject: str) -> str:
        if "#" in control_key:
            return lib.KIND_FINDINGS[control_key.split("#")[1]].format(subject=subject)
        f = by_any[control_key.split("#")[0]].control.finding
        return f if f[:1].isdigit() else f[:1].lower() + f[1:]

    by_any = {c.key: c for c in concepts}

    # --- IA issues: planted repeat findings first, then audits' other findings ----------------
    irng = stream(seed, "issue/ia")
    years_of_control = defaultdict(set)
    for _, year, _, ks in audit_info:
        for k in ks:
            years_of_control[k].add(year)
    multi_year = sorted(k for k, ys in years_of_control.items() if len(ys) >= 2)
    planted = irng.sample(multi_year, min(REPEAT_GROUPS, len(multi_year)))
    if len(planted) < 5:
        raise GenerationError("too few IA controls tested in two or more years to plant 5 repeat findings")
    ia_pairs = []  # (audit info, control key, repeat group or None)
    for g, k in enumerate(planted, 1):
        hosts = [info for info in audit_info if k in info[3]]
        by_year = defaultdict(list)
        for info in hosts:
            by_year[info[1]].append(info)
        years = sorted(by_year)[:4]
        for year in years:
            ia_pairs.append((irng.choice(by_year[year]), k, g))
    # other findings: a control outside the planted groups gets issues in one year only, so the
    # planted groups are exactly the repeat findings (009 review)
    candidates = [(info, k) for info in audit_info for k in info[3] if k not in planted]
    year_of = {}
    while len(ia_pairs) < counts["IA"] and candidates:
        info, k = candidates.pop(irng.randrange(len(candidates)))
        if year_of.setdefault(k, info[1]) != info[1]:
            continue
        ia_pairs.append((info, k, None))

    # --- non-IA issues: a rising ERM L1 category, other categories flat ------------------------
    nrng = stream(seed, "issue/other")
    erm_specific = sorted({inst for (inst, ordinal) in erm_risk if ordinal == 0 and inst in erm_ctrl})
    l1_of = {inst: erm_path[by_any[inst].erm_l3][0] for inst in erm_specific}
    by_l1 = defaultdict(list)
    for inst in erm_specific:
        by_l1[l1_of[inst]].append(inst)
    rising = "Credit" if "Credit" in by_l1 else sorted(by_l1, key=lambda l: -len(by_l1[l]))[1]
    others = sorted(l for l in by_l1 if l != rising)
    n_other = total - counts["IA"]
    per_year = [n_other // 3 + (1 if y < n_other % 3 else 0) for y in range(3)]
    other_sources = [s for s in ("Regulator", "Self-identified", "2nd line") for _ in range(counts[s])]
    nrng.shuffle(other_sources)
    share = {l: len(by_l1[l]) for l in others}
    non_ia = []  # (year, ERM instance)
    for y, (year_total, rising_n) in enumerate(zip(per_year, RISING_YEARS)):
        rest = year_total - rising_n
        quota = {l: int(rest * share[l] / sum(share.values())) for l in others}
        leftovers = sorted(others, key=lambda l: -(rest * share[l] / sum(share.values()) - quota[l]))
        for l in leftovers[:rest - sum(quota.values())]:
            quota[l] += 1
        for l, q in [(rising, rising_n)] + sorted(quota.items()):
            non_ia += [(2023 + y, nrng.choice(by_l1[l])) for _ in range(q)]

    # --- issue rows ---------------------------------------------------------------------------
    issue_ids = _ids(seed, "issue", "ISS-", len(ia_pairs) + len(non_ia), 1000, 10000)
    trng = stream(seed, "issue/text")
    drng_dup = stream(seed, "issue_against_risk_erm")  # either copy of an ERM duplicate (009 review)
    crng = stream(seed, "issue/dates")
    rrng = stream(seed, "issue/rating")
    issues, raised, owned = [], [], []
    against_c, against_r = {"erm": [], "ia": []}, {"erm": [], "ia": []}
    groups = defaultdict(list)
    pending = []
    used_templates = defaultdict(set)
    for iid, (info, k, group) in zip(issue_ids, ia_pairs):
        aid, year, end, _ = info
        inst = k.split("#")[0]
        subject = lib.THEME_SUBJECT[theme(inst)][1]
        options = [x for x in range(4) if x not in used_templates[k]] or list(range(4))
        tmpl = trng.choice(options)
        used_templates[k].add(tmpl)
        title = lib.FULL_ISSUE_TITLES["IA"][tmpl].format(subject=subject, Subject=_cap(subject))
        desc = lib.FULL_ISSUE_OPENINGS["IA"][tmpl].format(f=finding(k, subject))
        opened = min(end + timedelta(days=crng.randint(0, 20)), date(year, 12, 31))  # within the audit year
        issues.append((iid, "IA", title, desc, opened))
        raised.append((aid, iid))
        against_c["ia"].append((iid, ia_ctrl[k]))
        against_r["ia"].append((iid, ia_risk[inst]))
        if group:
            groups[group].append(iid)
        pending.append(("IA", k, opened.isoformat(), title, iid, desc))
    for iid, source, (year, inst) in zip(issue_ids[len(ia_pairs):], other_sources, non_ia):
        subject = lib.THEME_SUBJECT[theme(inst)][0]
        tmpl = trng.randrange(4)
        title = lib.FULL_ISSUE_TITLES[source][tmpl].format(subject=subject, Subject=_cap(subject))
        desc = lib.FULL_ISSUE_OPENINGS[source][tmpl].format(f=finding(inst, subject))
        opened = date(year, 1, 1) + timedelta(days=crng.randint(0, 364 if year < 2025 else 300))
        issues.append((iid, source, title, desc, opened))
        against_c["erm"].append((iid, erm_ctrl[inst]))
        copies = [o for o in (0, 1) if (inst, o) in erm_risk]
        against_r["erm"].append((iid, erm_risk[(inst, drng_dup.choice(copies))]))
        pending.append((source, inst, opened.isoformat(), title, iid, desc))

    orng = stream(seed, "issue_owned_by_person")
    rows = []
    for iid, source, title, desc, opened in issues:
        closed = ""
        if crng.random() < 0.6:
            close_date = opened + timedelta(days=crng.randint(30, 200))
            if close_date <= WINDOW_END:
                closed = close_date.isoformat()
        rating = rrng.choices(lib.RATINGS, weights=[2, 5, 3])[0]
        rows.append((iid, title, desc, source, rating, opened.isoformat(), closed))
        owned.append((iid, orng.choice(person_ids)))
    out["issue"] = Table(["issue_id", "title", "description", "source", "rating", "opened_date", "closed_date"],
                         rows)
    out["audit_raised_issue"] = Table(["audit_id", "issue_id"], raised)
    for source in ("erm", "ia"):
        out[f"issue_against_control_{source}"] = Table(["issue_id", "control_id"], against_c[source])
        out[f"issue_against_risk_{source}"] = Table(["issue_id", "risk_id"], against_r[source])
    out["issue_owned_by_person"] = Table(["issue_id", "person_id"], owned)

    seen: dict[tuple, int] = {}
    for source, k, opened_iso, title, iid, desc in sorted(pending):
        ordinal = seen.get((source, k), 0)
        seen[(source, k)] = ordinal + 1
        texts.append(TextItem(f"issue:{source}:{k}:{ordinal}", "issue", iid, "description", desc,
                              _hash("issue", source, k, title, desc)))

    scenarios = [(f"repeat_finding:{g}", iid) for g, ids in sorted(groups.items()) for iid in ids]
    scenarios += [("untested_high_risk", rid) for rid in untested_high]
    scenarios.append(("rising_category", erm_node[(1, rising)]))
    return {"tables": out, "scenarios": scenarios}


AI_TEXT_FILE = "ai_text.jsonl"            # sample text (005), hashes without a prompt version
FULL_AI_TEXT_FILE = "ai_text_full.jsonl"  # full-size text (010), hashes include the full prompt version


def full_text_hash(input_hash: str) -> str:
    """A full-size entry's stored hash: the item's inputs plus the full prompt version (010 AC-3)."""
    from .prompts import full_prompt_version

    return _hash(input_hash, full_prompt_version())


def load_ai_text(text_dir: Path, size: str = "sample") -> dict[str, dict]:
    path = Path(text_dir) / (FULL_AI_TEXT_FILE if size == "full" else AI_TEXT_FILE)
    if not path.exists():
        raise GenerationError(f"no committed AI text at {path}")
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            entries[entry["key"]] = entry
    return entries


def _apply_ai_text(tables: dict[str, Table], texts: list[TextItem], text_dir: Path | None,
                   size: str = "sample") -> None:
    if text_dir is None:
        raise GenerationError("--text ai needs --text-dir")
    entries = load_ai_text(text_dir, size)
    replacement: dict[tuple[str, str], str] = {}
    for item in texts:
        entry = entries.get(item.key)
        if entry is None:
            raise GenerationError(f"AI text missing for key {item.key}")
        expected = full_text_hash(item.input_hash) if size == "full" else item.input_hash
        if entry["input_hash"] != expected:
            raise GenerationError(f"AI text is stale for key {item.key}: its inputs or prompt changed")
        replacement[(item.file, item.item_id)] = entry["text"]
    for name, table in tables.items():
        if "description" not in table.columns:
            continue
        col = table.columns.index("description")
        table.rows = [row[:col] + (replacement.get((name, row[0]), row[col]),) + row[col + 1:]
                      for row in table.rows]


def orphan_ai_keys(dataset: Dataset, text_dir: Path, size: str = "sample") -> list[str]:
    """Committed AI text keys (of that size's file) that no generated item uses."""
    used = {item.key for item in dataset.text_items}
    return sorted(k for k in load_ai_text(text_dir, size) if k not in used)
