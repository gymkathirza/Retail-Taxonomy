# Assessment notes

## Location → zones

The PDF model uses **Location** as the top hierarchy level. This package maps that concept to **`zones`** in the database, REST API (`/api/v1/zones`), and UI. The seed CSV may still use a `Location` column; `scripts/seed.py` maps it into the `zones` table.

## PDF wrapped subcategory names

Two subcategory names wrap across lines in the PDF source. The seed CSV stores each as a single logical name. `seed_helpers.join_wrapped_name` rejoins those wraps so seed counts and uniqueness stay correct.

## Soft-delete

- `DELETE` sets `is_active=false` on the target node **and all descendants** in one transaction.
- `POST .../restore` reactivates **only** that node; restoring a child under an inactive parent returns `409`.
- Foreign keys use `ON DELETE RESTRICT`; there is no hard purge.
- List/tree/path endpoints are active-only by default; use `?include_inactive=true` (and the UI “Show inactive” toggle) to see retired nodes. `GET` by id still returns inactive rows.
