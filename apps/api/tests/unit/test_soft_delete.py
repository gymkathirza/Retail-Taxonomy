from app.services.soft_delete import HierarchyNode, apply_soft_delete, collect_descendant_ids


def _sample_tree() -> dict[str, HierarchyNode]:
    return {
        "z1": HierarchyNode(id="z1", parent_id=None, children=["d1"]),
        "d1": HierarchyNode(id="d1", parent_id="z1", children=["c1"]),
        "c1": HierarchyNode(id="c1", parent_id="d1", children=["s1", "s2"]),
        "s1": HierarchyNode(id="s1", parent_id="c1"),
        "s2": HierarchyNode(id="s2", parent_id="c1"),
    }


def test_collect_descendants_includes_root_and_children() -> None:
    nodes = _sample_tree()
    ids = collect_descendant_ids(nodes, "d1")
    assert ids[0] == "d1"
    assert set(ids) == {"d1", "c1", "s1", "s2"}


def test_soft_delete_deactivates_node_and_descendants() -> None:
    nodes = _sample_tree()
    affected = apply_soft_delete(nodes, "c1")
    assert set(affected) == {"c1", "s1", "s2"}
    assert nodes["c1"].is_active is False
    assert nodes["s1"].is_active is False
    assert nodes["s2"].is_active is False
    assert nodes["d1"].is_active is True
