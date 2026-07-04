from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from .models import TreeNode, NodeType, SkillMetadata
from .frontmatter import parse_skill_md, update_skill_md_usage, ensure_skill_md_fields
from .discovery import walk_skills, DiscoveryError


class SkillTree:
    def __init__(self, repo_root: Path, max_depth: int):
        self.repo_root = repo_root
        self.max_depth = max_depth
        self.root = TreeNode(
            path="",
            folder_name=repo_root.name,
            node_type=NodeType.GROUP,
        )
        self.nodes_by_path: dict[str, TreeNode] = {}
        self._build()

    def _build(self):
        discovered = walk_skills(self.repo_root, self.max_depth)

        seen_lower: dict[str, str] = {}
        for info in discovered:
            if not info["path"]:
                continue
            lowered = info["path"].lower()
            if lowered in seen_lower:
                raise DiscoveryError(
                    f"Case collision: paths '{info['path']}' and "
                    f"'{seen_lower[lowered]}' both resolve to '{lowered}'"
                )
            seen_lower[lowered] = info["path"]

            node = TreeNode(
                path=info["path"],
                folder_name=info["folder_name"],
                node_type=info["node_type"],
            )
            if info["skill_md_path"]:
                skill_path = Path(info["skill_md_path"])
                node.skill_md_path = str(skill_path)
                ensure_skill_md_fields(skill_path)
                result = parse_skill_md(skill_path)
                if result:
                    node.skill_metadata, node.body = result
            self.nodes_by_path[lowered] = node

        names: dict[str, str] = {}
        for path, node in self.nodes_by_path.items():
            if node.skill_metadata:
                name = node.skill_metadata.name
                if name in names:
                    raise DiscoveryError(
                        f"Duplicate skill name '{name}' at paths: {names[name]} and {node.path}"
                    )
                names[name] = node.path

        for path, node in self.nodes_by_path.items():
            if "/" in path:
                parent_path = "/".join(path.split("/")[:-1])
                parent = self.nodes_by_path.get(parent_path) or self.root
            else:
                parent = self.root
            parent.children[node.folder_name] = node

    def get_node(self, path: str) -> Optional[TreeNode]:
        if not path or path == "/":
            return self.root
        normalized = path.strip("/").lower()
        if ".." in normalized.split("/"):
            return None
        return self.nodes_by_path.get(normalized)

    def browse(self, path: str, depth: int = 1) -> dict:
        node = self.get_node(path)
        if not node:
            return {"path": path, "children": {}, "error": "path not found"}

        children = self._browse_children(node, depth)

        result: dict = {"path": path, "children": children}
        if node.skill_metadata:
            result["skill"] = {
                "name": node.skill_metadata.name,
                "path": node.path,
            }
        if node.node_type == NodeType.GROUP and not path:
            result["node_type"] = "root"
        return result

    def _browse_children(self, node: TreeNode, depth: int) -> dict:
        children = {}
        for name, child in node.children.items():
            entry = {
                "path": child.path,
                "node_type": child.node_type.value,
                "name": child.skill_metadata.name if child.skill_metadata else name,
            }
            if depth > 1 and child.children:
                entry["children"] = self._browse_children(child, depth - 1)
            children[name] = entry
        return children

    def read(self, path: str) -> str:
        node = self.get_node(path)
        if not node or not node.body:
            raise KeyError(f"Skill not found at '{path}'")
        return node.body

    def info(self, path: str) -> dict:
        node = self.get_node(path)
        if not node or not node.skill_metadata:
            raise KeyError(f"Skill not found at '{path}'")
        m = node.skill_metadata
        return {
            "name": m.name,
            "path": node.path,
            "folder_name": node.folder_name,
            "node_type": node.node_type.value,
            "tags": m.tags,
            "aliases": m.aliases,
            "description": m.description,
            "depends_on": m.depends_on,
            "related": m.related,
            "followed_by": m.followed_by,
            "uses": m.uses,
            "last_used": m.last_used,
            "steps": m.steps,
        }

    def use(self, path: str) -> dict:
        node = self.get_node(path)
        if not node or not node.skill_metadata:
            raise KeyError(f"Skill not found at '{path}'")
        node.skill_metadata.uses += 1
        node.skill_metadata.last_used = datetime.now(timezone.utc).isoformat()
        if node.skill_md_path:
            try:
                update_skill_md_usage(
                    Path(node.skill_md_path),
                    node.skill_metadata.uses,
                    node.skill_metadata.last_used,
                )
            except OSError as e:
                raise OSError(f"Failed to persist usage for '{path}': {e}")
        return self.info(path)

    def steps(self, path: str) -> list[str]:
        node = self.get_node(path)
        if not node or not node.skill_metadata:
            raise KeyError(f"Skill not found at '{path}'")
        return node.skill_metadata.steps

    def reload(self):
        self.nodes_by_path.clear()
        self.root = TreeNode(
            path="",
            folder_name=self.repo_root.name,
            node_type=NodeType.GROUP,
        )
        self._build()
