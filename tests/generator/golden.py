"""Golden checksums for the default build (INV-7).

Regenerate after an intentional output change, in the same commit:
    .venv\\Scripts\\python -m tests.generator.golden
"""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "golden" / "checksums.sha256"


def checksums(out: Path) -> dict[str, str]:
    return {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(out.rglob("*")) if p.is_file()}


def render(sums: dict[str, str]) -> str:
    return "".join(f"{digest}  {path}\n" for path, digest in sorted(sums.items()))


def read_golden() -> dict[str, str]:
    lines = GOLDEN.read_text(encoding="utf-8").splitlines()
    return {path: digest for digest, path in (line.split("  ", 1) for line in lines if line)}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "akg", "build", "--seed", "42", "--out", tmp], cwd=ROOT, check=True)
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        with open(GOLDEN, "w", encoding="utf-8", newline="\n") as f:
            f.write(render(checksums(Path(tmp))))
    print(f"wrote {GOLDEN}")


if __name__ == "__main__":
    main()
