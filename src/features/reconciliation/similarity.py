"""Risk-to-risk similarity from published files only (E2; shared by the taxonomy vote and child b).

Similarity = word TF-IDF cosine + character TF-IDF cosine on `title + '. ' + description`,
plus a structural bonus: SHARED_ENTITY when the risks share an exposed auditable entity, or else
SHARED_UNIT when they share a business unit of their exposed entities.
"""
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

WORD_NGRAMS = (1, 2)
CHAR_NGRAMS = (3, 5)
SHARED_ENTITY = 0.3
SHARED_UNIT = 0.15


def read(build_dir: Path, name: str) -> list[dict]:
    with open(Path(build_dir) / f"{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def risk_text(row: dict) -> str:
    return row["title"] + ". " + row["description"]


def exposure(build_dir: Path) -> tuple[dict, dict]:
    """(risk ID -> exposed auditable entities, auditable entity -> business unit)."""
    exposed = defaultdict(set)
    for source in ("erm", "ia"):
        for r in read(build_dir, f"auditable_entity_exposed_to_risk_{source}"):
            exposed[r["risk_id"]].add(r["auditable_entity_id"])
    unit = {r["auditable_entity_id"]: r["business_unit_id"]
            for r in read(build_dir, "business_unit_owns_auditable_entity")}
    return exposed, unit


def text_similarity(texts_a: list[str], texts_b: list[str]) -> np.ndarray:
    """Word plus character TF-IDF cosine, both vectorizers fitted on all texts of both sides."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    every = texts_a + texts_b
    total = np.zeros((len(texts_a), len(texts_b)))
    for vectorizer in (TfidfVectorizer(ngram_range=WORD_NGRAMS, sublinear_tf=True),
                       TfidfVectorizer(analyzer="char_wb", ngram_range=CHAR_NGRAMS, sublinear_tf=True)):
        vectorizer.fit(every)
        total += cosine_similarity(vectorizer.transform(texts_a), vectorizer.transform(texts_b))
    return total


def risk_similarity(build_dir: Path) -> tuple[list[str], list[str], np.ndarray]:
    """(IA risk IDs sorted, ERM risk IDs sorted, IA x ERM similarity matrix)."""
    erm = sorted(read(build_dir, "risk_erm"), key=lambda r: r["risk_id"])
    ia = sorted(read(build_dir, "risk_ia"), key=lambda r: r["risk_id"])
    sims = text_similarity([risk_text(r) for r in ia], [risk_text(r) for r in erm])
    exposed, unit = exposure(build_dir)
    units = {rid: {unit[a] for a in entities} for rid, entities in exposed.items()}
    for a, i in enumerate(r["risk_id"] for r in ia):
        for b, e in enumerate(r["risk_id"] for r in erm):
            if exposed[i] & exposed[e]:
                sims[a, b] += SHARED_ENTITY
            elif units.get(i, set()) & units.get(e, set()):
                sims[a, b] += SHARED_UNIT
    return [r["risk_id"] for r in ia], [r["risk_id"] for r in erm], sims
