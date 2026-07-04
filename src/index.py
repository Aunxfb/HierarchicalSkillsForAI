from __future__ import annotations
import fnmatch
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from .models import SearchResult


class SearchIndex:
    def __init__(self):
        self.skills: dict[str, dict] = {}
        self.name_index: dict[str, list[str]] = {}
        self.tag_index: dict[str, list[str]] = {}
        self.alias_index: dict[str, list[str]] = {}
        self.path_index: dict[str, list[str]] = {}
        self.text_index: dict[str, list[str]] = {}

    def build(self, tree):
        self.skills.clear()
        self.name_index.clear()
        self.tag_index.clear()
        self.alias_index.clear()
        self.path_index.clear()
        self.text_index.clear()

        for path, node in tree.nodes_by_path.items():
            if not node.skill_metadata:
                continue
            m = node.skill_metadata
            info = {
                "name": m.name,
                "path": path,
                "tags": m.tags,
                "aliases": m.aliases,
                "description": m.description,
                "body": node.body or "",
                "uses": m.uses,
                "last_used": m.last_used,
            }
            self.skills[path] = info

            name_lower = m.name.lower()
            self.name_index.setdefault(name_lower, []).append(path)

            for tag in m.tags:
                self.tag_index.setdefault(tag.lower(), []).append(path)

            for alias in m.aliases:
                self.alias_index.setdefault(alias.lower(), []).append(path)

            if path:
                parts = path.lower().split("/")
                for part in parts:
                    self.path_index.setdefault(part, []).append(path)
                self.path_index.setdefault(path, []).append(path)

            text = f"{m.description} {node.body or ''}"
            words = set(re.findall(r"\w+", text.lower()))
            for word in words:
                if len(word) >= 2:
                    self.text_index.setdefault(word, []).append(path)

    def update_usage(self, path: str, uses: int, last_used: str | None):
        if path in self.skills:
            self.skills[path]["uses"] = uses
            self.skills[path]["last_used"] = last_used

    @staticmethod
    def _compile_query(q: str) -> tuple[re.Pattern, bool]:
        if q.startswith("/") and len(q) >= 3:
            last_slash = q.rindex("/")
            if last_slash > 0:
                after = q[last_slash + 1:]
                if all(c in "ism" for c in after):
                    pattern = q[1:last_slash]
                    flags = 0
                    if "i" in after:
                        flags |= re.IGNORECASE
                    if "s" in after:
                        flags |= re.DOTALL
                    return re.compile(pattern, flags), True
        if "*" in q or "?" in q:
            glob_q = q.lstrip("/")
            return re.compile(fnmatch.translate(glob_q), re.IGNORECASE), True
        return re.compile(re.escape(q), re.IGNORECASE), False

    def search(self, query: str) -> list[SearchResult]:
        q = query.lower().strip()
        if not q:
            return []

        pattern, is_pattern = self._compile_query(query)

        scores: dict[str, float] = {}

        for name_lower, paths in self.name_index.items():
            if is_pattern:
                if pattern.search(name_lower):
                    for p in paths:
                        scores[p] = scores.get(p, 0) + 75
            else:
                if name_lower == q:
                    for p in paths:
                        scores[p] = scores.get(p, 0) + 100
                elif q in name_lower:
                    for p in paths:
                        scores[p] = scores.get(p, 0) + 50

        for tag, paths in self.tag_index.items():
            if pattern.search(tag):
                for p in paths:
                    scores[p] = scores.get(p, 0) + 30

        for alias, paths in self.alias_index.items():
            if pattern.search(alias):
                for p in paths:
                    scores[p] = scores.get(p, 0) + 25

        for path_seg, paths in self.path_index.items():
            if is_pattern:
                if pattern.search(path_seg):
                    for p in paths:
                        scores[p] = scores.get(p, 0) + 28
            else:
                if path_seg == q:
                    for p in paths:
                        scores[p] = scores.get(p, 0) + 35
                elif q in path_seg:
                    for p in paths:
                        scores[p] = scores.get(p, 0) + 20

        for word, paths in self.text_index.items():
            if is_pattern:
                if pattern.search(word):
                    for p in paths:
                        scores[p] = scores.get(p, 0) + 10
            else:
                if q in word or word in q:
                    for p in paths:
                        scores[p] = scores.get(p, 0) + 10

        now = datetime.now(timezone.utc)
        for p, info_data in self.skills.items():
            if p in scores:
                scores[p] *= 1 + min(info_data["uses"], 100) * 0.01
                last = info_data.get("last_used")
                if last:
                    try:
                        last_dt = datetime.fromisoformat(last.rstrip("Z"))
                        if now - last_dt < timedelta(days=7):
                            scores[p] *= 1.5
                    except (ValueError, TypeError):
                        pass

        sorted_paths = sorted(scores.items(), key=lambda x: (-x[1], x[0]))

        return [
            SearchResult(
                path=p,
                score=round(score, 2),
                name=self.skills[p]["name"],
            )
            for p, score in sorted_paths
        ]
