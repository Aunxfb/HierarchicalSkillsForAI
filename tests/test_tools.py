from pathlib import Path
import tempfile
from src.tree import SkillTree
from src.index import SearchIndex


def _make_skill(dirpath: Path, name: str, **kwargs):
    skill_dir = dirpath / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    tags = kwargs.get("tags", [])
    aliases = kwargs.get("aliases", [])
    description = kwargs.get("description", f"Skill {name}")
    depends_on = kwargs.get("depends_on", [])
    related = kwargs.get("related", [])
    steps = kwargs.get("steps", [])
    uses = kwargs.get("uses", 0)
    content = f"""\
---
name: {name}
tags: {tags!r}
aliases: {aliases!r}
description: {description}
depends_on: {depends_on!r}
related: {related!r}
uses: {uses}
steps: {steps!r}
---
# {name}
Body content for {name}
"""
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


def get_test_tree():
    tmp = tempfile.mkdtemp()
    root = Path(tmp)
    _make_skill(root, "skill_a", tags=["python"], aliases=["sa"], steps=["step1"])
    _make_skill(root, "skill_b", tags=["rust"], description="A rust skill")
    return root, SkillTree(root, 4)


def test_browse_root():
    root, tree = get_test_tree()
    result = tree.browse("")
    assert "children" in result
    assert len(result["children"]) == 2


def test_browse_unknown():
    root, tree = get_test_tree()
    result = tree.browse("nonexistent")
    assert "error" in result


def test_browse_with_depth():
    tmp = Path(tempfile.mkdtemp())
    root = Path(tmp)
    group = root / "group_a"
    group.mkdir()
    _make_skill(root / "group_a", "skill_c")
    _make_skill(root / "group_a", "skill_d")
    tree = SkillTree(root, 4)
    r1 = tree.browse("group_a", depth=1)
    assert "children" in r1
    assert len(r1["children"]) == 2
    for name, c in r1["children"].items():
        assert "children" not in c
    r2 = tree.browse("", depth=2)
    assert "group_a" in r2["children"]
    assert "children" in r2["children"]["group_a"]
    assert "skill_c" in r2["children"]["group_a"]["children"]


def test_read():
    root, tree = get_test_tree()
    body = tree.read("skill_a")
    assert "Body content for skill_a" in body


def test_read_invalid():
    root, tree = get_test_tree()
    try:
        tree.read("nonexistent")
        assert False
    except KeyError:
        pass


def test_info():
    root, tree = get_test_tree()
    info = tree.info("skill_a")
    assert info["name"] == "skill_a"
    assert info["tags"] == ["python"]
    assert info["aliases"] == ["sa"]
    assert info["uses"] == 0


def test_info_invalid():
    root, tree = get_test_tree()
    try:
        tree.info("nonexistent")
        assert False
    except KeyError:
        pass


def test_use():
    root, tree = get_test_tree()
    info = tree.use("skill_a")
    assert info["uses"] == 1
    assert info["last_used"] is not None
    info2 = tree.use("skill_a")
    assert info2["uses"] == 2


def test_steps():
    root, tree = get_test_tree()
    steps = tree.steps("skill_a")
    assert steps == ["step1"]


def test_steps_empty():
    root, tree = get_test_tree()
    steps = tree.steps("skill_b")
    assert steps == []


def test_search_exact_name():
    root, tree = get_test_tree()
    index = SearchIndex()
    index.build(tree)
    results = index.search("skill_a")
    assert len(results) >= 1
    assert results[0].path == "skill_a"


def test_search_tag():
    root, tree = get_test_tree()
    index = SearchIndex()
    index.build(tree)
    results = index.search("python")
    assert any(r.path == "skill_a" for r in results)


def test_search_description():
    root, tree = get_test_tree()
    index = SearchIndex()
    index.build(tree)
    results = index.search("rust")
    assert any(r.path == "skill_b" for r in results)


def test_search_path_segment():
    tmp = Path(tempfile.mkdtemp())
    root = Path(tmp)
    (root / "group_a").mkdir()
    _make_skill(root / "group_a", "hidden_skill")
    tree = SkillTree(root, 4)
    index = SearchIndex()
    index.build(tree)
    results = index.search("group_a")
    assert any(r.path == "group_a/hidden_skill" for r in results)

def test_search_usage_boost():
    root, tree = get_test_tree()
    tree.use("skill_a")
    tree.use("skill_a")
    index = SearchIndex()
    index.build(tree)
    results = index.search("skill")
    assert results[0].path == "skill_a"


def test_reload():
    root, tree = get_test_tree()
    assert len(tree.nodes_by_path) == 2
    _make_skill(root, "skill_c")
    tree.reload()
    assert "skill_c" in tree.nodes_by_path
    assert len(tree.nodes_by_path) == 3


def test_case_insensitive_lookup():
    root, tree = get_test_tree()
    for method in [tree.read, tree.info, tree.steps]:
        result_lower = method("skill_a")
        result_upper = method("SKILL_A")
        assert result_lower == result_upper, f"{method.__name__} failed case-insensitive lookup"
    b1 = tree.browse("skill_a")
    b2 = tree.browse("SKILL_A")
    assert b1["children"] == b2["children"]
    assert b1.get("skill") == b2.get("skill")
    assert "error" not in b2


def test_case_collision_raises():
    import tempfile
    from pathlib import Path
    from src.discovery import DiscoveryError
    tmp = Path(tempfile.mkdtemp())
    (tmp / "Coding").mkdir()
    (tmp / "coding").mkdir()
    (tmp / "Coding" / "SKILL.md").write_text("---\nname: skill_x\n---\n")
    (tmp / "coding" / "SKILL.md").write_text("---\nname: skill_y\n---\n")
    try:
        from src.tree import SkillTree
        SkillTree(tmp, 4)
        assert False, "Expected DiscoveryError for case collision"
    except DiscoveryError:
        pass


def test_use_persists_to_disk():
    root = Path(tempfile.mkdtemp())
    _make_skill(root, "persist_skill")
    tree = SkillTree(root, 4)
    tree.use("persist_skill")
    skill_file = root / "persist_skill" / "SKILL.md"
    content = skill_file.read_text()
    assert "uses: 1" in content
    assert "last_used:" in content
    assert "202" in content  # year in timestamp
    tree.use("persist_skill")
    content2 = skill_file.read_text()
    assert "uses: 2" in content2
