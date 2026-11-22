"""Named formatters for rendered figures (021). Shared by the builder and the tests, each unit-tested.

A marked element is `<span data-source="..." data-format="name">text</span>`; its text is
`FORMATTERS[name](value)`, where `value` is the resolved source (a list when the source names several
comma-separated paths).
"""
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
         10: "ten", 11: "eleven", 12: "twelve"}


def plain(value) -> str:
    return str(value)


def count_word(value: int) -> str:
    """seven, three; a number above twelve is written in digits."""
    return WORDS.get(value, str(value))


def times_word(value: int) -> str:
    """once, twice, three times."""
    if value == 1:
        return "once"
    if value == 2:
        return "twice"
    return f"{count_word(value)} times"


def signed(value: float) -> str:
    """+4.75, -0.75, +0.00."""
    return f"{value:+.2f}"


def fraction(value) -> str:
    """[33, 33] -> 33/33."""
    numerator, denominator = value
    return f"{numerator}/{denominator}"


def rows_shown(value) -> str:
    """[shown, total] -> '20 of 61 rows', or '14 rows' when nothing is cut."""
    shown, total = value
    return f"{total} rows" if shown == total else f"{shown} of {total} rows"


def names_and(value) -> str:
    """['A', 'B', 'C'] -> 'A, B and C'; numbers are written as they are ([1, 6, 7] -> '1, 6 and 7')."""
    names = [str(v) for v in value]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def verdict(value) -> str:
    """A measured or expected verdict; a supporting query has no expected verdict."""
    return "none (supporting query)" if value is None else str(value)


def check(value) -> str:
    """An agreement or oracle check: True passed, False failed, 'not run' as is."""
    if value is True:
        return "passed"
    if value is False:
        return "failed"
    return str(value)


def scenario(value) -> str:
    """A round's planted scenario and its rule, or 'none planted'."""
    return "none planted" if value is None else f"{value['planted']} ({value['rule']})"


def triple(value) -> str:
    """[clauses, steps, moving parts] -> '5 / 1 / 1'."""
    return " / ".join(str(v) for v in value)


FORMATTERS = {f.__name__: f for f in (plain, count_word, times_word, signed, fraction, rows_shown, names_and,
                                      verdict, check, scenario, triple)}
