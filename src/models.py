from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class NodeType(Enum):
    SKILL = "skill"
    GROUP = "group"
    DUAL = "dual"


@dataclass
class SkillMetadata:
    name: str
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    depends_on: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)
    followed_by: list[str] = field(default_factory=list)
    uses: int = 0
    last_used: Optional[str] = None
    steps: list[str] = field(default_factory=list)


@dataclass
class TreeNode:
    path: str
    folder_name: str
    node_type: NodeType
    skill_metadata: Optional[SkillMetadata] = None
    body: Optional[str] = None
    skill_md_path: Optional[str] = None
    children: dict[str, TreeNode] = field(default_factory=dict)


@dataclass
class SearchResult:
    path: str
    score: float
    name: str
