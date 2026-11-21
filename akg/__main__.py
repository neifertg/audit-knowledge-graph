"""Command-line entry point.

    python -m akg build        generate the synthetic bank (E1); E2 and E3 add steps later
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
    from src.features.generator import cli  # imported late so `--help` works without it

    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
