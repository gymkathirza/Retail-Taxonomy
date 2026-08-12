# Assessment notes

## Domain interpretation

The hierarchy `Zone / Department / Category / SubCategory` is treated as a unique
merchandise classification leaf (SKU-class identity). Each full path is uniquely
addressable, and every node also has a stable UUID. No separate Product/SKU catalog
is built in this scope.

## PDF `Location` → model `zones`

The source PDF column is named `Location` with values `Center` / `Perimeter`. These are
merchandising areas/zones. They are modeled as the `zones` table (`zone_id`,
`/api/v1/zones`, UI label **Zone**). The seed CSV keeps the PDF column header
`Location`; `scripts/seed.py` maps that column into `zones`.

## Seed reconstruction

`data/seed/taxonomy.csv` is the canonical, already-unwrapped source of truth. The
application never parses the PDF at runtime. Two subcategory names span wrapped PDF
lines and are preserved verbatim:

- `Refrigerated English Muffins and Biscuits`
- `Refrigerated Sweet Breakfast Baked Goods`

Expected seed counts (asserted in `apps/api/tests/unit/test_seed_csv.py`):

| Entity | Count |
| --- | --- |
| Zones | 2 |
| Departments | 8 |
| Categories | 25 |
| Subcategories | 61 |
| Unique hierarchy paths | 61 |

## Soft-delete contract

`is_active BOOLEAN NOT NULL DEFAULT true` on all four tables. HTTP `DELETE` sets
`is_active=false` on the node and all descendants in one transaction (idempotent `204`).
Foreign keys are `ON DELETE RESTRICT`; rows are never physically removed. Uniqueness
constraints include inactive names, so recreating a retired sibling name returns `409`.
`POST .../restore` reactivates the node only; restoring a child whose parent is still
inactive returns `409`.
