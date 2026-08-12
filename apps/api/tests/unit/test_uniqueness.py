from app.services.uniqueness import SiblingName, has_duplicate_sibling_name


def test_duplicate_active_sibling_name_is_detected() -> None:
    existing = [
        SiblingName(parent_id="zone-1", name="Bakery", is_active=True),
        SiblingName(parent_id="zone-1", name="Dairy", is_active=True),
    ]
    assert (
        has_duplicate_sibling_name(existing, parent_id="zone-1", name="Bakery")
        is True
    )


def test_same_name_under_different_parent_is_allowed() -> None:
    existing = [SiblingName(parent_id="zone-1", name="Bakery", is_active=True)]
    assert (
        has_duplicate_sibling_name(existing, parent_id="zone-2", name="Bakery")
        is False
    )


def test_inactive_sibling_name_still_blocks_recreate() -> None:
    existing = [SiblingName(parent_id="zone-1", name="Bakery", is_active=False)]
    assert (
        has_duplicate_sibling_name(existing, parent_id="zone-1", name="Bakery")
        is True
    )


def test_whitespace_normalized_name_collides() -> None:
    existing = [SiblingName(parent_id="zone-1", name="Bakery", is_active=True)]
    assert (
        has_duplicate_sibling_name(existing, parent_id="zone-1", name="  Bakery  ")
        is True
    )
