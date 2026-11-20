"""AC-7: items in one true cluster share no ID number, sentence, near-identical text or row order."""
import re
import statistics
import unittest
from collections import defaultdict

from .helpers import answer_key, build, cosine_by_id, read, sentences


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


class LeakageTests(unittest.TestCase):
    def check_kind(self, out, kind: str):
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
            for i, (_, a) in enumerate(items):
                for _, b in items[i + 1:]:
                    self.assertFalse(set(re.findall(r"\d+", a)) & set(re.findall(r"\d+", b)),
                                     f"{a} and {b} share an ID number")
                    shared = sentences(by_id[a]["description"]) & sentences(by_id[b]["description"])
                    self.assertFalse(shared, f"{a} and {b} share a sentence: {shared}")
                    self.assertLess(sims[(a, b)], 0.90, f"{a} and {b} are near-copies")
                    pair_sims.append(sims[(a, b)])
                    if kind == "control":
                        ra, rb = by_id[a], by_id[b]
                        same = (owner[a] == owner[b], ra["frequency"] == rb["frequency"],
                                ra["control_type"] == rb["control_type"])
                        self.assertFalse(all(same), f"{a} and {b} have identical owner, frequency and type")
        self.assertLess(statistics.median(pair_sims), 0.70)

        cross = [items for items in members.values() if {s for s, _ in items} == {"ERM", "IA"}]
        erm_pos = [min(position[i] for s, i in items if s == "ERM") for items in cross]
        ia_pos = [min(position[i] for s, i in items if s == "IA") for items in cross]
        self.assertLess(abs(spearman(erm_pos, ia_pos)), 0.8, "matched items sit in the same order in both files")

    def test_ac7_matched_items_share_no_id_sentence_attributes_or_order(self):
        for text in ("templated", "ai"):
            out = build("--text", text)
            for kind in ("risk", "control"):
                with self.subTest(text=text, kind=kind):
                    self.check_kind(out, kind)


if __name__ == "__main__":
    unittest.main()
