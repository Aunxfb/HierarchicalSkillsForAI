from __future__ import annotations
from pathlib import Path
from .models import NodeType


class DiscoveryError(Exception):
    pass


def walk_skills(repo_root: Path, max_depth: int) -> list[dict]:
    discovered: list[dict] = []
    _walk(repo_root, repo_root, 0, max_depth, discovered)
    return discovered


def _walk(
    repo_root: Path,
    current_dir: Path,
    depth: int,
    max_depth: int,
    discovered: list[dict],
):
    if depth > max_depth:
        return

    skill_md = current_dir / "SKILL.md"
    has_skill = skill_md.exists()

    subdirs = sorted(
        d for d in current_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    )
    has_subfolders = len(subdirs) > 0

    if not has_skill and not has_subfolders:
        return

    rel_path = current_dir.relative_to(repo_root)
    path_parts = str(rel_path) if rel_path != Path(".") else ""

    if has_skill and has_subfolders:
        node_type = NodeType.DUAL
    elif has_skill:
        node_type = NodeType.SKILL
    else:
        node_type = NodeType.GROUP

    info = {
        "path": path_parts,
        "folder_name": current_dir.name,
        "node_type": node_type,
        "skill_md_path": str(skill_md) if has_skill else None,
    }
    discovered.append(info)

    if has_subfolders:
        for subdir in subdirs:
            _walk(repo_root, subdir, depth + 1, max_depth, discovered)
