"""Command-line entry point.

    python -m akg build        generate the synthetic bank (E1), then reconcile it (E2)
    python -m akg reconcile    (re)write <out>/reconciled/ for an existing build
    python -m akg load         (re)build <out>/akg.sqlite, and Neo4j when NEO4J_URI is set (E3)
    python -m akg rounds       run the head-to-head rounds on an existing loaded build (E3)
    python -m akg sample-pack  render the realism-review sample pack
    python -m akg check-text   check committed AI text for orphan keys

Run from the repository root, so `src.features.generator` is importable.
"""
import argparse
import sys
from pathlib import Path

DEFAULT_OUT = Path("data")
DEFAULT_PACK = Path("research/r2-synthetic-text-realism/sample_pack.md")
DEFAULT_TEXT_DIR = Path("src/features/generator/text")


def _count(value: str) -> tuple[str, int]:
    """Parse a `--count TYPE=N` override."""
    name, sep, number = value.partition("=")
    if not sep or not name or not number.isdigit():
        raise argparse.ArgumentTypeError(f"expected TYPE=N, got {value!r}")
    return name.strip().upper(), int(number)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m akg")
    commands = parser.add_subparsers(dest="command", required=True)

    def add_generation_options(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--size", choices=["sample", "full"], default="sample")
        sub.add_argument("--seed", type=int, default=42)
        sub.add_argument("--count", type=_count, action="append", default=[],
                         metavar="TYPE=N", help="override one entity type's row count")
        sub.add_argument("--text", choices=["templated", "ai"], default=None,
                         help="default: ai (committed AI text); --count overrides need templated")
        sub.add_argument("--text-dir", type=Path, default=DEFAULT_TEXT_DIR)

    build = commands.add_parser("build", help="generate the synthetic bank (full size by default)")
    add_generation_options(build)
    build.set_defaults(size="full")
    build.add_argument("--out", type=Path, default=DEFAULT_OUT)
    build.add_argument("--no-reconcile", action="store_true",
                       help="generate only; removes any stale <out>/reconciled/")

    build.add_argument("--no-load", action="store_true",
                       help="generate and reconcile only; removes any stale <out>/akg.sqlite")

    reconcile = commands.add_parser("reconcile", help="(re)write <out>/reconciled/ for an existing build")
    reconcile.add_argument("--out", type=Path, default=DEFAULT_OUT)

    load = commands.add_parser("load", help="(re)build <out>/akg.sqlite for an existing reconciled build")
    load.add_argument("--out", type=Path, default=DEFAULT_OUT)

    rounds = commands.add_parser("rounds", help="run the SQL and Cypher rounds on an existing loaded build")
    rounds.add_argument("--out", type=Path, default=DEFAULT_OUT)

    pack = commands.add_parser("sample-pack", help="render the realism-review sample pack")
    add_generation_options(pack)
    pack.add_argument("--out", type=Path, default=DEFAULT_PACK)

    check = commands.add_parser("check-text", help="fail on committed AI text whose key no item uses")
    check.add_argument("--seed", type=int, default=42)
    check.add_argument("--size", choices=["sample", "full"], default="sample")
    check.add_argument("--text-dir", type=Path, default=DEFAULT_TEXT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "reconcile":
        _remove_database(args.out)  # a database never outlives the files it was loaded from
        return _reconcile(args.out)
    if args.command == "load":
        return _load(args.out)
    if args.command == "rounds":
        return _rounds(args.out)
    from src.features.generator import cli  # imported late so `--help` works without it

    code = cli.run(args)
    if code != 0 or args.command != "build":
        return code
    if args.no_reconcile:
        import shutil

        shutil.rmtree(Path(args.out) / "reconciled", ignore_errors=True)
        _remove_database(args.out)
        return 0
    code = _reconcile(args.out)
    if code != 0:
        return code
    if args.no_load:
        _remove_database(args.out)
        return 0
    code = _load(args.out)
    if code != 0:
        return code
    return _rounds(args.out)


def _rounds(out: Path) -> int:
    """E3: run the head-to-head rounds on SQLite, and on Neo4j when NEO4J_URI is set."""
    from src.features.rounds.runner import main as run_rounds

    return run_rounds(out)


def _remove_database(out: Path) -> None:
    from src.features.stores.sqlite_store import remove_database

    remove_database(out)


def _load(out: Path) -> int:
    """E3: load the published and reconciled files into <out>/akg.sqlite (never the answer key)."""
    from src.features.stores.sqlite_store import LoadError, load

    try:
        print(f"loaded {load(out)}")
    except LoadError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return _load_neo4j(out)


def _load_neo4j(out: Path) -> int:
    """E3: load akg.sqlite into Neo4j when NEO4J_URI is set (replaces that database's contents)."""
    from src.features.stores.neo4j_store import Neo4jLoadError, configured

    if not configured():
        print("Neo4j: skipped (NEO4J_URI is not set)")
        return 0
    from src.features.stores.neo4j_store import connect, load_neo4j

    try:
        driver = connect()
        try:
            counts = load_neo4j(out, driver)
        finally:
            driver.close()
    except Neo4jLoadError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Neo4j: loaded {counts['nodes']} nodes and {counts['edges']} edges")
    return 0


def _reconcile(out: Path) -> int:
    """E2: reconcile the published files in `out` (never reads its answer key, INV-6)."""
    from src.features.reconciliation.canonical import write_reconciled

    print(f"reconciled into {write_reconciled(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
