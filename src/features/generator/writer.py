"""Write a Dataset as CSVs: UTF-8 without BOM, LF line endings (INV-7)."""
import csv
from pathlib import Path

from .generate import Dataset, Table


def write_csv(path: Path, table: Table) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(table.columns)
        writer.writerows(table.rows)


def write(dataset: Dataset, out: Path) -> None:
    out = Path(out)
    for name, table in dataset.tables.items():
        write_csv(out / f"{name}.csv", table)
    for name, table in dataset.answer_key.items():
        write_csv(out / "answer_key" / f"{name}.csv", table)
