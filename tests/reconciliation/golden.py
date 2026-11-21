r"""Golden checksums for the seed-42 full build's reconciled/ output (013 AC-5, INV-7 for E2).

Regenerate after an intentional change:
    .venv\Scripts\python -m tests.reconciliation.golden
"""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "golden" / "checksums_reconciled.sha256"


def checksums(out: Path) -> dict[str, str]:
    folder = Path(out) / "reconciled"
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob("*.csv"))}


def render(sums: dict[str, str]) -> str:
    return "".join(f"{digest}  {name}\n" for name, digest in sums.items())


def read_golden() -> dict[str, str]:
    return {name: digest for digest, name in (line.split("  ", 1) for line in GOLDEN.read_text(encoding="utf-8").splitlines())}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "akg", "build", "--seed", "42", "--size", "full", "--out", tmp],
                       cwd=ROOT, check=True)
        GOLDEN.write_text(render(checksums(Path(tmp))), encoding="utf-8", newline="\n")
    print(f"wrote {GOLDEN}")


if __name__ == "__main__":
    main()
