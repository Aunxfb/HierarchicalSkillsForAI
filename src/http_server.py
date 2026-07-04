from __future__ import annotations
import json
import http.server
import os
from urllib.parse import urlparse, parse_qs
from .tree import SkillTree
from .index import SearchIndex


class SkillsHTTPHandler(http.server.BaseHTTPRequestHandler):
    tree: SkillTree = None
    index: SearchIndex = None
    static_dir: str = ""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        try:
            if path == "/":
                self._serve_static("index.html")
            elif path == "/api/browse":
                p = params.get("path", [""])[0]
                d = params.get("depth", ["1"])[0]
                try:
                    depth = max(1, int(d))
                except (ValueError, TypeError):
                    depth = 1
                self._json_response(self.tree.browse(p, depth))
            elif path == "/api/search":
                q = params.get("q", [""])[0]
                results = self.index.search(q) if q else []
                self._json_response(
                    [{"path": r.path, "score": r.score, "name": r.name} for r in results]
                )
            elif path == "/api/read":
                p = params.get("path", [""])[0]
                if not p:
                    self._json_response({"error": "missing 'path' parameter"}, status=400)
                    return
                try:
                    content = self.tree.read(p)
                    info_data = self.tree.info(p)
                    self._json_response({"content": content, "metadata": info_data})
                except KeyError as e:
                    self._json_response({"error": str(e)}, status=404)
            elif path == "/api/info":
                p = params.get("path", [""])[0]
                if not p:
                    self._json_response({"error": "missing 'path' parameter"}, status=400)
                    return
                try:
                    self._json_response(self.tree.info(p))
                except KeyError as e:
                    self._json_response({"error": str(e)}, status=404)
            else:
                self._serve_static(path.removeprefix("/"))
        except Exception as e:
            self._json_response({"error": f"Internal server error: {e}"}, status=500)

    def _serve_static(self, filename: str):
        safe = os.path.normpath(os.path.join(self.static_dir, filename))
        if not safe.startswith(os.path.normpath(self.static_dir)):
            self.send_error(403)
            return
        if not os.path.isfile(safe):
            self.send_error(404)
            return
        filepath = safe
        self.send_response(200)
        ext = os.path.splitext(filename)[1]
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
        }
        self.send_header(
            "Content-Type", content_types.get(ext, "application/octet-stream")
        )
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    def _json_response(self, data, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode("utf-8"))

    def log_message(self, fmt: str, *args):
        pass


def create_http_server(
    host: str, port: int, tree: SkillTree, index: SearchIndex, static_dir: str
) -> http.server.HTTPServer:
    SkillsHTTPHandler.tree = tree
    SkillsHTTPHandler.index = index
    SkillsHTTPHandler.static_dir = static_dir
    return http.server.HTTPServer((host, port), SkillsHTTPHandler)
