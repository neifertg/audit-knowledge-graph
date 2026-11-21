# Reconciled files: data dictionary

E2's output in `<out>/reconciled/` (see docs/data-model.md, "Canonical layer"), in the same format as the generator's data dictionary (`src/features/generator/README.md`), so `schema.py` can generate the SQLite schema from both.

Types are as in the generator's dictionary, plus `decimal` (a floating-point number, written with 6 decimals). Values that name two files `by` a column (for example `risk_erm.csv` or `risk_ia.csv` by `source`) point to either table depending on that column. They get no SQL foreign key; tests check them instead.

### `reconciled/canonical_control.csv`

| column | type | values |
|---|---|---|
| `canonical_control_id` | id | primary key |

### `reconciled/canonical_risk.csv`

| column | type | values |
|---|---|---|
| `canonical_risk_id` | id | primary key |
| `erm_l3_node_id` | id | `taxonomy_node_erm.csv` |
| `placement` | enum | erm, matched, mapped, nearest |

### `reconciled/control_maps_to_canonical.csv`

| column | type | values |
|---|---|---|
| `source` | enum | ERM, IA |
| `control_id` | id | `control_erm.csv` or `control_ia.csv` by `source` |
| `canonical_control_id` | id | `canonical_control.csv` |
| `logit` | decimal | merged edge's logit, blank for unmerged items |

### `reconciled/ia_maps_to_erm.csv`

| column | type | values |
|---|---|---|
| `ia_node_id` | id | primary key; `taxonomy_node_ia.csv` |
| `erm_node_id` | id | `taxonomy_node_erm.csv`, or `unmapped` (stored as NULL) |
| `score` | decimal | winning vote share, 0-1 |
| `basis` | enum | vote, no_risks |

### `reconciled/review_queue.csv`

| column | type | values |
|---|---|---|
| `kind` | enum | risk, duplicate, control |
| `item_a` | id | `risk_erm.csv` or `control_erm.csv` by `kind` |
| `item_b` | id | `risk_ia.csv`, `risk_erm.csv` or `control_ia.csv` by `kind` |
| `logit` | decimal | pair's logit |
| `reason` | enum | review_band, conflict |
| `drivers` | text | free_text |

### `reconciled/risk_maps_to_canonical.csv`

| column | type | values |
|---|---|---|
| `source` | enum | ERM, IA |
| `risk_id` | id | `risk_erm.csv` or `risk_ia.csv` by `source` |
| `canonical_risk_id` | id | `canonical_risk.csv` |
| `logit` | decimal | merged edge's logit, blank for unmerged items |
