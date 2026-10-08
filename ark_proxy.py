"""Mandatory proposer proxy — the budget enforcement POINT (rsi/verified-lemma-growth).

Architecture (v11, replaces helper-invoked counting):
  - the ONLY route from Work to the proposer API is this proxy;
  - the container env declares ARK_PROXY_URL=http://127.0.0.1:8080;
    the real ARK endpoint and key are NOT in Work env (they live in
    the proxy's own process env, injected by the harness);
  - the task's network allowlist admits ONLY loopback traffic, so a
    candidate that bypasses the Python helpers (curl, raw sockets,
    its own urllib code) still reaches the API exclusively through
    this proxy — the counter is architectural, not advisory;
  - the proxy counts one unit per UPSTREAM dispatch attempt (429
    backoff retries included), enforces BudgetExhausted with HTTP 429
    + a machine-readable body before dispatch at the cap, and
    persists its count atomically to the budget state file.

Run inside Work:  python3 ark_proxy.py  (foreground; port 8080)
The loop code starts it automatically and waits for /health.
"""
import json
import os
import re
import socket
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROXY_PORT = int(os.environ.get("ARK_PROXY_PORT", "8080"))
UPSTREAM = os.environ.get("ARK_UPSTREAM_URL",
                          "https://ark.cn-beijing.volces.com/api/coding/v3")
UPSTREAM_KEY = os.environ.get("ARK_API_KEY", "")  # NOT exported to the agent
BUDGET_LIMIT = int(os.environ.get("FLYLOOP_CALL_BUDGET", "200"))
STATE_PATH = os.environ.get(
    "ARK_BUDGET_STATE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "runs", "budget_state.json"))

_count = 0
_lock = threading.Lock()


class BudgetExhausted(RuntimeError):
    pass


def _load_count():
    global _count
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            _count = int(json.load(f).get("calls", 0))
    except (OSError, ValueError):
        _count = 0


def _persist():
    try:
        d = os.path.dirname(STATE_PATH)
        if d:
            os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"calls": _count, "limit": BUDGET_LIMIT,
                       "source": "ark_proxy"}, f)
        os.replace(tmp, STATE_PATH)
    except OSError:
        pass


def consume():
    """One unit per upstream dispatch attempt; raise at the cap."""
    global _count
    with _lock:
        if _count >= BUDGET_LIMIT:
            raise BudgetExhausted(
                f"proposer call budget {BUDGET_LIMIT} exhausted")
        _count += 1
        _persist()


def remaining():
    return max(0, BUDGET_LIMIT - _count)


# -------- upstream forwarder (one unit per attempt, retries included) --

_FWD_HEADERS = ("content-type", "accept", "user-agent")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quiet default logging
        pass

    def _forbidden(self, why):
        body = json.dumps({"error": "forbidden", "why": why}).encode()
        self.send_response(403)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _budget(self, msg):
        body = json.dumps({"error": "budget_exhausted",
                           "calls": _count, "limit": BUDGET_LIMIT,
                           "why": msg}).encode()
        self.send_response(429)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"ok": True, "calls": _count,
                               "limit": BUDGET_LIMIT,
                               "remaining": remaining()}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._forbidden("only POST /responses and GET /health are served")

    def do_POST(self):
        if not re.fullmatch(r"/(responses|chat/completions)/?", self.path):
            self._forbidden("only POST /responses is served")
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        # one unit per upstream attempt: 429 backoff retries each count
        attempts = 0
        for attempt in range(3):
            try:
                consume()
            except BudgetExhausted as e:
                self._budget(str(e))
                return
            attempts += 1
            req = urllib.request.Request(
                UPSTREAM + self.path, data=payload,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {UPSTREAM_KEY}"})
            try:
                with urllib.request.urlopen(req, timeout=900) as r:
                    data = r.read()
                    code = r.status
                break
            except urllib.error.HTTPError as ex:
                if ex.code == 429 and attempt < 2:
                    time.sleep(60 * (attempt + 1))
                    continue
                data = ex.read() if hasattr(ex, "read") else b"{}"
                code = ex.code
                break
            except Exception as ex:  # transport failure AFTER dispatch:
                # the attempt was counted (consume happened before the
                # request left the proxy); surface as 502 with reason
                data = json.dumps(
                    {"error": "upstream_transport",
                     "why": repr(ex)[:200],
                     "attempts_counted": attempts}).encode()
                code = 502
                break
        body = data if isinstance(data, bytes) else data.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Budget-Calls", str(_count))
        self.send_header("X-Budget-Remaining", str(remaining()))
        self.end_headers()
        self.wfile.write(body)


def main():
    _load_count()
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PROXY_PORT), Handler)
    print(f"ark_proxy: 127.0.0.1:{PROXY_PORT} -> proposer API | "
          f"budget {_count}/{BUDGET_LIMIT} (restored)", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
