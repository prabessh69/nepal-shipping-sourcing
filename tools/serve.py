#!/usr/bin/env python3
"""Local preview server that mimics Cloudflare Pages closely enough for testing.

    python3 tools/serve.py [port]      # default 8080, serves ./site

- Applies headers from site/_headers (exact paths and trailing /* splats)
- Serves /dir/ -> /dir/index.html and redirects /dir -> /dir/
- Returns site/404.html with status 404 for unknown paths
Standard library only; for local testing, not production.
"""
import http.server
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "site"


def parse_headers_file():
    rules, current = [], None
    for line in (ROOT / "_headers").read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            current = (line.strip(), [])
            rules.append(current)
        elif current and ":" in line:
            k, v = line.strip().split(":", 1)
            current[1].append((k.strip(), v.strip()))
    return rules


RULES = parse_headers_file()


def match(pattern, path):
    if pattern.endswith("*"):
        return path.startswith(pattern[:-1])
    return path == pattern


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".webmanifest": "application/manifest+json",
        ".svg": "image/svg+xml",
        ".woff2": "font/woff2",
        ".js": "text/javascript",
        ".xml": "application/xml",
    }

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def end_headers(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        for pattern, headers in RULES:
            if match(pattern, path):
                for k, v in headers:
                    self.send_header(k, v)
        super().end_headers()

    def send_head(self):
        path = self.path.split("?", 1)[0]
        fs = Path(self.translate_path(path))
        if path.startswith("/_headers") or not fs.exists():
            return self._not_found()
        if fs.is_dir() and not (fs / "index.html").exists():
            return self._not_found()
        return super().send_head()

    def _not_found(self):
        body = (ROOT / "404.html").read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        from io import BytesIO
        return BytesIO(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"Serving {ROOT} at http://127.0.0.1:{port}/")
        httpd.serve_forever()
