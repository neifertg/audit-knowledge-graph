"""The measured verdict for a pair of queries (E3 children c and d; changes 017 and 018).

Pure and round-agnostic. Each side scores `clauses + steps + 5 * moving_parts`; the side whose
score times 1.25 is at most the other's wins, else the verdict is `close`. Moving parts follow one
rule on both sides (owner decisions 2026-11-21, changes 018 and 020), with two disclosed exceptions:
filtering after an aggregate (SQL's HAVING is a clause, Cypher's WITH stage a moving part) and
upserts. Clauses and steps measure what each language writes. Counted outside comments and string
literals:
- clauses: whole-word clause keywords (multi-word tokens as one). JOIN and the Cypher writes are
  layout keywords but not scored clauses: a join counts once, as a step, and a write once, as a
  moving part. In Cypher, keywords inside (...) or [...] are expressions, not clauses; OPTIONAL MATCH
  is a clause like every MATCH.
- steps: SQL, every FROM/JOIN target (table, view, CTE name or parenthesised subquery) minus one,
  not counting a FROM inside a function call or a DELETE FROM. Cypher, every relationship pattern;
  a fixed `*n` or bounded `*m..n` / `*..n` counts n hops, an unbounded one (`*`, `*m..`) one hop.
- moving_parts: SQL, every SELECT beyond the first (a CTE, subquery or union branch), except the
  SELECTs inside a recursive CTE's body, plus RECURSIVE and write or DDL statements. Cypher, every
  WITH stage outside (...)/[...] (including inside { }), every { } subquery and UNION, every
  unbounded variable-length pattern (recursion, as RECURSIVE is in SQL), plus write clauses.
A round with setup is scored as one text: the setup followed by the query.
"""
import re

WEIGHT = 5
MARGIN = 1.25

# Scored clauses. SQL_LAYOUT adds JOIN for the one-clause-per-line style check (017 AC-1).
SQL_CLAUSES = r"WITH\s+RECURSIVE|WITH|SELECT|FROM|WHERE|GROUP\s+BY|HAVING|ORDER\s+BY|LIMIT|UNION(?:\s+ALL)?"
SQL_LAYOUT = SQL_CLAUSES + r"|(?:LEFT\s+|INNER\s+|CROSS\s+)?JOIN"
CYPHER_CLAUSES = r"OPTIONAL\s+MATCH|MATCH|WHERE|WITH|RETURN|ORDER\s+BY|LIMIT|UNION(?:\s+ALL)?|CALL|UNWIND"
SQL_WRITES = r"CREATE|ALTER|DROP|INSERT|UPDATE|DELETE"
CYPHER_WRITES = r"CREATE|MERGE|SET|DELETE|REMOVE"
# A write counts once, as a moving part, on both sides (020): it is not a scored clause. It stays a
# line-start keyword for the layout check, as JOIN does in SQL_LAYOUT.
CYPHER_LAYOUT = CYPHER_CLAUSES + "|" + CYPHER_WRITES
COMMENT = {"sql": "--", "cypher": "//"}
# Words that may precede "(" without being a function call.
SQL_NOT_FUNCTIONS = {"IN", "EXISTS", "AS", "FROM", "JOIN", "ON", "VALUES", "AND", "OR", "NOT", "WHERE",
                     "SELECT", "USING", "WHEN", "THEN", "ELSE", "ALL", "ANY", "HAVING", "BY"}
RELATIONSHIP = re.compile(r"<?-\[([^\]]*)\]->?|<--|-->|(?<![<\-])--(?![>\-])")
VAR_LENGTH = re.compile(r"\*\s*(\d*)\s*(\.\.)?\s*(\d*)")


def _clean(text: str, engine: str) -> str:
    """Upper-cased code without comments (whole-line or trailing), string literals, or the
    STARTS/ENDS WITH operators."""
    code = re.sub(r"'(?:[^']|'')*'", "''", text)
    marker = COMMENT[engine]
    lines = [line.split(marker, 1)[0] for line in code.splitlines()]
    code = "\n".join(line for line in lines if line.strip()).upper()
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


def _paren_end(code: str, start: int) -> int:
    """Index just past the parenthesis that closes the one opened before `start`."""
    depth, i = 1, start
    while depth and i < len(code):
        depth += {"(": 1, ")": -1}.get(code[i], 0)
        i += 1
    return i


def _blank_function_calls(code: str) -> str:
    """Blank the arguments of SQL function calls (COUNT(...), trim(... FROM x)), keeping keyword
    parentheses such as IN (SELECT ...), EXISTS (...), AS (...) and FROM (...)."""
    out, i = list(code), 0
    for m in re.finditer(r"\b(\w+)\s*\(", code):
        if m.start() < i or m.group(1) in SQL_NOT_FUNCTIONS:
            continue
        end = _paren_end(code, m.end())
        for j in range(m.end(), end - 1):
            if out[j] != "\n":
                out[j] = " "
        i = end
    return "".join(out)


def _recursive_body_selects(code: str) -> int:
    n = 0
    for m in re.finditer(r"\bRECURSIVE\s+\w+\s*(?:\([^)]*\))?\s*AS\s*\(", code):
        n += len(re.findall(r"\bSELECT\b", code[m.end():_paren_end(code, m.end())]))
    return n


def _count(pattern: str, code: str) -> int:
    return len(re.findall(rf"\b(?:{pattern})\b", code))


def metrics(text: str, engine: str) -> dict:
    """{'clauses', 'steps', 'moving_parts'} for one text; engine is 'sql' or 'cypher'."""
    code = _clean(text, engine)
    if engine == "sql":
        code = _blank_function_calls(code)
        recursive = _count("RECURSIVE", code)
        clauses = _count(SQL_CLAUSES, code)
        targets = len(re.findall(r"\b(?:FROM|JOIN)\s+(?:\w+|\()", code)) - len(re.findall(r"\bDELETE\s+FROM\b", code))
        steps = max(targets - 1, 0)
        selects = _count("SELECT", code) - _recursive_body_selects(code)
        moving = max(selects - 1, 0) + recursive + _count(SQL_WRITES, code)
    elif engine == "cypher":
        outer = top_level(code)
        clauses = _count(CYPHER_CLAUSES, outer)
        steps, unbounded = 0, 0
        for m in RELATIONSHIP.finditer(code):
            length = VAR_LENGTH.search(m.group(1) or "")
            if not length:
                steps += 1
                continue
            lo, dots, hi = length.groups()
            if (dots and not hi) or (not dots and not lo):
                steps += 1
                unbounded += 1
            else:
                steps += int(hi if dots else lo)
        moving = (_count("WITH", outer) + len(re.findall(r"\b(?:CALL|EXISTS|COUNT|COLLECT)\s*\{", code))
                  + _count("UNION", outer) + _count(CYPHER_WRITES, outer) + unbounded)
    else:
        raise ValueError(f"unknown engine {engine!r}")
    return {"clauses": clauses, "steps": steps, "moving_parts": moving}


def clauses_per_line(text: str, engine: str) -> list[int]:
    """Clause keywords on each code line (comments dropped), for the layout rule; JOIN counts here."""
    code = _clean(text, engine)
    if engine == "cypher":
        code = top_level(code)
    pattern = SQL_LAYOUT if engine == "sql" else CYPHER_LAYOUT
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


def margin(sql_metrics: dict, cypher_metrics: dict) -> float:
    """How far the verdict is past the 1.25 line: max - 1.25 * min. Zero or more is a winner
    (zero: exactly on the line); negative is `close`."""
    s, c = score(sql_metrics), score(cypher_metrics)
    return round(max(s, c) - MARGIN * min(s, c), 2)
