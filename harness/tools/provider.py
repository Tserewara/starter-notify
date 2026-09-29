"""The delivery provider, faked. The service POSTs each notification to
/send; the provider keeps what it accepted, with the time it arrived.

    POST   /send        {"id": ..., "channel": ..., ...} -> 200, or 503 during an outage
    GET    /received    every notification accepted: [{"id", "channel", "urgency", "received_at"}]
    DELETE /received    forget them
    POST   /_control    {"latency_ms": N} and/or {"fail": true|false}
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

state = {"latency_ms": 40, "fail": False}
received = []
lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def body(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")

    def reply(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path == "/_control":
            with lock:
                state.update({k: v for k, v in self.body().items() if k in state})
                return self.reply(200, dict(state))
        if self.path != "/send":
            return self.reply(404, {"detail": "not found"})
        record = self.body()
        with lock:
            latency, fail = state["latency_ms"], state["fail"]
        time.sleep(latency / 1000)
        if fail:
            return self.reply(503, {"detail": "provider outage"})
        with lock:
            received.append({"id": record.get("id"), "channel": record.get("channel"),
                             "urgency": record.get("urgency"), "received_at": time.time()})
        self.reply(200, {"accepted": True})

    def do_GET(self):
        if self.path == "/health":
            return self.reply(200, {"ok": True})
        with lock:
            self.reply(200, list(received))

    def do_DELETE(self):
        with lock:
            received.clear()
        self.reply(200, {"cleared": True})


ThreadingHTTPServer(("0.0.0.0", 8001), Handler).serve_forever()
