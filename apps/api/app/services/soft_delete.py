"""Soft-delete cascade helpers for hierarchy nodes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HierarchyNode:
    id: str
    parent_id: str | None
    is_active: bool = True
    children: list[str] = field(default_factory=list)


def collect_descendant_ids(nodes_by_id: dict[str, HierarchyNode], root_id: str) -> list[str]:
    """Return root_id plus all descendant ids in breadth-first order."""
    raise NotImplementedError


def apply_soft_delete(nodes_by_id: dict[str, HierarchyNode], root_id: str) -> list[str]:
    """Set is_active=False on root and all descendants; return affected ids."""
    raise NotImplementedError
