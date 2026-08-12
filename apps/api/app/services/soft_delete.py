"""Soft-delete cascade helpers for hierarchy nodes."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class HierarchyNode:
    id: str
    parent_id: str | None
    is_active: bool = True
    children: list[str] = field(default_factory=list)


def collect_descendant_ids(nodes_by_id: dict[str, HierarchyNode], root_id: str) -> list[str]:
    """Return root_id plus all descendant ids in breadth-first order."""
    if root_id not in nodes_by_id:
        raise KeyError(root_id)
    ordered: list[str] = []
    queue: deque[str] = deque([root_id])
    seen: set[str] = set()
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        ordered.append(current)
        node = nodes_by_id[current]
        queue.extend(node.children)
    return ordered


def apply_soft_delete(nodes_by_id: dict[str, HierarchyNode], root_id: str) -> list[str]:
    """Set is_active=False on root and all descendants; return affected ids."""
    affected = collect_descendant_ids(nodes_by_id, root_id)
    for node_id in affected:
        nodes_by_id[node_id].is_active = False
    return affected
