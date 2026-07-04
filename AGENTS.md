# AGENTS.md — Agent Conventions

## Project Overview

`skills-mcp-server` is a hierarchical MCP (Model Context Protocol) server for managing skill definitions stored as `SKILL.md` files with YAML frontmatter. It provides a tree-based skill hierarchy, full-text search, usage tracking, and a read-only web UI.

## Python Environment

```bash
cd /home/axl/CODE/HierarchicalSkillsForAI
source venv/bin/activate
```

## Key Commands

```bash
# Run tests
python -m pytest tests/ -v

# Run the server (simple entry point — defaults to sample_skills)
python mcp_server.py --port 8080

# Run with custom repo
python mcp_server.py --port 8080 --repo /path/to/skills --max-depth 4
```

## Code Layout

| Path | Purpose |
|------|---------|
| `mcp_server.py` | Simple root-level entry point (`python mcp_server.py --port 8080`) |
| `src/__main__.py` | Package entry point (`python -m src`) |
| `src/main.py` | CLI argument parsing, startup orchestration |
| `src/models.py` | Data models: `SkillMetadata`, `TreeNode`, `SearchResult`, `NodeType` |
| `src/frontmatter.py` | YAML frontmatter parser for `SKILL.md` |
| `src/discovery.py` | Recursive folder walker with depth limit |
| `src/tree.py` | In-memory tree: `browse()`, `read()`, `info()`, `use()`, `steps()`, `reload()` |
| `src/index.py` | Search index: name, tags, aliases, description, body text, path segments, usage/recency boost |
| `src/mcp_server.py` | FastMCP tool definitions for all 7 MCP tools |
| `src/http_server.py` | HTTP server for web UI (`/api/browse`, `/api/search`, `/api/read`, `/api/info`) |
| `src/static/index.html` | Single-page web UI (vanilla HTML/CSS/JS) |
| `tests/` | pytest tests for discovery, frontmatter parsing, and tools |
| `sample_skills/` | Demo skill folders with `SKILL.md` files |

## MCP Tools

| Tool | Description |
|------|-------------|
| `browse(path, depth=1)` | Browse skill hierarchy; returns child groups + skills. `depth > 1` for nested levels |
| `read(path)` | Return full `SKILL.md` body |
| `search(query)` | Search by name, tags, aliases, description, path segments; ranked results |
| `info(path)` | Return YAML metadata (no body) |
| `use(path)` | Increment usage counter, update `last_used` |
| `steps(path)` | Return ordered `steps` array |
| `reload()` | Re-scan repo, re-validate, re-index |

## Environment

- Python 3.10+ required
- Dependencies: `mcp >= 1.0.0`, `pyyaml >= 6.0`
- Virtual environment at `venv/`
- Install: `pip install -e .`

## Skill File Format

Skills are stored in folders containing `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
tags: [tag1, tag2]
aliases: [alias1]
description: Description text
depends_on: [parent-skill]
related: [related-skill]
followed_by: [next-skill]
uses: 0
last_used: null
steps: [sub-step1, sub-step2]
---
```

## Conventions

- Use `pytest` for testing
- Type hints required for all functions
- Avoid adding external dependencies unless necessary
- Keep web UI as vanilla HTML/CSS/JS (no build step)
- Server validates `name` uniqueness at startup; duplicate names abort
- Folders beyond `--max-depth` are silently ignored
