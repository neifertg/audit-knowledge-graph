"""Golden checksums for the default build and the full build (INV-7).

Regenerate after an intentional output change, in the same commit:
    .venv\\Scripts\\python -m tests.generator.golden               # sample (the default build)
    .venv\\Scripts\\python -m tests.generator.golden --size full   # full build
"""
import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "golden" / "checksums.sha256"
GOLDEN_FULL = ROOT / "tests" / "golden" / "checksums_full.sha256"


def checksums(out: Path) -> dict[str, str]:
    """Generator CSV output only: `reconciled/` has its own golden (013); derived stores (akg.sqlite,
    015) and exports are not golden."""
    return {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(out.rglob("*.csv")) if p.is_file() and p.relative_to(out).parts[0] != "reconciled"}


def render(sums: dict[str, str]) -> str:
    return "".join(f"{digest}  {path}\n" for path, digest in sorted(sums.items()))


def read_golden(size: str = "sample") -> dict[str, str]:
    lines = (GOLDEN_FULL if size == "full" else GOLDEN).read_text(encoding="utf-8").splitlines()
    return {path: digest for digest, path in (line.split("  ", 1) for line in lines if line)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=["sample", "full"], default="sample")
    size = parser.parse_args().size
    target = GOLDEN_FULL if size == "full" else GOLDEN
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "akg", "build", "--seed", "42", "--size", size, "--out", tmp],
                       cwd=ROOT, check=True,
                       env={k: v for k, v in __import__('os').environ.items() if not k.startswith('NEO4J_')})
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(render(checksums(Path(tmp))))
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
