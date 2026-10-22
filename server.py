import json
import os
from threading import Lock
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 9600
DATA_FILE = "data.json"

DATA_LOCK = Lock()

VALID_CHAIR_STATUSES = {
    "available",
    "busy",
    "unavailable"
}


def load_data():
    with DATA_LOCK:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def save_data(data):

    temp_file = DATA_FILE + ".tmp"

    with DATA_LOCK:

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        os.replace(temp_file, DATA_FILE)


class Handler(BaseHTTPRequestHandler):

    def send_json(self, obj, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps(obj).encode("utf-8")
        )

    def do_GET(self):

        parsed = urlparse(self.path)

        if parsed.path == "/api/status":

            salon_id = parse_qs(
                parsed.query
            ).get(
                "salon",
                [""]
            )[0]

            data = load_data()

            salon = data["salons"].get(
                salon_id
            )

            if not salon:
                return self.send_json(
                    {"error": "Salon not found"},
                    404
                )

            return self.send_json({
                "id": salon_id,
                "name": salon["name"],
                "address": salon["address"],
                "chairs": salon["chairs"]
            })

        if self.path == "/" or self.path.startswith("/?"):

            with open(
                "index.html",
                "rb"
            ) as f:

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/html"
                )
                self.end_headers()
                self.wfile.write(
                    f.read()
                )
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):

        if self.path != "/api/update":
            self.send_response(404)
            self.end_headers()
            return

        length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )

        body = self.rfile.read(length)

        payload = json.loads(body)

        salon_id = payload.get("salon")
        admin_code = payload.get("adminCode")
        chairs = payload.get("chairs")

        data = load_data()

        salon = data["salons"].get(
            salon_id
        )

        if not salon:
            return self.send_json(
                {"error": "Salon not found"},
                404
            )

        if admin_code != salon["adminCode"]:
            return self.send_json(
                {"error": "Invalid admin code"},
                403
            )

        for chair in chairs:

            if chair["status"] not in VALID_CHAIR_STATUSES:

                return self.send_json(
                    {
                        "error":
                        "Invalid chair status"
                    },
                    400
                )

        salon["chairs"] = chairs
        salon["updatedUtc"] = (
            datetime.utcnow().isoformat()
        )

        save_data(data)

        self.send_json(
            {"success": True}
        )


server = ThreadingHTTPServer(
    ("0.0.0.0", PORT),
    Handler
)

print(
    f"Running at http://0.0.0.0:{PORT}"
)

server.serve_forever()