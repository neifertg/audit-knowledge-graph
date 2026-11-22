"""Figures derived from the exports for the page's prose (021, 022). Tests recompute each independently.

Each function takes the loaded sources ({'rounds.json': ..., 'site.json': ..., 'scores.json': ...}).
"""
SHOWN = 5   # rows of each answer shown on the page


def _rounds(sources: dict) -> list:
    return sources["rounds.json"]["rounds"]


def verdict_counts(sources: dict) -> dict:
    counts = {"SQL": 0, "graph": 0, "close": 0}
    for r in _rounds(sources):
        counts[r["measured_verdict"]] += 1
    return counts


def rounds_count(sources: dict) -> int:
    return len(_rounds(sources))


def differ_from_expected(sources: dict) -> int:
    return sum(r["measured_verdict"] != r["expected_verdict"] for r in _rounds(sources))


def near_the_line(sources: dict) -> list:
    """Rounds whose margin is within one point of the 1.25 line."""
    return [r["number"] for r in _rounds(sources) if abs(r["margin"]) <= 1]


def rounds_by_verdict(sources: dict) -> dict:
    by = {"SQL": [], "graph": [], "close": []}
    for r in _rounds(sources):
        by[r["measured_verdict"]].append(r["number"])
    return by


def _m(r: dict, side: str, field: str) -> int:
    return r["metrics"][side][field]


def graph_rule(sources: dict) -> list:
    """Rounds with equal moving parts on both sides and more SQL steps (joins) than Cypher steps (hops)."""
    return [r["number"] for r in _rounds(sources)
            if _m(r, "sql", "moving_parts") == _m(r, "cypher", "moving_parts") and _m(r, "sql", "steps") > _m(r, "cypher", "steps")]


def close_steps(sources: dict) -> list:
    """Close rounds where SQL's steps are no more than Cypher's."""
    return [r["number"] for r in _rounds(sources)
            if r["measured_verdict"] == "close" and _m(r, "sql", "steps") <= _m(r, "cypher", "steps")]


def close_moving(sources: dict) -> list:
    """Close rounds where Cypher needs more moving parts than SQL."""
    return [r["number"] for r in _rounds(sources)
            if r["measured_verdict"] == "close" and _m(r, "cypher", "moving_parts") > _m(r, "sql", "moving_parts")]


def disclosed_count(sources: dict) -> int:
    return sum(row["disclosed"] for row in sources["site.json"]["symmetry"])


def shown_rows(sources: dict) -> dict:
    """[rows shown on the page, rows in the answer], by round number (owner concentration as 'owners')."""
    out = {}
    for r in _rounds(sources) + sources["rounds.json"]["supporting"]:
        out[str(r["number"])] = [min(SHOWN, len(r["rows"])), r["row_count"]]
    return out


DERIVED = {f.__name__: f for f in (verdict_counts, rounds_count, differ_from_expected, near_the_line, rounds_by_verdict,
                                   graph_rule, close_steps, close_moving, disclosed_count, shown_rows)}
