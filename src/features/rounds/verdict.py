"""The measured verdict for a pair of queries (E3 child c, change 017, AC-2).

Pure and round-agnostic, so child d reuses it unchanged. Each side scores
`clauses + steps + 5 * moving_parts`; the side whose score times 1.25 is at most the other's
wins, else the verdict is `close`. Counted outside comments and string literals:
- clauses: whole-word clause keywords (multi-word tokens as one); in Cypher, keywords inside
  (...) or [...] are expressions, not clauses. Clauses, not lines, so layout cannot move a score.
- steps: SQL, every FROM/JOIN target (table, view, CTE name or parenthesised subquery) minus one;
  Cypher, every relationship pattern in any form, including inside { } subqueries.
- moving_parts: SQL, every SELECT beyond the first, plus RECURSIVE and write or DDL statements;
  Cypher, every WITH stage outside (...)/[...] (including inside { }), every { } subquery and UNION,
  plus write clauses.
"""
import re

WEIGHT = 5
MARGIN = 1.25

SQL_CLAUSES = (r"WITH\s+RECURSIVE|WITH|SELECT|FROM|(?:LEFT\s+|INNER\s+|CROSS\s+)?JOIN|WHERE|GROUP\s+BY|HAVING"
               r"|ORDER\s+BY|LIMIT|UNION(?:\s+ALL)?")
CYPHER_CLAUSES = (r"OPTIONAL\s+MATCH|MATCH|WHERE|WITH|RETURN|ORDER\s+BY|LIMIT|UNION(?:\s+ALL)?|CALL|UNWIND"
                  r"|CREATE|MERGE|SET|DELETE|REMOVE")
SQL_WRITES = r"CREATE|ALTER|DROP|INSERT|UPDATE|DELETE"
CYPHER_WRITES = r"CREATE|MERGE|SET|DELETE|REMOVE"
COMMENT = {"sql": "--", "cypher": "//"}


def _clean(text: str, engine: str) -> str:
    """Upper-cased code without comment lines, string literals, or the STARTS/ENDS WITH operators."""
    lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith(COMMENT[engine])]
    code = re.sub(r"'(?:[^']|'')*'", "''", "\n".join(lines)).upper()
    return re.sub(r"\b(?:STARTS|ENDS)\s+WITH\b", "OP", code)


def top_level(code: str) -> str:
    """Blank out everything inside (...) and [...] (Cypher expressions and patterns); braces and
    newlines are kept, so line positions survive."""
    out, depth = [], 0
    for ch in code:
        if ch == "\n":
            out.append(ch)
        elif ch in "([":
            depth += 1
            out.append(" ")
        elif ch in ")]":
            depth = max(depth - 1, 0)
            out.append(" ")
        else:
            out.append(ch if depth == 0 else " ")
    return "".join(out)


def _count(pattern: str, code: str) -> int:
    return len(re.findall(rf"\b(?:{pattern})\b", code))


def metrics(text: str, engine: str) -> dict:
    """{'clauses', 'steps', 'moving_parts'} for one query; engine is 'sql' or 'cypher'."""
    code = _clean(text, engine)
    if engine == "sql":
        recursive = _count("RECURSIVE", code)
        clauses = _count(SQL_CLAUSES, code)
        steps = len(re.findall(r"\b(?:FROM|JOIN)\s+(?:\w+|\()", code)) - 1
        moving = _count("SELECT", code) - 1 + recursive + _count(SQL_WRITES, code)
    elif engine == "cypher":
        outer = top_level(code)
        clauses = _count(CYPHER_CLAUSES, outer)
        steps = len(re.findall(r"<?-\[[^\]]*\]->?|<--|-->|(?<![<\-])--(?![>\-])", code))
        moving = (_count("WITH", outer) + len(re.findall(r"\b(?:CALL|EXISTS|COUNT|COLLECT)\s*\{", code))
                  + _count("UNION", outer) + _count(CYPHER_WRITES, outer))
    else:
        raise ValueError(f"unknown engine {engine!r}")
    return {"clauses": clauses, "steps": max(steps, 0), "moving_parts": max(moving, 0)}


def clauses_per_line(text: str, engine: str) -> list[int]:
    """Clause keywords on each code line (comments dropped), for the layout rule in AC-1."""
    code = _clean(text, engine)
    if engine == "cypher":
        code = top_level(code)
    pattern = SQL_CLAUSES if engine == "sql" else CYPHER_CLAUSES
    return [_count(pattern, line) for line in code.splitlines()]


def score(m: dict) -> int:
    return m["clauses"] + m["steps"] + WEIGHT * m["moving_parts"]


def measured(sql_metrics: dict, cypher_metrics: dict) -> str:
    """'SQL', 'graph' or 'close'."""
    s, c = score(sql_metrics), score(cypher_metrics)
    if s * MARGIN <= c:
        return "SQL"
    if c * MARGIN <= s:
        return "graph"
    return "close"
