import csv
from pathlib import Path

CSV = Path(__file__).resolve().parents[4] / "data" / "seed" / "taxonomy.csv"


def _load():
    with CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_seed_counts_match_assessment():
    rows = _load()
    zones = {r["Location"] for r in rows}
    departments = {(r["Location"], r["Department"]) for r in rows}
    categories = {(r["Location"], r["Department"], r["Category"]) for r in rows}
    subcategories = {
        (r["Location"], r["Department"], r["Category"], r["SubCategory"]) for r in rows
    }
    assert len(zones) == 2
    assert len(departments) == 8
    assert len(categories) == 25
    assert len(subcategories) == 61
    assert len(subcategories) == len(rows)  # every row is a unique leaf path


def test_wrapped_subcategory_names_preserved():
    names = {r["SubCategory"] for r in _load()}
    assert "Refrigerated English Muffins and Biscuits" in names
    assert "Refrigerated Sweet Breakfast Baked Goods" in names
