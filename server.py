#!/usr/bin/env python3
"""One board for every phone on this Wi-Fi. No database.

From this folder:
    python server.py

Phones open http://<this-laptop-ip>:9600
"""

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUS = ROOT / "status.json"
PASSWORD = "08061980"
ALLOWED = {"green", "red", "grey", "black"}
PORT = 9600


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/status":
            body = STATUS.read_bytes() if STATUS.exists() else b'{"chairs":["green","green","green"]}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/status":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            chairs = payload["chairs"]
        except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
            self.send_error(400)
            return
        if payload.get("password") != PASSWORD:
            self.send_error(403)
            return
        if not isinstance(chairs, list) or len(chairs) != 3 or any(c not in ALLOWED for c in chairs):
            self.send_error(400)
            return
        body = json.dumps({"chairs": chairs}).encode("utf-8")
        STATUS.write_bytes(body)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"Craze Men's Saloon board on http://0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()