"""Shared test helpers: run the real CLI into temp dirs and read what it wrote."""
import csv
import re
import subprocess
import sys
import tempfile
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_TMP = tempfile.TemporaryDirectory(prefix="akg-test-")


def run_akg(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run([sys.executable, "-m", "akg", *args], cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise AssertionError(f"akg {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
    return result


@cache
def build(*extra: str) -> Path:
    """Build once per distinct argument list; returns the output directory."""
    out = Path(_TMP.name) / f"build{abs(hash(extra))}"
    run_akg("build", "--seed", "42", "--out", str(out), *extra)
    return out


def read(out: Path, name: str) -> list[dict]:
    with open(out / f"{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def tables(out: Path) -> dict[str, list[dict]]:
    return {p.stem: read(out, p.stem) for p in sorted(out.glob("*.csv"))}


def answer_key(out: Path, name: str) -> list[dict]:
    return read(out / "answer_key", name)


def sentences(text: str) -> set[str]:
    return {s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()}


def cosine_by_id(rows_erm: list[dict], rows_ia: list[dict], id_col: str) -> dict:
    """TF-IDF cosine between every pair of items of one kind (risks or controls), keyed by id pair.

    Fixed settings for AC-2 and AC-7: TfidfVectorizer(lowercase=True, ngram_range=(1, 2)),
    fit on all ERM and IA descriptions of that kind.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    rows = rows_erm + rows_ia
    ids = [r[id_col] for r in rows]
    matrix = TfidfVectorizer(lowercase=True, ngram_range=(1, 2)).fit_transform([r["description"] for r in rows])
    sims = cosine_similarity(matrix)
    return {(a, b): float(sims[i, j]) for i, a in enumerate(ids) for j, b in enumerate(ids) if i != j}
