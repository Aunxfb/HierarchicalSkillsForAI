from pathlib import Path
import tempfile
from src.discovery import walk_skills, DiscoveryError
from src.tree import SkillTree


def _make_skill(dirpath: Path, name: str):
    skill_dir = dirpath / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = f"""\
---
name: {name}
description: Skill for {name}
---
# {name}
"""
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


def _make_skill_with_name(dirpath: Path, folder: str, skill_name: str):
    skill_dir = dirpath / folder
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = f"""\
---
name: {skill_name}
description: Skill for {skill_name}
---
# {skill_name}
"""
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


def test_walk_basic():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "skill_a")
        _make_skill(root, "skill_b")
        results = walk_skills(root, 4)
        assert len(results) == 3  # root + 2 skills


def test_walk_nested():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "group_a").mkdir()
        _make_skill(root / "group_a", "skill_x")
        results = walk_skills(root, 4)
        assert len(results) == 3  # root + group_a + skill_x


def test_walk_depth_limit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        d = root / "a" / "b" / "c"
        d.mkdir(parents=True)
        _make_skill(d, "deep_skill")
        results = walk_skills(root, 2)
        assert len(results) == 3  # root + a + b (groups, skill beyond depth)
        results = walk_skills(root, 4)
        assert len(results) == 5  # root + a + b + c + deep_skill


def test_walk_ignores_empty():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "empty_dir").mkdir()
        results = walk_skills(root, 4)
        assert len(results) == 1  # root only (empty_dir silently ignored)


def test_duplicate_name_validation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "skill_one")
        _make_skill_with_name(root, "skill_two", "skill_one")
        try:
            SkillTree(root, 4)
            assert False, "Should have raised error"
        except DiscoveryError as e:
            assert "duplicate" in str(e).lower()


def test_valid_tree():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "skill_a")
        _make_skill(root, "skill_b")
        tree = SkillTree(root, 4)
        assert "skill_a" in tree.nodes_by_path
        assert "skill_b" in tree.nodes_by_path


def test_dual_node():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        gx = root / "group_x"
        gx.mkdir()
        (gx / "SKILL.md").write_text("""\
---
name: group_x
---
# Group X Skill
""")
        child = gx / "child_skill"
        child.mkdir()
        (child / "SKILL.md").write_text("""\
---
name: child_skill
---
# Child
""")
        tree = SkillTree(root, 4)
        node = tree.get_node("group_x")
        assert node is not None
        assert node.node_type.value == "dual"
        assert node.skill_metadata is not None
        assert node.skill_metadata.name == "group_x"
        assert "child_skill" in node.children
