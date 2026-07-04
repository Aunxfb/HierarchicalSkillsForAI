from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from .tree import SkillTree
from .index import SearchIndex


def _validate_path(path: str):
    if ".." in path.split("/"):
        raise ValueError(f"Invalid path: '{path}'")


def create_mcp_server(tree: SkillTree, index: SearchIndex, *, update_index_on_use: bool = True) -> FastMCP:
    mcp = FastMCP("skills-mcp-server")

    @mcp.tool()
    def browse(path: str = "", depth: int = 1) -> dict:
        """Browse the skill hierarchy at a given path. Returns child groups and skills. Set depth > 1 to include nested levels."""
        _validate_path(path)
        return tree.browse(path, depth)

    @mcp.tool()
    def read(path: str) -> str:
        """Read the full SKILL.md content for a skill at the given path."""
        _validate_path(path)
        try:
            return tree.read(path)
        except KeyError as e:
            return str(e)

    @mcp.tool()
    def search(query: str) -> list[dict]:
        """Search for skills matching the query. Searches name, tags, aliases, description. Returns ranked results."""
        results = index.search(query)
        return [{"path": r.path, "score": r.score, "name": r.name} for r in results]

    @mcp.tool()
    def info(path: str) -> dict:
        """Get metadata about a skill without reading its full content."""
        _validate_path(path)
        try:
            return tree.info(path)
        except KeyError as e:
            return {"error": str(e)}

    @mcp.tool()
    def use(path: str) -> dict:
        """Record that a skill was used. Increments usage counter and updates timestamp."""
        _validate_path(path)
        try:
            result = tree.use(path)
            if update_index_on_use:
                index.update_usage(path, result["uses"], result["last_used"])
            return result
        except KeyError as e:
            return {"error": str(e)}

    @mcp.tool()
    def steps(path: str) -> list[str]:
        """Get the ordered workflow steps for a skill."""
        _validate_path(path)
        try:
            return tree.steps(path)
        except KeyError as e:
            return [str(e)]

    @mcp.tool()
    def reload() -> dict:
        """Re-scan the repo tree, re-validate all skills, and rebuild the index."""
        try:
            tree.reload()
            index.build(tree)
            return {"status": "ok", "skills": len(tree.nodes_by_path)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    return mcp
