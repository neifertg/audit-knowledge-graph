"""Cached full builds for reconciliation tests, any seed (E2)."""
import tempfile
from functools import cache
from pathlib import Path

from tests.generator.helpers import ROOT, read, run_akg

_TMP = tempfile.TemporaryDirectory(prefix="akg-recon-")


@cache
def full_build(seed: int = 42, text: str = "ai") -> Path:
    """A full-size build. AI text exists only for seed 42; other seeds use templated text."""
    out = Path(_TMP.name) / f"seed{seed}-{text}"
    run_akg("build", "--seed", str(seed), "--size", "full", "--text", text, "--out", str(out))
    return out


def answer_key(out: Path, name: str) -> list[dict]:
    return read(out / "answer_key", name)


__all__ = ["ROOT", "answer_key", "full_build", "read"]
