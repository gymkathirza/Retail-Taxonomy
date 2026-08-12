from app.services.seed_helpers import join_wrapped_seed_lines


def test_joins_refrigerated_english_muffins_wrap() -> None:
    lines = [
        "Location,Department,Category,SubCategory",
        "Center,Dairy,Refrigerated Baking,Refrigerated English Muffins and",
        "Biscuits",
        "Center,Dairy,Refrigerated Baking,Refrigerated Hand Held Sweets",
    ]
    rows = join_wrapped_seed_lines(lines)
    assert (
        "Center,Dairy,Refrigerated Baking,Refrigerated English Muffins and Biscuits"
        in rows
    )


def test_joins_sweet_breakfast_baked_goods_wrap() -> None:
    lines = [
        "Center,Dairy,Refrigerated Baking,Refrigerated Sweet Breakfast Baked",
        "Goods",
    ]
    rows = join_wrapped_seed_lines(lines)
    assert rows == [
        "Center,Dairy,Refrigerated Baking,Refrigerated Sweet Breakfast Baked Goods"
    ]


def test_drops_page_marker() -> None:
    lines = [
        "Perimeter,Floral,Gifts,Gifts",
        "3.",
        "Perimeter,Floral,Plants,Plants",
    ]
    rows = join_wrapped_seed_lines(lines)
    assert rows == [
        "Perimeter,Floral,Gifts,Gifts",
        "Perimeter,Floral,Plants,Plants",
    ]
