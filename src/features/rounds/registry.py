"""The head-to-head rounds: one .sql and one .cypher file each (E3 child c, change 017, AC-1)."""
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent
VIEWS = HERE / "views.sql"
# Round 2: a control is stale unless tested by an audit ending on or after this date
# (24 months before window end 2025-12-31; inclusive).
STALE_CUTOFF = "2023-12-31"


@dataclass(frozen=True)
class Round:
    number: int
    question: str
    columns: tuple[str, ...]
    expected: str                 # expected verdict, written before the queries: SQL, close or graph
    params: dict = field(default_factory=dict)
    ordered: bool = False         # compare rows in order (a ranked top N) instead of as a sorted set

    @property
    def sql_path(self) -> Path:
        return HERE / f"round{self.number}.sql"

    @property
    def cypher_path(self) -> Path:
        return HERE / f"round{self.number}.cypher"

    @property
    def sql(self) -> str:
        return self.sql_path.read_text(encoding="utf-8")

    @property
    def cypher(self) -> str:
        return self.cypher_path.read_text(encoding="utf-8")


ROUNDS = (
    Round(1, "Open issues by business unit and rating",
          ("business_unit_id", "business_unit_name", "rating", "open_issues"), "SQL"),
    Round(2, "High risks with stale coverage, on canonical items",
          ("canonical_risk_id", "has_ia_member"), "close", {"cutoff": STALE_CUTOFF}),
    Round(3, "Shared-system blast radius: the 3 systems reaching the most auditable entities",
          ("system_id", "system_name", "entities"), "graph", ordered=True),
    Round(4, "Every path from a regulation to a business unit",
          ("regulation_id", "business_unit_id", "paths"), "graph"),
)
