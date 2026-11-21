"""Load a built, reconciled directory into `<out>/akg.sqlite` (E3 child a, change 015).

Never reads `answer_key/` (INV-6). Writes to a temporary file and renames it at the end, so a
failed load leaves no partial database. Foreign keys are on throughout; tables load in
dependency order.
"""
import csv
import os
import sqlite3
from pathlib import Path

from .schema import SCHEMA, Table, load_tables

DATABASE = "akg.sqlite"
CAST = {"int": int, "decimal": float}


class LoadError(Exception):
    pass


def cast(column, value: str):
    if value == "" or (value == "unmapped" and "unmapped" in column.values):
        return None
    return CAST.get(column.type, str)(value)


def read_rows(build_dir: Path, table: Table) -> list[tuple]:
    with open(Path(build_dir) / table.path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected = [c.name for c in table.columns]
        if header != expected:
            raise LoadError(f"{table.path}: columns {header} differ from the dictionary's {expected}")
        return [tuple(cast(c, v) for c, v in zip(table.columns, row)) for row in reader]


def remove_database(build_dir: Path) -> None:
    (Path(build_dir) / DATABASE).unlink(missing_ok=True)


def load(build_dir: Path) -> Path:
    """(Re)build <build_dir>/akg.sqlite from the published and reconciled CSVs."""
    build_dir = Path(build_dir)
    if not (build_dir / "reconciled").is_dir():
        raise LoadError(f"{build_dir / 'reconciled'} is missing: run `python -m akg reconcile --out {build_dir}` first")
    target, partial = build_dir / DATABASE, build_dir / (DATABASE + ".partial")
    partial.unlink(missing_ok=True)
    con = sqlite3.connect(partial)
    try:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
        for table in load_tables():
            rows = read_rows(build_dir, table)
            con.executemany(f"INSERT INTO {table.name} VALUES ({', '.join('?' * len(table.columns))})", rows)
        con.commit()
        problems = con.execute("PRAGMA foreign_key_check").fetchall()
        if problems:
            raise LoadError(f"foreign key violations: {problems[:5]}")
    except BaseException:
        con.close()
        partial.unlink(missing_ok=True)
        raise
    con.close()
    os.replace(partial, target)
    return target
