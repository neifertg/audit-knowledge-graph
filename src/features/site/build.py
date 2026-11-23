"""Render the page from committed exports (021). Standard library only; reads no build or database.

    python -m src.features.site.build --out <dir>       writes <dir>/index.html, methods.html and the files they link

Template syntax in template.html:
- `{{<source>|<format>}}` becomes `<span data-source="<source>" data-format="<format>">text</span>`, where
  <source> is `site.json:<path>`, `rounds.json:<path>`, `scores.json:<path>` or `derived:<name>.<path>`,
  several sources may be joined by commas, and a path uses dots, `[i]` and `[*]` (every item).
- `{{@graph-data}}` embeds site.json's subgraph as `<script type="application/json" id="site-data">`.
- `{{@unit-table}}` renders the blast radius per business unit, every cell marked.
No figure is typed into the template; tests check every marked figure against its source.
"""
import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

from .derived import DERIVED, SHOWN
from .formatters import FORMATTERS

HERE = Path(__file__).parent
FEATURES = HERE.parent
# Paths, not imports: the builder runs with the standard library only (CI and the Pages workflow), and
# the modules that own these files import heavier packages.
SITE_JSON = HERE / "data" / "site.json"
ROUNDS_JSON = FEATURES / "rounds" / "rounds.json"
SCORES = FEATURES / "reconciliation" / "scores.json"
TEMPLATE = HERE / "template.html"
METHODS = HERE / "methods.html"
STATIC = ("site.css", "site.js")
PLACEHOLDER = re.compile(r"\{\{\s*([^}|]+?)\s*(?:\|\s*(\w+)\s*)?\}\}")


def load_sources() -> dict:
    return {"site.json": json.loads(SITE_JSON.read_text(encoding="utf-8")),
            "rounds.json": json.loads(ROUNDS_JSON.read_text(encoding="utf-8")),
            "scores.json": json.loads(SCORES.read_text(encoding="utf-8"))}


def walk(value, path: str):
    """Follow a path of `.key`, `[i]` and `[*]` steps."""
    for step in re.findall(r"\[\*\]|\[\d+\]|[^.\[\]]+", path):
        if step == "[*]":
            return [walk(item, path.split("[*]", 1)[1].lstrip(".")) for item in value]
        value = value[int(step[1:-1])] if step.startswith("[") else value[step]
    return value


def resolve(source: str, sources: dict):
    """The value one source names; a comma-separated source gives a list."""
    if "," in source:
        return [resolve(part.strip(), sources) for part in source.split(",")]
    name, _, path = source.partition(":")
    if name == "derived":
        function, _, rest = path.partition(".")
        return walk(DERIVED[function](sources), rest) if rest else DERIVED[function](sources)
    return walk(sources[name], path)


def marked(source: str, fmt: str, sources: dict, tag: str = "span") -> str:
    text = FORMATTERS[fmt](resolve(source, sources))
    return f'<{tag} data-source="{html.escape(source)}" data-format="{fmt}">{html.escape(text)}</{tag}>'


def code(source: str, sources: dict) -> str:
    return f'<pre class="code">{marked(source, "plain", sources, "code")}</pre>'


def one_round(base: str, r: dict, sources: dict) -> str:
    """One round (or the supporting query) with its queries, figures, checks and first rows (022 AC-1)."""
    m = lambda path, fmt="plain": marked(f"{base}.{path}", fmt, sources)
    key = str(r["number"])
    if r["supporting"]:
        heading = (f'<h3>Owner concentration <span class="tag" data-label="derived">supporting query; derived, not planted'
                   f'</span></h3><p class="question">{m("question")}</p>')
        scenario = m("checks.scenario", "scenario_supporting")
    else:
        heading = f'<h3>Round {m("number")}</h3><p class="question">{m("question")}</p>'
        scenario = m("checks.scenario", "scenario")
    rows = r["rows"][:SHOWN]   # the same constant derived.shown_rows reports
    head = "".join(f"<th scope=\"col\">{m(f'columns[{j}]')}</th>" for j, _ in enumerate(r["columns"]))
    body = "\n".join("<tr>" + "".join(f"<td>{m(f'rows[{i}][{j}]')}</td>" for j, _ in enumerate(row)) + "</tr>"
                     for i, row in enumerate(rows))
    truncated = (f'<p class="note">The full answer is reproducible from a fresh clone; the published export keeps its first '
                 f'rows: <a href="rounds.json">rounds.json</a>.</p>' if len(r["rows"]) < r["row_count"] else "")
    riser = ""
    if r.get("top_riser"):
        riser = (f'<p><strong>Top riser:</strong> {m("top_riser.l1_name")}, from {m("top_riser.2023")} to '
                 f'{m("top_riser.2025")}.</p>')
    return f"""<article class="round" id="round-{html.escape(key)}">
{heading}
<dl class="facts">
<dt>Score</dt><dd>SQL {m("scores.sql")} against Cypher {m("scores.cypher")}</dd>
<dt>Margin</dt><dd>{m("margin", "signed")}</dd>
<dt>Measured verdict</dt><dd>{m("measured_verdict", "verdict")}</dd>
<dt>Agreement</dt><dd>{m("checks.agreement", "check")}</dd>
<dt>Oracle</dt><dd>{m("checks.oracle", "check")}</dd>
<dt>Scenario</dt><dd>{scenario}</dd>
</dl>
<div class="pair"><div><h4>SQL</h4>{code(base + ".sql", sources)}</div><div><h4>Cypher</h4>{code(base + ".cypher", sources)}</div></div>
<div class="scroll"><table class="data"><caption>First rows: {marked(f"derived:shown_rows.{key}", "rows_shown", sources)}</caption>
<thead><tr>{head}</tr></thead><tbody>
{body}
</tbody></table></div>
{truncated}{riser}
</article>"""


def rounds_block(sources: dict) -> str:
    doc = sources["rounds.json"]
    parts = [one_round(f"rounds.json:rounds[{i}]", r, sources) for i, r in enumerate(doc["rounds"])]
    parts += [one_round(f"rounds.json:supporting[{i}]", r, sources) for i, r in enumerate(doc["supporting"])]
    return "\n".join(parts)


def counting_block(sources: dict) -> str:
    items = sources["rounds.json"]["verdict_rule"]["counting"]
    return "\n".join(f"<li>{marked(f'rounds.json:verdict_rule.counting[{i}]', 'plain', sources)}</li>" for i, _ in enumerate(items))


def symmetry_block(sources: dict) -> str:
    rows = []
    for i, row in enumerate(sources["site.json"]["symmetry"]):
        base = f"site.json:symmetry[{i}]"
        tag = ' <span class="tag">disclosed</span>' if row["disclosed"] else ""
        rows.append(f"<tr><th scope=\"row\">{marked(base + '.construct', 'plain', sources)}{tag}</th>"
                    f"<td>{code(base + '.sql', sources)}</td><td>{code(base + '.cypher', sources)}</td>"
                    f"<td>{marked(base + '.sql_metrics', 'triple', sources)}</td>"
                    f"<td>{marked(base + '.cypher_metrics', 'triple', sources)}</td></tr>")
    return "\n".join(rows)


def inventory_block(sources: dict) -> str:
    rows = sources["site.json"]["inventory"]["entities"]
    return "\n".join(f"<tr><td>{marked(f'site.json:inventory.entities[{i}].file', 'plain', sources)}</td>"
                     f"<td>{marked(f'site.json:inventory.entities[{i}].rows', 'plain', sources)}</td></tr>"
                     for i, _ in enumerate(rows))


def project_block(sources: dict) -> str:
    epics = sources["site.json"]["project"]
    return "\n".join(f"<li>{marked(f'site.json:project[{i}].title', 'plain', sources)}: "
                     f"{marked(f'site.json:project[{i}].changes', 'plain', sources)} changes</li>" for i, _ in enumerate(epics))


def caveats_block(sources: dict) -> str:
    return "\n".join(f"<li>{marked(f'scores.json:caveats.{name}', 'plain', sources)}</li>"
                     for name in sorted(sources["scores.json"]["caveats"]))


def unit_table(sources: dict) -> str:
    rows = []
    for i, _ in enumerate(sources["site.json"]["blast_radius"]["by_unit"]):
        base = f"site.json:blast_radius.by_unit[{i}]"
        rows.append(f"<tr><td>{marked(base + '.unit_name', 'plain', sources)}</td>"
                    f"<td>{marked(base + '.entities', 'plain', sources)}</td></tr>")
    return "\n".join(rows)


def graph_data(sources: dict) -> str:
    data = json.dumps(sources["site.json"]["subgraph"], sort_keys=True, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/json" id="site-data">{data}</script>'


def render(sources: dict | None = None, template: Path | None = None) -> str:
    sources = sources or load_sources()
    template = template or TEMPLATE
    blocks = {"@graph-data": graph_data, "@unit-table": unit_table, "@rounds": rounds_block,
              "@counting": counting_block, "@symmetry-table": symmetry_block, "@inventory-table": inventory_block,
              "@project-list": project_block, "@caveats": caveats_block,
              "@views-sql": lambda s: code("rounds.json:views.sql", s)}

    def replace(match):
        source, fmt = match.group(1), match.group(2)
        if source in blocks:
            return blocks[source](sources)
        return marked(source, fmt or "plain", sources)

    return PLACEHOLDER.sub(replace, template.read_text(encoding="utf-8"))


def build(out: Path) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(render(template=TEMPLATE), encoding="utf-8", newline="\n")
    (out / "methods.html").write_text(render(template=METHODS), encoding="utf-8", newline="\n")
    for name in STATIC:
        shutil.copyfile(HERE / name, out / name)
    for path in (SITE_JSON, ROUNDS_JSON, SCORES):
        shutil.copyfile(path, out / path.name)
    return out / "index.html"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.features.site.build")
    parser.add_argument("--out", type=Path, required=True)
    print(f"wrote {build(parser.parse_args(argv).out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
