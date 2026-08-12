"""Sibling uniqueness rules for hierarchy nodes (active and inactive)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SiblingName:
    parent_id: str | None
    name: str
    is_active: bool = True


def normalize_sibling_name(name: str) -> str:
    return name.strip()


def has_duplicate_sibling_name(
    existing: list[SiblingName],
    *,
    parent_id: str | None,
    name: str,
    exclude_id: str | None = None,
) -> bool:
    """
    Return True if `name` would collide with an existing sibling under the same parent.

    Uniqueness includes inactive rows so a retired name cannot be recreated.
    """
    candidate = normalize_sibling_name(name)
    for row in existing:
        if exclude_id is not None and getattr(row, "id", None) == exclude_id:
            continue
        if row.parent_id != parent_id:
            continue
        if normalize_sibling_name(row.name) == candidate:
            return True
    return False
