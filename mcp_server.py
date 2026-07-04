#!/usr/bin/env python3
"""
Entry point for MCP agents: python mcp_server.py --port 8080

Defaults: --repo sample_skills --max-depth 4 --port 8080
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

known_args = [a for a in sys.argv[1:] if a.startswith("-")]
has_repo = any(a == "--repo" for a in known_args)
has_depth = any(a == "--max-depth" for a in known_args)

composed = [sys.argv[0]]
if not has_repo:
    composed.extend(["--repo", os.path.join(script_dir, "sample_skills")])
if not has_depth:
    composed.extend(["--max-depth", "4"])
composed.extend(sys.argv[1:])
sys.argv = composed

from src.main import main

if __name__ == "__main__":
    main()
