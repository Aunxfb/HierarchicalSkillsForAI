# 🧠 Skills MCP Hierarchical System — Implementation Plan

## 1. Core Concept

Build a **single MCP server** that exposes skills as a **tree + searchable index**:

* Human-facing: hierarchical browsing (folders/domains)
* Agent-facing: fast search + direct path access
* Skills stored as files with metadata
* No dynamic MCP spawning, no tool explosion

---

## 2. Data Model

### File-based structure (source of truth)

```text
skills/
  coding/
    python/
      fastapi.md
      pandas.md
    rust/
      tokio.md

  pentest/
    ad/
      kerberoasting.md
    web/
      xss.md

  general/
    writing/
      email.md
```

---

### Each skill file contains metadata

```yaml
name: FastAPI
path: coding/python/fastapi

tags:
  - python
  - api
  - web

aliases:
  - fast api
  - fastapi framework

description: Python web framework for APIs

group:
  - coding/python
```

---

## 3. MCP API (minimal + sufficient)

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

* Returns lightweight metadata without full skill content

---

## 4. Indexing Layer (important)

Build an in-memory or persisted index:

* Map:

  * tags → skills
  * aliases → skills
  * keywords → skills
  * path → node

Implementation options:

* simple JSON index (MVP)
* SQLite FTS (better)
* Meilisearch (optional advanced)

---

## 5. Resolution Logic

When agent calls:

### browse()

* just filesystem traversal

### search()

* index lookup → ranked results

### read()

* filesystem read

No dynamic loading complexity needed.

---

## 6. UX Strategy for the LLM

The model should behave like:

### Default behavior:

1. Use `search()` first

### When exploring:

2. Use `browse()` to understand structure

### When executing:

3. Use `read()` to load skill

---

## 7. Recommended Tree Design Rules

Keep hierarchy:

* max depth: 3–4 levels
* max children per node: ~10–20
* anything larger → split or rely on search

Example:

```text
coding/
  python/
    web/
    data/
    async/
```

---

## 8. Performance Goals

* browse: O(1) or O(log n)
* search: sub-100ms (indexed)
* read: filesystem I/O only

---

## 9. What NOT to build (important)

Avoid:

* ❌ dynamic MCP tool registration
* ❌ spawning per-skill servers
* ❌ deep plugin architectures
* ❌ complex runtime dependency graphs

Keep it:

> “Filesystem + index + 4 MCP functions”

---

## 10. MVP Build Steps

### Step 1

Implement folder-based skills repo

### Step 2

Implement:

* `browse()`
* `read()`

### Step 3

Add metadata parser (YAML frontmatter)

### Step 4

Build index:

* tags
* aliases
* keywords

### Step 5

Implement `search()`

### Step 6

Add caching + optional persistence

---

## 11. Final Architecture

```text
Agent
  ↓
Skills MCP Server
  ├── browse(path)
  ├── search(query)
  ├── read(path)
  └── info(path)
        ↓
   File system + Index
        ↓
   skills/ (hierarchical tree)
```

---

## Bottom line

This is **not overengineered**, and it *does* scale to 100–1000+ skills.

The key insight:

> hierarchy is for humans
> search is for the model
> metadata is the glue
