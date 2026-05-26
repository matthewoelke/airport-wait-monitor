from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .service import SUPPORTED_AIRPORTS, build_all_airports_payload, build_airport_payload


STATIC_DIR = Path(__file__).resolve().parent / "static"


class WaitMonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/waits":
            airport = query.get("airport", [""])[0] or ""
            self.send_json(build_airport_payload(airport))
            return

        if path == "/api/waits/all":
            self.send_json(build_all_airports_payload())
            return

        if path == "/" or path == "/index.html":
            self.send_static("index.html", "text/html; charset=utf-8")
            return

        if path == "/app.js":
            self.send_static("app.js", "application/javascript; charset=utf-8")
            return

        if path == "/styles.css":
            self.send_static("styles.css", "text/css; charset=utf-8")
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def send_json(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, filename: str, content_type: str) -> None:
        file_path = STATIC_DIR / filename
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the airport wait monitor API and dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind. Default: 8000")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), WaitMonitorHandler)
    print(f"Serving airport wait monitor on http://{args.host}:{args.port}")
    print(f"Supported airports: {', '.join(SUPPORTED_AIRPORTS)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
