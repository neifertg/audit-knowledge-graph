"""Figures derived from rounds.json for the page's prose (021). Tests recompute each independently."""


def verdict_counts(rounds: dict) -> dict:
    counts = {"SQL": 0, "graph": 0, "close": 0}
    for r in rounds["rounds"]:
        counts[r["measured_verdict"]] += 1
    return counts


def rounds_count(rounds: dict) -> int:
    return len(rounds["rounds"])


def differ_from_expected(rounds: dict) -> int:
    return sum(r["measured_verdict"] != r["expected_verdict"] for r in rounds["rounds"])


def near_the_line(rounds: dict) -> list:
    """Rounds whose margin is within one point of the 1.25 line."""
    return [r["number"] for r in rounds["rounds"] if abs(r["margin"]) <= 1]


DERIVED = {f.__name__: f for f in (verdict_counts, rounds_count, differ_from_expected, near_the_line)}
