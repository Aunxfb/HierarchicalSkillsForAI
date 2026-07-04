# 🧠 Skills MCP Hierarchical System — Implementation Plan

## 1. Core Concept

Build a **single MCP server** that exposes skills as a **tree + searchable index**:

* Human-facing: hierarchical browsing (folders/domains)
* Agent-facing: fast search + direct path access
* Skills stored as folders containing `SKILL.md` with YAML frontmatter
* Server takes `--repo <path>` (root folder) and `--max-depth <N>` at startup
* Built-in web UI for human browsing (tree + search + view, no editing)
* No dynamic MCP spawning, no tool explosion

---

## 2. Data Model

### File-based structure (source of truth)

Server walks the `--repo` tree up to `--max-depth`. 

* A folder is a **skill** if it contains `SKILL.md` — stop descending.
* A folder is a **group** if it contains subfolders — recurse.
* A folder can be **both** (has `SKILL.md` AND subfolders). In that case it's a group that also carries a skill of its own — `browse()` lists both the skill and child groups.
* A folder with neither `SKILL.md` nor subfolders is silently ignored.

```text
skills/                          # --repo root
  coding/                        # group
    python/                      # group
      fastapi/                   # skill (dead end — contains SKILL.md)
        SKILL.md
      pandas/
        SKILL.md
    rust/
      tokio/
        SKILL.md

  pentest/
    ad/
      kerberoasting/
        SKILL.md
    web/
      xss/
        SKILL.md

  general/
    writing/
      email/
        SKILL.md
```

---

### Skill folder contains `SKILL.md` with YAML frontmatter

`name` is the canonical identifier (does not need to match folder name). Validated for **uniqueness** across the entire tree — two skills cannot share a name. If any `name` duplicates → error + abort.

```yaml
---
name: fastapi

tags:
  - python
  - api
  - web

aliases:
  - fast api
  - fastapi framework

description: Python web framework for building APIs

# ── Skill graph ──────────────────────────────────────
depends_on:      # prerequisites the AI should know first
  - python/basics
related:         # conceptually similar skills
  - flask
  - starlette
followed_by:     # natural next skills after mastering this one
  - sqlalchemy
  - pytest

# ── Quality signals (auto-managed by use()) ──────────
uses: 0
last_used: null

# ── Composition ──────────────────────────────────────
steps:
  - setup/project-scaffold
  - coding/python/fastapi/routing
  - coding/python/fastapi/middleware
---
```

---

## 3. CLI Arguments & Startup Validation

### Server startup

```text
python mcp_server.py --port 8080
```

* `--repo` (optional, default `sample_skills`): path to the root folder containing grouped skills
* `--max-depth` (optional, default 4): how deep to walk the folder tree when discovering skills
* `--port` (optional, default 8080): port for the web UI

### Startup validation (fail-fast)

On startup the server walks the `--repo` tree and validates **every** discovered skill:

1. Folder must contain a `SKILL.md` file
2. `SKILL.md` must have valid YAML frontmatter (`---` delimited)
3. The `name` field must be **unique** across the entire tree (no duplicates)
4. Folders beyond `--max-depth` are silently ignored

If **any** skill fails validation → log each error to stderr, then **abort** with non-zero exit code.

### Discovery algorithm

```
walk(path, depth):
  if depth > max_depth → stop
  has_skill = path contains SKILL.md
  has_subfolders = path contains subdirectories
  if has_skill:
    validate_skill(path)
    add_skill_node(path)
  if has_subfolders:
    if has_skill: mark node as "group + skill" (dual node)
    recurse into subdirectories
  if neither: silently ignore
```

---

## 4. MCP API (minimal + sufficient)

### A. Hierarchy browsing

```text
browse(path)
```

* Input: `" / "`, `"coding"`, `"coding/python"`
* Output: child nodes (groups + skills)

Example:

```json
{
  "path": "coding/python",
  "children": [
    "fastapi",
    "pandas",
    "asyncio"
  ]
}
```

---

### B. Read skill

```text
read(path)
```

* Returns full SKILL.md

Example:

```text
coding/python/fastapi
```

---

### C. Search (critical)

```text
search(query)
```

* Searches:

  * skill name
  * tags
  * aliases
  * description
  * path segments (folder names in the skill's path)
* Returns ranked paths

Example:

```json
[
  "pentest/ad/kerberoasting",
  "general/networking/kerberos"
]
```

---

### D. Optional: metadata-only inspect

```text
info(path)
```

* Returns lightweight metadata without full skill content (includes relations, usage stats, steps list)

---

### E. Track usage (quality signal)

```text
use(path)
```

* Increments `uses` counter and sets `last_used` to current timestamp in the skill's metadata
* Returns updated metadata
* The AI **should** call this after successfully applying a skill — enables search ranking to boost popular/recent skills

### F. Get workflow steps

```text
steps(path)
```

* Returns the ordered `steps` array from the skill's metadata (sub-skill paths)
* Enables the AI to execute a multi-step workflow without manually hunting for sub-skills

### G. Hot-reload

```text
reload()
```

* Re-scans the `--repo` tree, re-validates all skills, rebuilds index
* No server restart needed — use after adding/removing skill folders while the server runs

---

## 5. Web UI (Human-Facing)

A lightweight web UI is served at `http://localhost:<port>` for human browsing. It reuses the same in-memory tree + index — no duplicate logic.

### Pages / features

| Feature | Description |
|---|---|
| **Tree browser** | Expandable/collapsible sidebar showing the skill hierarchy (groups → skills) |
| **Search bar** | Text input that queries the same `search()` index, shows ranked results |
| **Skill view** | Renders `SKILL.md` content (markdown) when a skill node is clicked |
| **Info panel** | Shows YAML metadata (name, tags, aliases, description, depends_on, related, steps) for the selected skill |
| **Usage stats** | Shows `uses` count and `last_used` timestamp for the selected skill |

### Design constraints

* Single-page application (no routing, no build step)
* Vanilla HTML + CSS + JS served as embedded static assets
* All data fetched via internal REST/JSON endpoints (backed by the same tree + index)
* No authentication, no editing, no write operations

### Implementation

```
Server (Python)
  ├── MCP transport (stdio/SSE)  ← agents
  ├── HTTP server                 ← browser
  │     ├── GET /                 → serves index.html
  │     ├── GET /api/browse?path= → returns child nodes (JSON)
  │     ├── GET /api/search?q=    → returns ranked paths (JSON)
  │     └── GET /api/read?path=   → returns skill content + metadata (JSON)
  └── In-memory tree + index
```

---

## 6. Indexing Layer (important)

Build an in-memory or persisted index:

* Map:

  * tags → skills
  * aliases → skills
  * keywords → skills
  * path → node
  * body text → skills (index SKILL.md prose beyond YAML)
  * `depends_on` / `related` / `followed_by` → skills (traversable graph)

* Search ranking signals (in order of priority):

  1. **Exact name match** — highest
  2. **Tag/alias match** — high
  3. **Description/body keyword match** — medium
  4. **Usage boost** — `uses` count adds a small multiplier
  5. **Recency boost** — `last_used` within last 7 days adds a multiplier

Implementation options:

* simple JSON index (MVP)
* SQLite FTS (better)
* Meilisearch (optional advanced)

---

## 7. Resolution Logic

When agent calls:

### browse()

* in-memory tree traversal (group nodes → children, dual nodes include their SKILL.md)

### search()

* index lookup → ranked by name/tag/alias/body match, boosted by usage and recency

### read()

* filesystem read (SKILL.md at the resolved path)

### info()

* returns parsed YAML metadata from the in-memory node

### use()

* in-memory update to `uses` counter + `last_used` timestamp; optionally persisted

### steps()

* returns `steps` array from the skill's metadata — sub-skill paths for workflow execution

### reload()

* full re-scan of `--repo` tree, re-validate, rebuild index

No dynamic loading complexity needed.

---

## 8. UX Strategy for the LLM

The model should behave like:

### Default behavior:

1. Use `search()` first

### When exploring:

2. Use `browse()` to understand structure

### When executing:

3. Call `steps(path)` if the skill has a workflow, then `read()` each sub-skill
4. Use `read()` to load skill content

### After executing:

5. Call `use(path)` to signal the skill was successfully applied — this improves future search ranking

### When skills change:

6. Call `reload()` if newly added skills aren't appearing

---

## 9. Recommended Tree Design Rules

Keep hierarchy:

* `--max-depth` should be set to 3–4 levels
* max children per node: ~10–20
* anything larger → split or rely on search
* folders beyond `--max-depth` are silently ignored

Example:

```text
coding/
  python/
    web/
    data/
    async/
```

---

## 10. Performance Goals

* browse: O(1) or O(log n)
* search: sub-100ms (indexed)
* read: filesystem I/O only

---

## 11. What NOT to build (important)

Avoid:

* ❌ dynamic MCP tool registration
* ❌ spawning per-skill servers
* ❌ deep plugin architectures
* ❌ complex runtime dependency graphs

* ❌ editing/CRUD in the web UI
* ❌ authentication or multi-user
* ❌ build tooling or framework for the frontend

Keep it:

> “Filesystem + index + 7 MCP functions + read-only web UI”

---

## 12. MVP Build Steps

### Step 1

Implement `--repo` / `--max-depth` / `--port` CLI parsing + startup validation (with root-level `mcp_server.py` wrapper defaulting to `sample_skills`):

* Recursive discovery (SKILL.md → skill, subfolders → group, both → dual)
* YAML frontmatter parser (all fields including graph + quality + steps)
* `name` uniqueness validation (not folder-name match)
* Warn + abort on invalid skills

### Step 2

Implement in-memory tree model (typed nodes: Skill | Group | Dual) from discovered structure

### Step 3

Implement:

* `browse()` — returns children (groups + skills, dual nodes include both)
* `read()` — returns full SKILL.md body
* `info()` — returns parsed YAML metadata

### Step 4

Build index:

* tags, aliases, keywords, description, body text
* relation fields (depends_on, related, followed_by)
* Ranked by name match → tag/alias → text match, boosted by usage + recency

### Step 5

Implement `search()` — with usage/recency boost

### Step 6

Implement `use()` — increment counter, update timestamp (in-memory + optional persistence)

### Step 7

Implement `steps()` — return steps array from metadata

### Step 8

Implement `reload()` — full re-scan, re-validate, re-index

### Step 9

Add caching + optional persistence (mapping, usage stats)

### Step 10

Build static web UI:

* Embed single `index.html` with tree browser, search bar, skill view, info panel, usage stats
* Serve via HTTP alongside MCP transport
* Wire up to internal REST endpoints

### Step 11

Polish: error display for missing/empty repo, graceful shutdown

---

## 13. Final Architecture

```text
  Agent (MCP client)             Human (browser)
       ↓                              ↓
Skills MCP Server  ←  --repo <path> --max-depth <N> --port <P>
       │                              │
       ├── MCP transport              ├── HTTP (web UI)
       │     browse(path)             │     GET /          → index.html
       │     search(query)            │     GET /api/browse?path=
       │     read(path)               │     GET /api/search?q=
       │     info(path)               │     GET /api/read?path=
       │     use(path)                │
       │     steps(path)              │
       │     reload()                 │
       │                              │
       └──────────┬───────────────────┘
                  ↓
      ┌───────────┼───────────┐
      ↓           ↓           ↓
 File system   Index     Usage stats
 (SKILL.md)   (tags,     (uses count,
               aliases,   last_used)
               body,
               relations)
      ↓
skills/ (groups, skills, dual group+skill nodes)
```

---

## 14. Implementation Checklist

### Phase 1 — Core scaffold
- [x] Create Python project structure (`pyproject.toml`, entry point, MCP SDK dependency)
- [x] Parse CLI args: `--repo`, `--max-depth`, `--port`
- [x] Implement recursive folder walker with depth limit
- [x] Detect skill (has `SKILL.md`), group (has subfolders), dual (both), ignore (neither)

### Phase 2 — YAML parsing & validation
- [x] Parse YAML frontmatter from `SKILL.md`
- [x] Validate required fields (`name`)
- [x] Validate `name` uniqueness across the entire tree
- [x] On validation failure: log per-skill errors to stderr, abort with non-zero exit

### Phase 3 — In-memory model & core MCP tools
- [x] Build in-memory tree (typed nodes: Skill, Group, Dual)
- [x] Implement `browse(path)` — returns child groups + skills
- [x] Implement `read(path)` — returns full SKILL.md body
- [x] Implement `info(path)` — returns parsed YAML metadata

### Phase 4 — Index & search
- [x] Build index over: name, tags, aliases, description, body text
- [x] Build relation index: `depends_on`, `related`, `followed_by`
- [x] Implement `search(query)` with ranked results (name match > tag/alias > text)
- [x] Add usage boost and recency boost to ranking

### Phase 5 — Quality & composition tools
- [x] Implement `use(path)` — increment `uses`, set `last_used`
- [x] Implement `steps(path)` — return `steps` array from metadata

### Phase 6 — Hot-reload
- [x] Implement `reload()` — full re-scan, re-validate, re-index

### Phase 7 — Web UI
- [x] Build single `index.html` (vanilla HTML + CSS + JS)
- [x] Implement tree browser (expandable/collapsible sidebar)
- [x] Implement search bar wired to `/api/search`
- [x] Implement skill view (rendered markdown on click)
- [x] Implement info panel showing metadata + usage stats
- [x] Serve via HTTP alongside MCP transport

### Phase 8 — Polish
- [x] Handle missing/empty `--repo` gracefully
- [x] Graceful shutdown (SIGTERM, SIGINT)
- [x] Persist usage stats back to `SKILL.md` YAML frontmatter on `use()`
- [x] Root-level `mcp_server.py` entry point for agent simplicity
- [x] Write tests for discovery, validation, and each MCP tool

---

## Bottom line

This is **not overengineered**, and it *does* scale to 100–1000+ skills.

The key insight:

> hierarchy is for humans
> search is for the model
> the graph connects skills
> usage makes the index self-improving
