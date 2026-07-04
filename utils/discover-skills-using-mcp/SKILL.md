---
name: discover-skills-using-mcp

tags:
  - meta
  - workflow
  - mcp
  - search

aliases:
  - how to use skills mcp
  - skills mcp guide
  - mcp workflow

description: Step-by-step guide for AI agents on how to discover, search, load, execute, and track skills using this MCP server.

depends_on: []

related:
  - creating-skills
  - maintaining-skills

followed_by:
  - creating-skills

uses: 0
last_used: null

steps:
  - util_skills/using-skills-mcp#search-first
  - util_skills/using-skills-mcp#explore-structure
  - util_skills/using-skills-mcp#inspect-metadata
  - util_skills/using-skills-mcp#load-content
  - util_skills/using-skills-mcp#execute-workflow
  - util_skills/using-skills-mcp#track-usage
  - util_skills/using-skills-mcp#refresh
---

# Using the Skills MCP Server

This server exposes 7 MCP tools for discovering, loading, and tracking skills.

## Efficient Discovery Strategy

When given a task, the goal is to find the most relevant skill with minimal calls.

### Core workflow

1. **Extract 1–3 keywords** from the user's task (topic, technology, action)
2. **`search(keyword)`** — always start here. One call may be all you need.
3. **Read the results**: each result has a **path** and a **score**. The path often tells you more than the score: `pentest/web/xss` clearly indicates "web security" even without reading the body. Prioritize results whose path matches your task domain.
4. **If you find candidates** → `info(path)` on the top 1–2 to check tags, description, depends_on, and usage signals
5. **Load the best match** → `read(path)` for full instructions
6. **Execute any sub-steps** → `steps(path)` then `read()` each sub-skill
7. **If nothing fits** → tell the user what you found and ask for clarification — don't force an irrelevant skill

### When your first search doesn't find what you need

Try **2–3 search attempts with different terms** before falling back to browsing. Your initial keywords may not match the skill's vocabulary:

```
# User says: "I need to analyze network traffic"
search("network traffic")   → nothing relevant
search("packet capture")    → no match either
search("wireshark")         → found! skill: "packet-capture"
```

If 2–3 search attempts still fail, **browse to discover vocabulary**:

```
browse("")                  → root groups: coding, pentest, general
```

The group names (`pentest`, `general`) and their child paths are indexed — browsing reveals the actual terms used in the skill tree. Once you see `pentest/ad/`, you know to search for "active directory" or "kerberos" next.

### Narrowing results

If a search returns too many results, **add more specific terms** to your query:

```
search("web")               → 6 results, many domains
search("web security")      → fewer, more targeted
search("/web.*sec/i")       → regex: any phrase with "web" near "sec"
```

### Key principle

**Search first, browse to learn vocabulary, search again.** Browsing root-to-leaf without prior search costs multiple round-trips and wastes calls. But browsing is invaluable for discovering what terms the skill tree actually uses — use it to inform better search queries, not as your primary navigation tool.

## search-first

**Tool**: `search(query)`

Before anything else, **search**. Don't guess paths — the index covers names, tags, aliases, description, body text, and **path segments** (folder names). Results are ranked by relevance, boosted by usage and recency.

```
search("python api")     → finds fastapi (score 145)
search("web")             → finds fastapi, xss (tag match)
search("kerberos")        → finds kerberoasting (alias match)
search("pentest")         → finds xss, kerberoasting (path match)
```

Search supports **wildcards** (`*`, `?`) and **regex** (`/pattern/flags`):

```
search("x*")              → finds xss (glob: starts with x)
search("*/xss")           → finds pentest/web/xss (glob: ends with /xss)
search("/p.*t/")          → finds pytest, pentest (regex: p...t)
search("/(?:xss|fast)/")  → finds xss, fastapi (regex: alternation)
search("/pent.*/i")       → case-insensitive regex
search("*")               → lists ALL skills (usage/recency sorted)
```

Don't default to `search("*")` — always search for a **specific** skill or topic. Only use `*` when the user explicitly asks to see all available skills.

Search returns a path + score. Use that path in subsequent calls.

## explore-structure

**Tool**: `browse(path, depth=1)`

When you need to understand the hierarchy or discover what's available in a domain. **Drill in by passing the child's path** from one browse result into the next:

```
browse("")                → root groups: coding, pentest, general
browse("coding")          → python, rust groups (2nd level)
browse("coding/python")   → fastapi, pytest skills (3rd level — leaf skills)
```

Use **`depth > 1`** to fetch multiple levels in one call:

```
browse("pentest", depth=2) → shows groups + all child skills
browse("", depth=3)        → full tree overview
```

A node with `node_type: "group"` is a container. Drill into it. A node with `node_type: "skill"` (or `"dual"`) carries a SKILL.md you can read.

## inspect-metadata

**Tool**: `info(path)`

Before loading the full body, check the metadata. It tells you:

- **tags / aliases** — alternative ways to identify this skill
- **depends_on** — prerequisites you should know first (call `info()` on those too)
- **related** — conceptually similar skills worth considering
- **followed_by** — natural next skills after mastering this one
- **uses / last_used** — quality signals; higher usage = more battle-tested
- **steps** — sub-skills that make up this skill's workflow (call `steps()` to execute them)

```
info("coding/python/fastapi")
# → shows depends_on: [python/basics, python/async]
# → shows related: [flask, starlette]
# → shows uses: 5 (well-used skill)
```

## load-content

**Tool**: `read(path)`

Once you've confirmed the skill is relevant, load its full SKILL.md body for detailed instructions, code samples, and explanations.

```
read("coding/python/fastapi")
# → returns full markdown with installation, examples, key concepts
```

## execute-workflow

**Tool**: `steps(path)`

Skills with multi-step workflows expose an ordered `steps` array. Call this to get the execution sequence, then `read()` each sub-skill in order:

```
steps("pentest/ad/kerberoasting")
# → returns: [discovery, extraction, cracking]

# Then execute in order:
#   1. read("pentest/ad/kerberoasting/discovery")
#   2. read("pentest/ad/kerberoasting/extraction")
#   3. read("pentest/ad/kerberoasting/cracking")
```

The `steps` array contains paths to sub-skills that drill into finer-grained instructions.

## track-usage

**Tool**: `use(path)`

After you have **successfully applied** a skill to the task at hand, call `use()`. This:

1. Increments the `uses` counter (boosts future search ranking)
2. Updates `last_used` timestamp (enables 7-day recency boost)
3. Persists both values to the SKILL.md file on disk

```
use("coding/python/fastapi")
# → uses: 0 → 1, last_used: null → "2026-07-04T..."
```

Only call `use()` after genuine successful application. This keeps the index self-improving.

## refresh

**Tool**: `reload()`

Call `reload()` when:

- New skill folders have been added to the repo
- Existing SKILL.md files have been edited
- The index feels stale or results seem wrong

```
reload()
# → re-scans repo, re-validates all skills, rebuilds index
```

No server restart needed.
