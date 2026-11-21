"""Pair feature tables for matching (E2 child b, change 012). Published files only (INV-6).

Three pair kinds, each a (matrix, sorted pair list) with named columns:
- RISK: every ERM x IA risk pair (rows of the text matrices are IA risks)
- DUPLICATE: every unordered ERM x ERM risk pair
- CONTROL: every ERM x IA control pair (needs cross-source risk scores for `risk_link`)
`word` and `char` are tail scores (see `tail`), so they are scale-free across text styles.
"""
from collections import defaultdict
from pathlib import Path

import numpy as np

from .similarity import CHAR_NGRAMS, WORD_NGRAMS, exposure, read, risk_text
from .taxonomy_map import UNMAPPED, _ancestors, _tree, map_taxonomy

RISK_COLUMNS = ["word", "char", "rank", "shared_entity", "shared_unit_only", "taxonomy", "same_rating"]
DUPLICATE_COLUMNS = ["word", "char", "rank", "same_node", "same_rating"]
CONTROL_COLUMNS = ["word", "char", "rank", "risk_link", "same_type", "same_nature", "same_frequency",
                   "shared_system", "citation"]


def tail(values: np.ndarray) -> np.ndarray:
    """-log10(1 - p + 1/n), where p = (0-based average rank of ties) / (n - 1) within `values`."""
    n = len(values)
    order = np.argsort(values, kind="stable")
    _, start, counts = np.unique(values[order], return_index=True, return_counts=True)
    ranks = np.empty(n)
    ranks[order] = np.repeat(start + (counts - 1) / 2.0, counts)
    p = ranks / (n - 1)
    return -np.log10(1 - p + 1.0 / n)


def cosines(rows: list[str], cols: list[str], fit_on: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """(word, char) TF-IDF cosine matrices, vectorizers fitted on `fit_on`."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    out = []
    for vectorizer in (TfidfVectorizer(ngram_range=WORD_NGRAMS, sublinear_tf=True),
                       TfidfVectorizer(analyzer="char_wb", ngram_range=CHAR_NGRAMS, sublinear_tf=True)):
        vectorizer.fit(fit_on)
        out.append(cosine_similarity(vectorizer.transform(rows), vectorizer.transform(cols)))
    return out[0], out[1]


def row_rank(scores: np.ndarray) -> np.ndarray:
    """1 / (1-based position of each column among its row's candidates, highest first, stable)."""
    order = np.argsort(-scores, axis=1, kind="stable")
    ranks = np.empty_like(order)
    ranks[np.arange(scores.shape[0])[:, None], order] = np.arange(scores.shape[1])[None, :]
    return 1.0 / (ranks + 1)


def _with_tails(rows: list, columns: int = 2) -> np.ndarray:
    matrix = np.array(rows, dtype=float)
    for c in range(columns):
        matrix[:, c] = tail(matrix[:, c])
    return matrix


def risk_tables(build_dir: Path):
    """((RISK matrix, [(erm_id, ia_id)]), (DUPLICATE matrix, [(erm_id, erm_id)]))."""
    erm = sorted(read(build_dir, "risk_erm"), key=lambda r: r["risk_id"])
    ia = sorted(read(build_dir, "risk_ia"), key=lambda r: r["risk_id"])
    E, I = [r["risk_id"] for r in erm], [r["risk_id"] for r in ia]
    te, ti = [risk_text(r) for r in erm], [risk_text(r) for r in ia]
    word, char = cosines(ti, te, ti + te)
    rank = row_rank(word + char)
    exposed, unit = exposure(build_dir)
    units = {rid: {unit[a] for a in ents} for rid, ents in exposed.items()}
    node_of = {r["risk_id"]: r["taxonomy_node_id"] for s in ("erm", "ia")
               for r in read(build_dir, f"taxonomy_node_classifies_risk_{s}")}
    erm_parent, ia_parent = _tree(build_dir, "erm")[1], _tree(build_dir, "ia")[1]
    mapping = {r["ia_node_id"]: r["erm_node_id"] for r in map_taxonomy(build_dir)}
    target = {i: next((mapping[n] for n in _ancestors(node_of[i], ia_parent) if mapping[n] != UNMAPPED), None)
              for i in I}
    rating = {r["risk_id"]: r["inherent_rating"] for r in erm + ia}
    pairs, rows = [], []
    for a, i in enumerate(I):
        for b, e in enumerate(E):
            entity = bool(exposed[i] & exposed[e])
            rows.append([word[a, b], char[a, b], rank[a, b], entity,
                         (not entity) and bool(units.get(i, set()) & units.get(e, set())),
                         target[i] is not None and target[i] in _ancestors(node_of[e], erm_parent),
                         rating[i] == rating[e]])
            pairs.append((e, i))
    dword, dchar = cosines(te, te, ti + te)
    np.fill_diagonal(dword, -1.0)
    np.fill_diagonal(dchar, -1.0)
    drank = row_rank(dword + dchar)
    dpairs, drows = [], []
    for a in range(len(E)):
        for b in range(a + 1, len(E)):
            drows.append([dword[a, b], dchar[a, b], max(drank[a, b], drank[b, a]),
                          node_of[E[a]] == node_of[E[b]], rating[E[a]] == rating[E[b]]])
            dpairs.append((E[a], E[b]))
    return (_with_tails(rows), pairs), (_with_tails(drows), dpairs)


def citation(erm_title: str, ia_description: str) -> bool:
    if ":" not in erm_title:
        return False
    subject = erm_title.split(":", 1)[0].strip().lower()
    return bool(subject) and subject in ia_description.lower()


def control_table(build_dir: Path, risk_score: dict):
    """(CONTROL matrix, [(erm_id, ia_id)]); risk_score: (erm_risk, ia_risk) -> risk-model probability."""
    cerm = sorted(read(build_dir, "control_erm"), key=lambda r: r["control_id"])
    cia = sorted(read(build_dir, "control_ia"), key=lambda r: r["control_id"])
    E, I = [r["control_id"] for r in cerm], [r["control_id"] for r in cia]
    te, ti = [risk_text(r) for r in cerm], [risk_text(r) for r in cia]
    word, char = cosines(ti, te, ti + te)
    rank = row_rank(word + char)
    mitigates, systems = defaultdict(set), defaultdict(set)
    for s in ("erm", "ia"):
        for r in read(build_dir, f"control_mitigates_risk_{s}"):
            mitigates[r["control_id"]].add(r["risk_id"])
        for r in read(build_dir, f"control_depends_on_system_{s}"):
            systems[r["control_id"]].add(r["system_id"])
    row = {r["control_id"]: r for r in cerm + cia}
    pairs, rows = [], []
    for a, i in enumerate(I):
        for b, e in enumerate(E):
            link = max((risk_score.get((x, y), 0.0) for x in mitigates[e] for y in mitigates[i]), default=0.0)
            rows.append([word[a, b], char[a, b], rank[a, b], link,
                         row[e]["control_type"] == row[i]["control_type"], row[e]["nature"] == row[i]["nature"],
                         row[e]["frequency"] == row[i]["frequency"], bool(systems[e] & systems[i]),
                         citation(row[e]["title"], row[i]["description"])])
            pairs.append((e, i))
    return _with_tails(rows), pairs
