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


def chance_f1(pairs, truth) -> float:
    """F1 of predicting every candidate pair a match: the floor any matcher must beat."""
    return 2 * len(truth) / (len(pairs) + len(truth)) if truth else 0.0


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
        self.title = {r["risk_id"]: r["title"] for r in rows}
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

    def theme(self, rid: str) -> str:
        """An ERM risk's theme: its title before the entity in brackets ('Sanctions list update delays')."""
        return self.title[rid].split(" (")[0]

    def same_theme_sibling_median(self) -> float:
        """Median cosine of ERM pairs sharing a theme that are not duplicates (L-007's near-copies)."""
        return statistics.median(self.cos(*p) for p in self.erm_pairs
                                 if p not in self.erm_truth and self.theme(p[0]) == self.theme(p[1]))

    def duplicate_median(self) -> float:
        return statistics.median(self.cos(*p) for p in self.erm_truth)

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
            return [e for e in self.erm_ids if distinctive & words(self.title[e] + " " + self.desc[e])]
        return self._best_per_ia(mentions)

    def same_unit_hard_negative_share(self) -> float:
        hard = self.hard_negatives()
        units = lambda r: {self.unit_of[a] for a in self.exposed[r]}
        sharing = [i for i, es in hard.items() if any(units(i) & units(e) for e in es)]
        return len(sharing) / len(hard) if hard else 0.0

    def _erm_links(self):
        """(link is stale, link stays in the home segment) for every ERM exposure link."""
        for e in self.erm_ids:
            units = Counter(self.unit_of[a] for a in self.exposed[e])
            home = units.most_common(1)[0][0]
            for a in self.exposed[e]:
                unit = self.unit_of[a]
                yield unit != home, self.segment_of[unit] == self.segment_of[home]

    def stale_link_share(self) -> float:
        """Share of ERM exposure links pointing to another business unit of the same segment."""
        links = list(self._erm_links())
        return sum(stale and same_segment for stale, same_segment in links) / len(links)

    def cross_segment_links(self) -> int:
        """ERM exposure links into another segment (the stale-link rule allows none)."""
        return sum(stale and not same_segment for stale, same_segment in self._erm_links())


class Controls:
    """Published control data plus the answer key's truth, for one build directory (008)."""

    def __init__(self, out):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        self.erm, self.ia = read(out, "control_erm"), read(out, "control_ia")
        rows = self.erm + self.ia
        self.row = {r["control_id"]: r for r in rows}
        ids = [r["control_id"] for r in rows]
        sims = cosine_similarity(TfidfVectorizer(lowercase=True, ngram_range=(1, 2)).fit_transform(
            [r["description"] for r in rows]))
        index = {cid: i for i, cid in enumerate(ids)}
        self.cos = lambda a, b: float(sims[index[a], index[b]])
        clusters = answer_key(out, "control_clusters")
        self.cluster = {r["control_id"]: r["cluster_id"] for r in clusters}
        self.erm_ids = [r["control_id"] for r in self.erm]
        self.ia_ids = [r["control_id"] for r in self.ia]
        self.pairs = [(e, i) for e in self.erm_ids for i in self.ia_ids]
        same = lambda a, b: self.cluster[a] != "none" and self.cluster[a] == self.cluster[b]
        self.truth = {p for p in self.pairs if same(*p)}

        self.owner, self.systems, self.regulations = {}, defaultdict(set), defaultdict(set)
        self.risks = defaultdict(set)
        for source in ("erm", "ia"):
            self.owner.update({r["control_id"]: r["person_id"]
                               for r in read(out, f"control_owned_by_person_{source}")})
            for r in read(out, f"control_depends_on_system_{source}"):
                self.systems[r["control_id"]].add(r["system_id"])
            for r in read(out, f"regulation_requires_control_{source}"):
                self.regulations[r["control_id"]].add(r["regulation_id"])
            for r in read(out, f"control_mitigates_risk_{source}"):
                self.risks[r["control_id"]].add(r["risk_id"])
        self.exposed = defaultdict(set)
        for source in ("erm", "ia"):
            for r in read(out, f"auditable_entity_exposed_to_risk_{source}"):
                self.exposed[r["risk_id"]].add(r["auditable_entity_id"])
        self.unit_of = {r["auditable_entity_id"]: r["business_unit_id"]
                        for r in read(out, "business_unit_owns_auditable_entity")}
        self.entity_name = {r["auditable_entity_id"]: r["name"] for r in read(out, "auditable_entity")}
        risk_rows = answer_key(out, "risk_clusters")
        self.risk_cluster = {r["risk_id"]: r["cluster_id"] for r in risk_rows}
        self.risk_source = {r["risk_id"]: r["source"] for r in risk_rows}

    def entities(self, cid):
        return {a for risk in self.risks[cid] for a in self.exposed[risk]}

    # --- AC-1 -----------------------------------------------------------------------------
    def overlap(self) -> float:
        return len({i for _, i in self.truth}) / len(self.ia_ids)

    def orphan_share(self, source: str) -> float:
        ids = self.erm_ids if source == "erm" else self.ia_ids
        return sum(not self.risks[c] for c in ids) / len(ids)

    def max_erm_per_cluster(self) -> int:
        return max(Counter(self.cluster[e] for e in self.erm_ids if self.cluster[e] != "none").values())

    def detail_share(self) -> float:
        words = lambda c: len(self.row[c]["description"].split())
        return sum(words(i) >= 2 * words(e) for e, i in self.truth) / len(self.truth)

    def frequency_disagreement(self) -> float:
        return sum(self.row[e]["frequency"] != self.row[i]["frequency"] for e, i in self.truth) / len(self.truth)

    def owners_always_differ(self) -> bool:
        return all(self.owner[e] != self.owner[i] for e, i in self.truth)

    # --- AC-4 -----------------------------------------------------------------------------
    def exact_text_f1(self) -> float:
        return _f1({p for p in self.pairs if self.row[p[0]]["description"] == self.row[p[1]]["description"]},
                   self.truth)

    def owner_frequency_f1(self) -> float:
        return _f1({(e, i) for e, i in self.pairs if self.owner[e] == self.owner[i]
                    and self.row[e]["frequency"] == self.row[i]["frequency"]}, self.truth)

    def tfidf_f1(self) -> float:
        return _best_threshold_f1({p: self.cos(*p) for p in self.pairs}, self.truth)

    def hard_negative_rate(self) -> float:
        median = statistics.median(self.cos(*p) for p in self.truth)
        hard = {i for e, i in self.pairs if (e, i) not in self.truth and self.cos(e, i) >= median}
        return len(hard) / len(self.ia_ids)

    # --- AC-5 -----------------------------------------------------------------------------
    def attribute_f1(self) -> float:
        key = lambda c: (self.row[c]["control_type"], self.row[c]["nature"], self.row[c]["frequency"])
        return _f1({(e, i) for e, i in self.pairs if key(e) == key(i)}, self.truth)

    def system_f1(self) -> float:
        return _f1({(e, i) for e, i in self.pairs if self.systems[e] & self.systems[i]}, self.truth)

    def regulation_f1(self) -> float:
        return _f1({(e, i) for e, i in self.pairs if self.regulations[e] & self.regulations[i]}, self.truth)

    def _best_per_ia(self, candidates) -> float:
        best = {}
        for i in self.ia_ids:
            options = candidates(i)
            if options:
                e = max(options, key=lambda e: self.cos(e, i))
                best[(e, i)] = self.cos(e, i)
        return _best_threshold_f1(best, self.truth)

    def system_text_f1(self) -> float:
        return self._best_per_ia(lambda i: [e for e in self.erm_ids if self.systems[e] & self.systems[i]])

    def unit_text_f1(self) -> float:
        def candidates(i):
            units = {self.unit_of[a] for a in self.entities(i)}
            return [e for e in self.erm_ids if units & {self.unit_of[a] for a in self.entities(e)}]
        return self._best_per_ia(candidates)

    def entity_mention_f1(self) -> float:
        words = lambda text: set(re.findall(r"[a-z]+", text.lower()))
        name_words = Counter(w for n in self.entity_name.values() for w in words(n))

        def candidates(i):
            distinctive = {w for a in self.entities(i) for w in words(self.entity_name[a]) if name_words[w] <= 3}
            return [e for e in self.erm_ids
                    if distinctive & words(self.row[e]["title"] + " " + self.row[e]["description"])]
        return self._best_per_ia(candidates)

    def subject_kind_f1(self, labels: list) -> float:
        """Pair controls whose titles share every word of a kind label and at least two other words."""
        words = lambda text: set(re.findall(r"[a-z]+", text.lower()))
        label_words = [words(label) for pair in labels for label in pair]
        titles = {c: words(self.row[c]["title"]) for c in self.erm_ids + self.ia_ids}
        predicted = set()
        for e, i in self.pairs:
            shared = titles[e] & titles[i]
            if any(lw <= shared and len(shared - lw) >= 2 for lw in label_words):
                predicted.add((e, i))
        return _f1(predicted, self.truth)

    def title_in_description_f1(self) -> float:
        """Pair an IA control with the only ERM control whose title words all appear in its description."""
        words = lambda text: set(re.findall(r"[a-z]+", text.lower()))
        titles = {e: words(self.row[e]["title"]) for e in self.erm_ids}
        predicted = set()
        for i in self.ia_ids:
            desc = words(self.row[i]["description"])
            hits = [e for e, t in titles.items() if t <= desc]
            if len(hits) == 1:
                predicted.add((hits[0], i))
        return _f1(predicted, self.truth)

    def subject_citation_f1(self, with_kind_map: bool = False) -> float:
        """008 review's measure: pair an IA control with every ERM control whose title subject (before ':')
        occurs in the IA description and that agrees on control type and nature; with the 8-entry map from
        IA's citation phrase to ERM's kind label, also require the cited kind to match ERM's label."""
        from src.features.generator import library

        label_of_phrase = {library.IA_CITATION[k.key]: k.erm_label.lower() for k in library.CONTROL_KINDS}
        predicted = set()
        for e, i in self.pairs:
            erm, ia = self.row[e], self.row[i]
            if ":" not in erm["title"]:
                continue
            subject, label = (part.strip().lower() for part in erm["title"].split(":", 1))
            desc = ia["description"].lower()
            if subject not in desc or (erm["control_type"], erm["nature"]) != (ia["control_type"], ia["nature"]):
                continue
            if with_kind_map and not any(p in desc and l == label for p, l in label_of_phrase.items()):
                continue
            predicted.add((e, i))
        return _f1(predicted, self.truth)

    def count_cue(self, source: str) -> float:
        """|mean controls per risk on matched risks - on unmatched risks| for one source."""
        ids = self.erm_ids if source == "erm" else self.ia_ids
        per_risk = Counter(r for c in ids for r in self.risks[c])
        cluster_sources = defaultdict(set)
        for r, s in self.risk_source.items():
            if self.risk_cluster[r] != "none":
                cluster_sources[self.risk_cluster[r]].add(s)
        matched = lambda r: cluster_sources.get(self.risk_cluster[r]) == {"ERM", "IA"}
        risks = [r for r, s in self.risk_source.items() if s == source.upper()]
        a = [per_risk[r] for r in risks if matched(r)]
        b = [per_risk[r] for r in risks if not matched(r)]
        return abs(statistics.mean(a) - statistics.mean(b))


def repeat_finding_cue(out) -> tuple[float, float]:
    """(recall, pair precision) of grouping IA issues by their text after the fixed opening words:
    the share of planted repeat groups that land in one bucket, and how many same-bucket pairs are
    issues on the same IA control (009 review's measure; the cue docs/data-model.md publishes)."""
    from src.features.generator.text_rules import ISSUE_OPENING

    issues = [r for r in read(out, "issue") if r["source"] == "IA"]
    finding = {r["issue_id"]: ISSUE_OPENING.sub("", r["description"]).strip().lower() for r in issues}
    groups = defaultdict(set)
    for row in answer_key(out, "scenarios"):
        if row["scenario"].startswith("repeat_finding:") and row["item_id"] in finding:
            groups[row["scenario"]].add(row["item_id"])
    buckets = defaultdict(set)
    for iid, text in finding.items():
        buckets[text].add(iid)
    recall = sum(any(ids <= b for b in buckets.values()) for ids in groups.values()) / len(groups)
    control_of = {r["issue_id"]: r["control_id"] for r in read(out, "issue_against_control_ia")}
    same = total = 0
    for bucket in buckets.values():
        ids = sorted(bucket)
        for n, a in enumerate(ids):
            for b in ids[n + 1:]:
                total += 1
                same += a in control_of and control_of.get(a) == control_of.get(b)
    return recall, (same / total if total else 0.0)


def cue_figures(out) -> dict[str, float]:
    """Every figure docs/data-model.md publishes about matching cues and difficulty (010 AC-5)."""
    r, c = Risks(out), Controls(out)
    recall, precision = repeat_finding_cue(out)
    return {
        "control_title_in_description_f1": c.title_in_description_f1(),
        "control_subject_citation_f1": c.subject_citation_f1(),
        "control_subject_citation_kind_map_f1": c.subject_citation_f1(with_kind_map=True),
        "control_tfidf_f1": c.tfidf_f1(),
        "control_chance_f1": chance_f1(c.pairs, c.truth),
        "risk_tfidf_f1": r.tfidf_f1(),
        "erm_duplicate_f1": r.erm_duplicate_f1(),
        "erm_duplicate_median_cosine": r.duplicate_median(),
        "erm_same_theme_sibling_median_cosine": r.same_theme_sibling_median(),
        "repeat_finding_recall": recall,
        "repeat_finding_pair_precision": precision,
    }
