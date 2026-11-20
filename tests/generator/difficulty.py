"""How hard is it to match ERM and IA risks? Baselines and rates for 007 (AC-1, AC-4, AC-5).

Every baseline reads only published files; the answer key is used only to score them.
"""
import re
import statistics
from collections import Counter, defaultdict

from .helpers import answer_key, read


def _f1(predicted: set, truth: set) -> float:
    if not predicted or not truth:
        return 0.0
    tp = len(predicted & truth)
    if tp == 0:
        return 0.0
    precision, recall = tp / len(predicted), tp / len(truth)
    return 2 * precision * recall / (precision + recall)


def _best_threshold_f1(scored: dict, truth: set) -> float:
    """Best F1 over thresholds, predicting every pair scored at or above the threshold (one sorted sweep)."""
    if not truth:
        return 0.0
    best = tp = predicted = 0
    ordered = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
    for n, (pair, score) in enumerate(ordered):
        predicted += 1
        tp += pair in truth
        last_at_this_score = n + 1 == len(ordered) or ordered[n + 1][1] != score
        if last_at_this_score and tp:
            best = max(best, 2 * tp / (predicted + len(truth)))
    return best


class Risks:
    """Published risk data plus the answer key's truth, for one build directory."""

    def __init__(self, out):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        self.erm, self.ia = read(out, "risk_erm"), read(out, "risk_ia")
        rows = self.erm + self.ia
        self.desc = {r["risk_id"]: r["description"] for r in rows}
        ids = [r["risk_id"] for r in rows]
        sims = cosine_similarity(TfidfVectorizer(lowercase=True, ngram_range=(1, 2)).fit_transform(
            [r["description"] for r in rows]))
        index = {rid: i for i, rid in enumerate(ids)}
        self.cos = lambda a, b: float(sims[index[a], index[b]])

        clusters = answer_key(out, "risk_clusters")
        self.cluster = {r["risk_id"]: r["cluster_id"] for r in clusters}
        self.true_node = {r["risk_id"]: r["true_erm_node_id"] for r in clusters}
        same = lambda a, b: self.cluster[a] != "none" and self.cluster[a] == self.cluster[b]
        self.erm_ids = [r["risk_id"] for r in self.erm]
        self.ia_ids = [r["risk_id"] for r in self.ia]
        self.cross_pairs = [(e, i) for e in self.erm_ids for i in self.ia_ids]
        self.truth = {p for p in self.cross_pairs if same(*p)}
        self.erm_pairs = [(a, b) for n, a in enumerate(self.erm_ids) for b in self.erm_ids[n + 1:]]
        self.erm_truth = {p for p in self.erm_pairs if same(*p)}

        self.exposed = defaultdict(set)
        for source in ("erm", "ia"):
            for r in read(out, f"auditable_entity_exposed_to_risk_{source}"):
                self.exposed[r["risk_id"]].add(r["auditable_entity_id"])
        self.unit_of = {r["auditable_entity_id"]: r["business_unit_id"]
                        for r in read(out, "business_unit_owns_auditable_entity")}
        self.segment_of = {r["business_unit_id"]: r["segment_id"] for r in read(out, "segment_has_business_unit")}
        self.entity_name = {r["auditable_entity_id"]: r["name"] for r in read(out, "auditable_entity")}

        ia_node = {r["risk_id"]: r["taxonomy_node_id"] for r in read(out, "taxonomy_node_classifies_risk_ia")}
        target = {r["ia_node_id"]: r["erm_node_id"] for r in answer_key(out, "taxonomy_map")}
        parent = {e["child_id"]: e["parent_id"] for e in read(out, "taxonomy_node_parent_of_taxonomy_node_erm")}

        def ancestors(node):
            chain = [node]
            while chain[-1] in parent:
                chain.append(parent[chain[-1]])
            return chain

        self.misfiled = [i for i in self.ia_ids if target[ia_node[i]] not in ancestors(self.true_node[i])]

    # --- AC-1 -----------------------------------------------------------------------------
    def overlap(self) -> float:
        matched = {i for _, i in self.truth}
        return len(matched) / len(self.ia_ids)

    def erm_duplicate_rate(self) -> float:
        counts = Counter(self.cluster[e] for e in self.erm_ids if self.cluster[e] != "none")
        return sum(c - 1 for c in counts.values() if c > 1) / len(self.erm_ids)

    def misfiled_rate(self) -> float:
        return len(self.misfiled) / len(self.ia_ids)

    # --- AC-4 -----------------------------------------------------------------------------
    def exact_text_f1(self) -> float:
        return _f1({p for p in self.cross_pairs if self.desc[p[0]] == self.desc[p[1]]}, self.truth)

    def tfidf_f1(self) -> float:
        return _best_threshold_f1({p: self.cos(*p) for p in self.cross_pairs}, self.truth)

    def erm_duplicate_f1(self) -> float:
        return _best_threshold_f1({p: self.cos(*p) for p in self.erm_pairs}, self.erm_truth)

    def hard_negatives(self) -> dict:
        """IA risk -> its hard negatives (ERM non-matches at or above the matched median cosine)."""
        median = statistics.median(self.cos(*p) for p in self.truth)
        found = defaultdict(list)
        for e, i in self.cross_pairs:
            if (e, i) not in self.truth and self.cos(e, i) >= median:
                found[i].append(e)
        return found

    def hard_negative_rate(self) -> float:
        return len(self.hard_negatives()) / len(self.ia_ids)

    # --- AC-5 -----------------------------------------------------------------------------
    def exposure_f1(self) -> float:
        predicted = {(e, i) for e, i in self.cross_pairs if self.exposed[i] & self.exposed[e]}
        return _f1(predicted, self.truth)

    def _best_per_ia(self, candidates) -> float:
        """For each IA risk keep its best-scoring candidate ERM risk; best F1 over thresholds."""
        best = {}
        for i in self.ia_ids:
            options = [e for e in candidates(i)]
            if options:
                e = max(options, key=lambda e: self.cos(e, i))
                best[(e, i)] = self.cos(e, i)
        return _best_threshold_f1(best, self.truth)

    def combined_f1(self) -> float:
        def same_unit(i):
            units = {self.unit_of[a] for a in self.exposed[i]}
            return [e for e in self.erm_ids if units & {self.unit_of[a] for a in self.exposed[e]}]
        return self._best_per_ia(same_unit)

    def entity_mention_f1(self) -> float:
        def words(text):
            return set(re.findall(r"[a-z]+", text.lower()))
        name_words = Counter(w for n in self.entity_name.values() for w in words(n))

        def mentions(i):
            distinctive = {w for a in self.exposed[i] for w in words(self.entity_name[a]) if name_words[w] <= 3}
            return [e for e in self.erm_ids if distinctive & words(self.desc[e])]
        return self._best_per_ia(mentions)

    def same_unit_hard_negative_share(self) -> float:
        hard = self.hard_negatives()
        units = lambda r: {self.unit_of[a] for a in self.exposed[r]}
        sharing = [i for i, es in hard.items() if any(units(i) & units(e) for e in es)]
        return len(sharing) / len(hard) if hard else 0.0

    def stale_link_share(self) -> float:
        links = stale = 0
        for e in self.erm_ids:
            units = Counter(self.unit_of[a] for a in self.exposed[e])
            home = units.most_common(1)[0][0]
            for a in self.exposed[e]:
                links += 1
                stale += self.unit_of[a] != home
        return stale / links
