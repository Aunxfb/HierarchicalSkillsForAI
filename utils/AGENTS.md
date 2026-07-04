# Skill Discovery — Agent Quick Reference

## Efficient Workflow

```
search(keywords)   → ranked results (path + score)
browse(path, depth)→ view tree structure (depth>1 for nested levels)
info(path)         → check metadata before loading body
read(path)         → full skill content
steps(path)        → sub-skill workflow
use(path)          → track successful application
```

## Finding the Right Skill

1. **Extract 1–3 keywords** from the user's task
2. **`search()`** — one call may be all you need. Prioritize results whose **path** matches the task domain (path often tells more than score).
3. **No results?** Try 2–3 searches with **different terms** (synonyms, related tech). If still nothing, `browse("", depth=2)` to discover vocabulary used in the tree, then search again.
4. **Too many results?** Add more specific terms or use regex: `/web.*sec/i`
5. **`info()`** on top candidates to verify relevance
6. **`read()`** the best match for full instructions
7. **`steps()`** then `read()` each sub-skill for workflows
8. **`use()`** after successful application

## Search Capabilities

| Type | Example | Matches |
|------|---------|---------|
| Plain text | `search("fastapi")` | name, tags, aliases, description, body, path segments |
| Wildcard | `search("x*")` or `search("*/xss")` | glob patterns with `*` and `?` |
| Regex | `search("/p.*t/")` or `search("/pent.*/i")` | `/pattern/flags` — `i` = case-insensitive |

## Key Principles

- **Search first, browse for vocabulary, search again.** Don't browse root-to-leaf as default navigation.
- **Don't `search("*")`** unless the user explicitly asks to see all skills.
- **`read()` only after confirming relevance** with `info()` or by reading the path.
