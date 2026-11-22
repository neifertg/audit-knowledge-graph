"""Render the page from committed exports (021). Standard library only; reads no build or database.

    python -m src.features.site.build --out <dir>       writes <dir>/index.html and the files it links

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

from .derived import DERIVED
from .formatters import FORMATTERS

HERE = Path(__file__).parent
FEATURES = HERE.parent
# Paths, not imports: the builder runs with the standard library only (CI and the Pages workflow), and
# the modules that own these files import heavier packages.
SITE_JSON = HERE / "data" / "site.json"
ROUNDS_JSON = FEATURES / "rounds" / "rounds.json"
SCORES = FEATURES / "reconciliation" / "scores.json"
TEMPLATE = HERE / "template.html"
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
        return walk(DERIVED[function](sources["rounds.json"]), rest) if rest else DERIVED[function](sources["rounds.json"])
    return walk(sources[name], path)


def marked(source: str, fmt: str, sources: dict) -> str:
    text = FORMATTERS[fmt](resolve(source, sources))
    return f'<span data-source="{html.escape(source)}" data-format="{fmt}">{html.escape(text)}</span>'


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


def render(sources: dict | None = None) -> str:
    sources = sources or load_sources()
    blocks = {"@graph-data": graph_data, "@unit-table": unit_table}

    def replace(match):
        source, fmt = match.group(1), match.group(2)
        if source in blocks:
            return blocks[source](sources)
        return marked(source, fmt or "plain", sources)

    return PLACEHOLDER.sub(replace, TEMPLATE.read_text(encoding="utf-8"))


def build(out: Path) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(render(), encoding="utf-8", newline="\n")
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
