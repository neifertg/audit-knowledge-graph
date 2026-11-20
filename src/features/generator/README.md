# generator

Purpose: generates the synthetic US regional bank (organization, ERM and IA taxonomies, risks, controls, audits, issues) plus a hidden answer key, so reconciliation accuracy can be measured.
Entry point: `generate.py` (`build()`); run it with `python -m akg build`.
Owns: every entity and relationship in `docs/data-model.md` except the canonical layer (E2); the answer key.
Depends on: nothing outside the standard library (scikit-learn is used only in tests).

Notes for people and agents working here:
- Content lives in `library.py` (risk concepts, organization, taxonomies) and `names/*.txt` (every institution, person, vendor and system name; INV-9). `names/deny_list.txt` holds real names that must never appear; `names/allow_terms.txt` holds capitalized domain terms AI text may use.
- Every entity type and relationship file draws from its own random stream (`rng.stream(seed, name)`), so adding draws to one never changes another file (AC-11). Never share a stream between files.
- Any intentional output change regenerates `tests/golden/checksums.sha256` in the same commit: `.venv\Scripts\python -m tests.generator.golden`.

## Data dictionary

Output goes to `--out` (default `data/`), with the answer key in `answer_key/` beside it. All files are UTF-8 without BOM, LF line endings, comma-separated with a header row, rows sorted by their first column.

**Layout.** One file per shared entity; one file per source (`_erm`, `_ia`) for taxonomy nodes, risks and controls; one file per relationship, named `<from>_<label>_<to>.csv`, with a source suffix when either end is a sourced entity. No relationship crosses sources: ERM-IA links exist only in `answer_key/`. Audits test IA controls only, so there is no `audit_tested_control_erm.csv`.

**Types.** `id`: an identifier (a primary key, or the file it references). `text`: either `name_list: <list>` (values come only from that list in `names/`; `people` means a first name from `first_names.txt` plus a last name from `last_names.txt`) or `free_text`. `enum`: one of the listed values. `int`, `date` (ISO 8601).

### `answer_key/control_clusters.csv`

| column | type | values |
|---|---|---|
| `source` | enum | ERM, IA |
| `control_id` | id | `control_erm.csv` or `control_ia.csv` (by `source`) |
| `cluster_id` | id | `RC-nnn` / `CC-nnn`, or `none` (singleton) |

### `answer_key/risk_clusters.csv`

| column | type | values |
|---|---|---|
| `source` | enum | ERM, IA |
| `risk_id` | id | `risk_erm.csv` or `risk_ia.csv` (by `source`) |
| `cluster_id` | id | `RC-nnn` / `CC-nnn`, or `none` (singleton) |
| `true_erm_node_id` | id | `taxonomy_node_erm.csv` (an L3 node) |

### `answer_key/scenarios.csv`

| column | type | values |
|---|---|---|
| `scenario` | text | free_text |
| `item_id` | id | any published ID |

### `answer_key/taxonomy_map.csv`

| column | type | values |
|---|---|---|
| `ia_node_id` | id | `taxonomy_node_ia.csv` |
| `erm_node_id` | id | `taxonomy_node_erm.csv`, or `unmapped` |

### `audit.csv`

| column | type | values |
|---|---|---|
| `audit_id` | id | primary key |
| `title` | text | free_text |
| `audit_year` | int | 2023-2025 |
| `start_date` | date | ISO 8601 |
| `end_date` | date | ISO 8601 |
| `rating` | enum | Satisfactory, Needs Improvement, Unsatisfactory |

### `audit_covered_auditable_entity.csv`

| column | type | values |
|---|---|---|
| `audit_id` | id | `audit.csv` |
| `auditable_entity_id` | id | `auditable_entity.csv` |

### `audit_raised_issue.csv`

| column | type | values |
|---|---|---|
| `audit_id` | id | `audit.csv` |
| `issue_id` | id | `issue.csv` |

### `audit_tested_control_ia.csv`

| column | type | values |
|---|---|---|
| `audit_id` | id | `audit.csv` |
| `control_id` | id | `control_ia.csv` |

### `auditable_entity.csv`

| column | type | values |
|---|---|---|
| `auditable_entity_id` | id | primary key |
| `name` | text | free_text |

### `auditable_entity_exposed_to_risk_erm.csv`

| column | type | values |
|---|---|---|
| `auditable_entity_id` | id | `auditable_entity.csv` |
| `risk_id` | id | `risk_erm.csv` |

### `auditable_entity_exposed_to_risk_ia.csv`

| column | type | values |
|---|---|---|
| `auditable_entity_id` | id | `auditable_entity.csv` |
| `risk_id` | id | `risk_ia.csv` |

### `auditable_entity_performs_process.csv`

| column | type | values |
|---|---|---|
| `auditable_entity_id` | id | `auditable_entity.csv` |
| `process_id` | id | `process.csv` |

### `business_unit.csv`

| column | type | values |
|---|---|---|
| `business_unit_id` | id | primary key |
| `name` | text | free_text |

### `business_unit_owns_auditable_entity.csv`

| column | type | values |
|---|---|---|
| `business_unit_id` | id | `business_unit.csv` |
| `auditable_entity_id` | id | `auditable_entity.csv` |

### `control_depends_on_system_erm.csv`

| column | type | values |
|---|---|---|
| `control_id` | id | `control_erm.csv` |
| `system_id` | id | `system.csv` |

### `control_depends_on_system_ia.csv`

| column | type | values |
|---|---|---|
| `control_id` | id | `control_ia.csv` |
| `system_id` | id | `system.csv` |

### `control_erm.csv`

| column | type | values |
|---|---|---|
| `control_id` | id | primary key |
| `title` | text | free_text |
| `description` | text | free_text |
| `control_type` | enum | Preventive, Detective |
| `nature` | enum | Manual, Automated, IT-dependent manual |
| `frequency` | enum | Per transaction, Daily, Weekly, Monthly, Quarterly, Annual, Per event |
| `key_control` | enum | Y, N |

### `control_ia.csv`

| column | type | values |
|---|---|---|
| `control_id` | id | primary key |
| `title` | text | free_text |
| `description` | text | free_text |
| `control_type` | enum | Preventive, Detective |
| `nature` | enum | Manual, Automated, IT-dependent manual |
| `frequency` | enum | Per transaction, Daily, Weekly, Monthly, Quarterly, Annual, Per event |
| `key_control` | enum | Y, N |

### `control_mitigates_risk_erm.csv`

| column | type | values |
|---|---|---|
| `control_id` | id | `control_erm.csv` |
| `risk_id` | id | `risk_erm.csv` |

### `control_mitigates_risk_ia.csv`

| column | type | values |
|---|---|---|
| `control_id` | id | `control_ia.csv` |
| `risk_id` | id | `risk_ia.csv` |

### `control_owned_by_person_erm.csv`

| column | type | values |
|---|---|---|
| `control_id` | id | `control_erm.csv` |
| `person_id` | id | `person.csv` |

### `control_owned_by_person_ia.csv`

| column | type | values |
|---|---|---|
| `control_id` | id | `control_ia.csv` |
| `person_id` | id | `person.csv` |

### `issue.csv`

| column | type | values |
|---|---|---|
| `issue_id` | id | primary key |
| `title` | text | free_text |
| `description` | text | free_text |
| `source` | enum | IA, Regulator, Self-identified, 2nd line |
| `rating` | enum | High, Medium, Low |
| `opened_date` | date | ISO 8601 |
| `closed_date` | date | ISO 8601, blank while open |

### `issue_against_control_erm.csv`

| column | type | values |
|---|---|---|
| `issue_id` | id | `issue.csv` |
| `control_id` | id | `control_erm.csv` |

### `issue_against_control_ia.csv`

| column | type | values |
|---|---|---|
| `issue_id` | id | `issue.csv` |
| `control_id` | id | `control_ia.csv` |

### `issue_against_risk_erm.csv`

| column | type | values |
|---|---|---|
| `issue_id` | id | `issue.csv` |
| `risk_id` | id | `risk_erm.csv` |

### `issue_against_risk_ia.csv`

| column | type | values |
|---|---|---|
| `issue_id` | id | `issue.csv` |
| `risk_id` | id | `risk_ia.csv` |

### `issue_owned_by_person.csv`

| column | type | values |
|---|---|---|
| `issue_id` | id | `issue.csv` |
| `person_id` | id | `person.csv` |

### `person.csv`

| column | type | values |
|---|---|---|
| `person_id` | id | primary key |
| `name` | text | name_list: people |
| `title` | text | name_list: titles |

### `process.csv`

| column | type | values |
|---|---|---|
| `process_id` | id | primary key |
| `name` | text | free_text |

### `process_runs_on_system.csv`

| column | type | values |
|---|---|---|
| `process_id` | id | `process.csv` |
| `system_id` | id | `system.csv` |

### `regulation.csv`

| column | type | values |
|---|---|---|
| `regulation_id` | id | primary key |
| `name` | text | name_list: regulations |
| `citation` | text | free_text |

### `regulation_requires_control_erm.csv`

| column | type | values |
|---|---|---|
| `regulation_id` | id | `regulation.csv` |
| `control_id` | id | `control_erm.csv` |

### `regulation_requires_control_ia.csv`

| column | type | values |
|---|---|---|
| `regulation_id` | id | `regulation.csv` |
| `control_id` | id | `control_ia.csv` |

### `risk_erm.csv`

| column | type | values |
|---|---|---|
| `risk_id` | id | primary key |
| `title` | text | free_text |
| `description` | text | free_text |
| `inherent_rating` | enum | High, Medium, Low |

### `risk_ia.csv`

| column | type | values |
|---|---|---|
| `risk_id` | id | primary key |
| `title` | text | free_text |
| `description` | text | free_text |
| `inherent_rating` | enum | High, Medium, Low |

### `segment.csv`

| column | type | values |
|---|---|---|
| `segment_id` | id | primary key |
| `name` | text | free_text |

### `segment_has_business_unit.csv`

| column | type | values |
|---|---|---|
| `segment_id` | id | `segment.csv` |
| `business_unit_id` | id | `business_unit.csv` |

### `system.csv`

| column | type | values |
|---|---|---|
| `system_id` | id | primary key |
| `name` | text | name_list: systems |
| `vendor` | text | name_list: vendors |
| `criticality` | enum | High, Medium, Low |

### `taxonomy_node_classifies_risk_erm.csv`

| column | type | values |
|---|---|---|
| `taxonomy_node_id` | id | `taxonomy_node_erm.csv` |
| `risk_id` | id | `risk_erm.csv` |

### `taxonomy_node_classifies_risk_ia.csv`

| column | type | values |
|---|---|---|
| `taxonomy_node_id` | id | `taxonomy_node_ia.csv` |
| `risk_id` | id | `risk_ia.csv` |

### `taxonomy_node_erm.csv`

| column | type | values |
|---|---|---|
| `taxonomy_node_id` | id | primary key |
| `level` | int | 1, 2, 3 |
| `name` | text | free_text |

### `taxonomy_node_ia.csv`

| column | type | values |
|---|---|---|
| `taxonomy_node_id` | id | primary key |
| `level` | int | 1, 2, 3 |
| `name` | text | free_text |

### `taxonomy_node_parent_of_taxonomy_node_erm.csv`

| column | type | values |
|---|---|---|
| `parent_id` | id | `taxonomy_node_erm.csv` |
| `child_id` | id | `taxonomy_node_erm.csv` |

### `taxonomy_node_parent_of_taxonomy_node_ia.csv`

| column | type | values |
|---|---|---|
| `parent_id` | id | `taxonomy_node_ia.csv` |
| `child_id` | id | `taxonomy_node_ia.csv` |

