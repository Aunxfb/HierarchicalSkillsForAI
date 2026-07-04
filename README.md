# Hierarchical Skills For AI - A Skills Serving Hierarchical MCP Server

A hierarchical MCP (Model Context Protocol) server for managing skill definitions. Skills are stored as folders containing `SKILL.md` with YAML frontmatter, organized in a browsable tree structure with full-text search and a web UI.

## Architecture

```
  Agent (MCP client)             Human (browser)
       ↓                              ↓
Skills MCP Server ← python mcp_server.py --port 8080
       │                              │
       ├── MCP (stdio)                ├── HTTP (web UI)
       │   browse(path, depth=1)      │   GET /api/browse?path=&depth=
       │   read(path)                 │   GET /api/search?q=
       │   search(query)              │   GET /api/read?path=
       │   info(path)                 │   GET /api/info?path=
       │   use(path)                  │
       │   steps(path)                │
       │   reload()                   │
       │                              │
       └──────────────────────────────┘
                      ↓
          ┌───────────┼───────────┐
          ↓           ↓           ↓
     File system    Index     Usage stats
     (SKILL.md)   (tags,     (uses count,
                   aliases,   last_used)
                   body,
                   relations)
```

## Quick Start

```bash
# Install
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Run with sample skills (activate venv first)
python mcp_server.py --port 8080

# Open web UI
open http://localhost:8080
```

## CLI Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--repo` | No | `sample_skills` | Path to root folder containing grouped skills |
| `--max-depth` | No | 4 | Maximum folder depth to walk |
| `--port` | No | 8080 | Port for web UI |
| `--host` | No | localhost | Host for web UI |

## MCP Tools

| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `browse(path, depth=1)` | `""`, `"coding"`, `"coding/python"` | Child groups + skills (nested if `depth>1`) | Navigate the skill hierarchy |
| `read(path)` | `"coding/python/fastapi"` | Full SKILL.md body | Load skill content |
| `search(query)` | `"fastapi"`, `"web"` | Ranked paths | Search by name, tags, aliases, description, path segments |
| `info(path)` | `"coding/python/fastapi"` | YAML metadata (no body) | Lightweight skill inspection |
| `use(path)` | `"coding/python/fastapi"` | Updated metadata | Track skill usage (boosts search ranking) |
| `steps(path)` | `"coding/python/fastapi"` | Ordered step list | Get workflow sub-skills |
| `reload()` | — | Status | Re-scan repo, re-validate, re-index |

## Skill File Format

Each skill lives in its own folder containing a `SKILL.md` file with YAML frontmatter delimited by `---`.

### Folder structure rules

```
skills/
  coding/                      # group folder (has subfolders, no SKILL.md)
    python/
      fastapi/                 # skill folder → contains SKILL.md
        SKILL.md
      pytest/
        SKILL.md
    rust/
      tokio/
        SKILL.md
```

- A folder is a **skill** if it contains `SKILL.md`
- A folder is a **group** if it has subfolders but no `SKILL.md`
- A folder can be **dual** (both group + skill) — has `SKILL.md` AND subfolders
- Folders beyond `--max-depth` are silently ignored
- Empty folders (no `SKILL.md`, no subfolders) are silently ignored
- Use lowercase with hyphens for folder names: `web-scraping`

### Frontmatter fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | **Yes** | string | Unique identifier across the entire tree. Does not need to match folder name. |
| `tags` | No | list | Keywords for search: `[python, api, web]` |
| `aliases` | No | list | Alternative names an AI might search by: `[fast api, fastapi framework]` |
| `description` | No | string | One or two sentences explaining the skill. Indexed for search. |
| `depends_on` | No | list of paths | Prerequisites the AI should know first: `[python/basics]` |
| `related` | No | list of paths | Conceptually similar skills: `[flask, starlette]` |
| `followed_by` | No | list of paths | Natural next skills after mastering this one |
| `steps` | No | list of paths | Ordered sub-skill paths for multi-step workflows |
| `uses` | Auto | integer | Usage counter — auto-incremented by `use()` tool |
| `last_used` | Auto | string or null | ISO timestamp — auto-set by `use()` tool |

### Example

```yaml
---
name: fastapi
tags: [python, api, web]
aliases: [fast api, fastapi framework]
description: Python web framework for building APIs
depends_on: [python/basics]
related: [flask, starlette]
followed_by: [sqlalchemy, pytest]
uses: 0
last_used: null
steps: [setup/project-scaffold, coding/python/fastapi/routing]
---
```

After the closing `---`, write standard Markdown body content. The server never modifies the body — only `uses` and `last_used` in the frontmatter are updated automatically.

### Validation rules

On startup and `reload()` the server validates every skill:
- `SKILL.md` must exist and have valid YAML frontmatter
- `name` field is required and must be **unique** across the entire tree
- Duplicate names cause an abort with per-skill error logging
- Folders beyond `--max-depth` are silently ignored

### Hierarchy guidelines

- Keep `--max-depth` between 3 and 5 levels
- Aim for 5–15 children per group node; split into sub-groups if exceeding 20
- Use dual nodes (folder with `SKILL.md` + subfolders) when a group has general content applying to all children
- Prefer 3–8 tags per skill, lowercase, singular form

## Project Structure

```
skills-mcp-server/
├── mcp_server.py           # Root-level entry point
├── pyproject.toml          # Project configuration
├── src/
│   ├── __init__.py         # Package init
│   ├── __main__.py         # Entry point
│   ├── main.py             # CLI + server orchestration
│   ├── models.py           # Data models
│   ├── frontmatter.py      # YAML frontmatter parser
│   ├── discovery.py        # Folder walker
│   ├── tree.py             # In-memory skill tree
│   ├── index.py            # Search index
│   ├── mcp_server.py       # MCP tool definitions
│   ├── http_server.py      # HTTP server for web UI
│   └── static/
│       └── index.html      # Web UI (vanilla HTML/CSS/JS)
├── tests/
│   ├── test_discovery.py   # Tests for discovery
│   ├── test_frontmatter.py # Tests for YAML parsing
│   └── test_tools.py       # Tests for tree tools & search
├── sample_skills/          # Demo skills
├── HANDOFF.md              # Session handoff notes
├── AGENTS.md               # Agent conventions
└── IMPLEMENTATION_PLAN.md  # Full implementation plan
```

## Design Principles

- **Hierarchy for humans, search for models** — tree browsing and full-text search coexist
- **Filesystem as source of truth** — no database needed
- **Minimal dependencies** — only `mcp` and `pyyaml`
- **Read-only web UI** — no editing, no auth, no build step
- **Self-improving index** — usage tracking boosts popular/recent skills in search results

## Tests

```bash
python -m pytest tests/ -v
```
