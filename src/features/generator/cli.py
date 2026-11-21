"""Commands behind `python -m akg` for the generator."""
import sys

from .generate import GenerationError, build, orphan_ai_keys
from .writer import write


def run(args) -> int:
    if getattr(args, "text", "") is None:
        # R2 chose AI text, committed for both sizes (010). It applies strictly: an item with
        # no current entry (e.g. new items from --count) fails the build; use --text templated.
        args.text = "ai"
    try:
        if args.command == "build":
            dataset = build(args.seed, dict(args.count), args.text, args.text_dir, args.size)
            write(dataset, args.out)
            print(f"wrote {len(dataset.tables)} tables and {len(dataset.answer_key)} answer-key files to {args.out}")
            return 0
        if args.command == "check-text":
            orphans = orphan_ai_keys(build(args.seed, size=args.size), args.text_dir, args.size)
            if orphans:
                print("AI text keys that no item uses: " + ", ".join(orphans), file=sys.stderr)
                return 1
            print("AI text: no orphan keys")
            return 0
        if args.command == "sample-pack":
            from .sample_pack import render

            render(args)
            return 0
    except GenerationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    raise SystemExit(f"unknown command {args.command}")
