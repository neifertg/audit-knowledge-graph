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


def _by_number(sources: dict) -> dict:
    return {r["number"]: r for r in _rounds(sources)}


def featured(sources: dict) -> dict:
    """Brief figures already stored on the rounds: row counts, the cutoff, the vendor, the top riser.

    The year labels are the top-riser object's own year keys, not a second calendar.
    """
    by = _by_number(sources)
    riser = by[7]["top_riser"]
    years = sorted(k for k in riser if str(k).isdigit())
    published = {row[2]: row[3] for row in by[7]["rows"] if row[1] == riser["l1_name"]}
    middle = [y for y in sorted(published) if y not in (years[0], years[-1])]
    if len(middle) != 1:
        raise ValueError("the top riser's published rows do not have one year between the endpoints")
    return {"stale_rows": by[2]["row_count"],
            "stale_cutoff": sources["rounds.json"]["parameters"]["round_2_cutoff"],
            "vendor": sources["rounds.json"]["parameters"]["round_5_vendor"],
            "vendor_rows": by[5]["row_count"],
            "yoy_name": riser["l1_name"],
            "yoy_from_year": years[0], "yoy_to_year": years[-1],
            "yoy_from": riser[years[0]], "yoy_to": riser[years[-1]],
            "yoy_mid_year": middle[0], "yoy_mid": published[middle[0]]}


def fourth_party(sources: dict) -> dict:
    """Direct vs fourth-party-only. Round 5 publishes every row, so this is the answer, not a sample."""
    r = _by_number(sources)[5]
    if len(r["rows"]) != r["row_count"]:
        raise ValueError("round 5's published rows are incomplete; refusing a partial count")
    column = r["columns"].index("exposure")
    counts = {"direct": 0, "fourth_party_only": 0}
    for row in r["rows"]:
        counts[row[column]] += 1
    return counts


def showcase(_sources: dict) -> dict:
    """This page publishes one synthetic bank from one generator.

    The executive summary says that in words ("One synthetic bank, one generator").
    These are constants of the showcase, not counts read from the exports.
    """
    return {"banks": 1, "generators": 1}


def shown_rows(sources: dict) -> dict:
    """[rows shown on the page, rows in the answer], by round number (owner concentration as 'owners')."""
    out = {}
    for r in _rounds(sources) + sources["rounds.json"]["supporting"]:
        out[str(r["number"])] = [min(SHOWN, len(r["rows"])), r["row_count"]]
    return out


DERIVED = {f.__name__: f for f in (verdict_counts, rounds_count, differ_from_expected, near_the_line, rounds_by_verdict,
                                   graph_rule, close_steps, close_moving, disclosed_count, shown_rows,
                                   featured, fourth_party, showcase)}
