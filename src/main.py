from __future__ import annotations
import argparse
import sys
import threading
import os
from pathlib import Path
from .tree import SkillTree
from .index import SearchIndex
from .mcp_server import create_mcp_server
from .http_server import create_http_server


def main():
    parser = argparse.ArgumentParser(
        description="Skills MCP Hierarchical Server"
    )
    parser.add_argument(
        "--repo", required=True, help="Path to the root folder containing grouped skills"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        required=True,
        help="Maximum depth to walk the folder tree",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for the web UI (default: 8080)",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for the web UI (default: localhost)",
    )

    args = parser.parse_args()

    if args.max_depth < 1:
        print("Error: --max-depth must be a positive integer", file=sys.stderr)
        sys.exit(1)

    if args.port < 1 or args.port > 65535:
        print(f"Error: --port must be between 1 and 65535 (got {args.port})", file=sys.stderr)
        sys.exit(1)

    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        print(f"Error: --repo path '{args.repo}' does not exist", file=sys.stderr)
        sys.exit(1)
    if not repo_path.is_dir():
        print(f"Error: --repo path '{args.repo}' is not a directory", file=sys.stderr)
        sys.exit(1)
    if not os.access(str(repo_path), os.R_OK):
        print(f"Error: --repo path '{args.repo}' is not readable", file=sys.stderr)
        sys.exit(1)

    print(f"Initializing skills tree from: {repo_path}", file=sys.stderr)

    try:
        tree = SkillTree(repo_path, args.max_depth)
    except Exception as e:
        print(f"Error during skill discovery: {e}", file=sys.stderr)
        sys.exit(1)

    print("Building search index...", file=sys.stderr)
    index = SearchIndex()
    index.build(tree)

    skill_count = len(index.skills)
    node_count = len(tree.nodes_by_path)
    print(f"Discovered {node_count} nodes, {skill_count} skills", file=sys.stderr)

    if skill_count == 0:
        print(
            f"Warning: no skills found in '{args.repo}'. "
            "Ensure folders contain SKILL.md files with YAML frontmatter.",
            file=sys.stderr,
        )

    mcp_app = create_mcp_server(tree, index)

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    httpd = create_http_server(args.host, args.port, tree, index, static_dir)

    http_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    http_thread.start()
    print(f"Web UI available at http://{args.host}:{args.port}", file=sys.stderr)

    print("Starting MCP server (stdio transport)...", file=sys.stderr)
    print("Press Ctrl+C to stop.", file=sys.stderr)

    try:
        mcp_app.run(transport="stdio")
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down...", file=sys.stderr)
        httpd.shutdown()
        print("Shutdown complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
