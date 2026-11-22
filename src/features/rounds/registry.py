"""The head-to-head rounds: one .sql and one .cypher file each (E3 children c and d; 017, 018)."""
from dataclasses import dataclass, field
from pathlib import Path

from .fourth_party import most_relied_on, read_register

HERE = Path(__file__).parent
VIEWS = HERE / "views.sql"
# Round 2: a control is stale unless tested by an audit ending on or after this date
# (24 months before window end 2025-12-31; inclusive).
STALE_CUTOFF = "2023-12-31"
REGISTER = read_register()


@dataclass(frozen=True)
class Round:
    number: int | str             # 1-7, or "owners" for the supporting query
    question: str
    columns: tuple[str, ...]
    expected: str | None          # expected verdict, written before the queries; None for a supporting query
    note: str                     # one-line readability note for the page
    params: dict = field(default_factory=dict)
    ordered: bool = False         # compare rows in order (a ranked top N) instead of as a sorted set
    source_tables: tuple[str, ...] = ()   # per-source tables it may name: its question is about one source
    scenario: tuple | None = None # (planted scenario, rule 'equal' or 'contains', verifying test)
    supporting: bool = False      # derived, not a scored round and not planted

    @property
    def stem(self) -> str:
        return f"round{self.number}" if isinstance(self.number, int) else str(self.number)

    @property
    def sql_path(self) -> Path:
        return HERE / f"{self.stem}.sql"

    @property
    def cypher_path(self) -> Path:
        return HERE / f"{self.stem}.cypher"

    def _read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @property
    def sql(self) -> str:
        return self._read(self.sql_path)

    @property
    def cypher(self) -> str:
        return self._read(self.cypher_path)

    @property
    def has_setup(self) -> bool:
        return (HERE / f"{self.stem}.setup.sql").exists()

    @property
    def sql_setup(self) -> str:
        return self._read(HERE / f"{self.stem}.setup.sql") if self.has_setup else ""

    @property
    def cypher_setup(self) -> str:
        return self._read(HERE / f"{self.stem}.setup.cypher") if self.has_setup else ""

    def scored(self, engine: str) -> str:
        """The text the verdict scores: setup followed by the query (018 AC-5)."""
        setup, query = (self.sql_setup, self.sql) if engine == "sql" else (self.cypher_setup, self.cypher)
        return f"{setup}\n{query}" if setup else query


T_ROUNDS = "rounds.test_rounds.RoundTests.test_ac3_sqlite_answers_match_oracle_and_scenarios"
T_ROUNDS57 = "rounds.test_rounds_5_7.Rounds57Tests.test_ac2_sqlite_answers_match_oracle_and_scenarios"

ROUNDS = (
    Round(1, "Open issues by business unit and rating",
          ("business_unit_id", "business_unit_name", "rating", "open_issues"), "SQL",
          "A four-join group-by in SQL; one pattern and implicit grouping in Cypher."),
    Round(2, "High risks with stale coverage, on canonical items",
          ("canonical_risk_id", "has_ia_member"), "close",
          "A CTE and an anti-join in SQL; a WITH stage and an EXISTS subquery in Cypher.",
          {"cutoff": STALE_CUTOFF}, source_tables=("audit_tested_control_ia",),
          scenario=("untested_high_risk", "contains", T_ROUNDS)),
    Round(3, "Shared-system blast radius: the 3 systems reaching the most auditable entities",
          ("system_id", "system_name", "entities"), "graph",
          "Three joins and a top-3 in SQL; one four-node pattern in Cypher.", ordered=True,
          scenario=("shared_system", "equal", T_ROUNDS)),
    Round(4, "Every path from a regulation to a business unit",
          ("regulation_id", "business_unit_id", "paths"), "graph",
          "Three joins counting rows in SQL; one five-node path counted in Cypher."),
    Round(5, "A third-party register arrives: which auditable entities are exposed to the vendor most "
             "others rely on, directly or only through fourth parties?",
          ("auditable_entity_id", "exposure"), "graph",
          "SQL adds one table and a recursive CTE; the graph must first turn vendors into nodes and edges.",
          {"vendor": most_relied_on(REGISTER)}),
    Round(6, "Repeat findings in disguise: IA controls with issues in two or more years, and their issues",
          ("control_id", "issue_id", "opened_date", "title"), "close",
          "A grouped CTE joined back in SQL; collect and unwind in Cypher. Links and dates, never titles.",
          source_tables=("issue_against_control_ia",),
          scenario=("repeat_finding", "equal", T_ROUNDS57)),
    Round(7, "Year-over-year findings by ERM L1 (regulator, self-identified and 2nd-line issues)",
          ("l1_node_id", "l1_name", "year", "issues"), "SQL",
          "Two parent joins up the taxonomy in SQL; a fixed two-hop path in Cypher.",
          source_tables=("issue_against_risk_erm", "taxonomy_node_classifies_risk_erm",
                         "taxonomy_node_parent_of_taxonomy_node_erm", "taxonomy_node_erm"),
          scenario=("rising_category", "equal", T_ROUNDS57)),
)

SUPPORTING = (
    Round("owners", "Owner concentration: who owns the most key controls, and how many business units "
                    "those controls reach (derived, not planted)",
          ("person_id", "key_controls", "business_units"), None,
          "LEFT JOINs keep key controls that reach no unit; OPTIONAL MATCH does the same in Cypher.",
          ordered=True, supporting=True),
)

ALL = ROUNDS + SUPPORTING
