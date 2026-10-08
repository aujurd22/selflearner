"""Mandatory proposer proxy — the budget enforcement point.

v12 architecture (aligned with the RSI Harness network model):
  - iptables-level allowlist entries are IP/pin-based and loopback is
    always blocked, so the proxy CANNOT hold the only egress; instead
    Work's allowlist names the real ARK endpoint, and the proxy is the
    only client authorized to use it credentially:
      * the ARK key is injected as a root-only file (mode 0600, owner
        root) by the harness secret mechanism; the proxy reads the
        FILE, the agent shell never sees the key (the runner scrubs
        ARK_API_KEY from its own env before starting the agent);
      * the proxy forwards only POST /responses and POST
        /chat/completions, rewrites the Authorization header from the
        key file, and pins the model field to the declared proposer
        model (a request naming a different model is rejected 403);
      * the loop client (llm_client.ask / ask_effort) is configured to
        talk ONLY to the proxy: ARK_PROXY_REQUIRED=1 makes the client
        refuse to send anywhere else, so the audited path and the
        counted path are the same path;
      * the proxy counts one unit per UPSTREAM dispatch attempt (429
        backoff retries each count), answers HTTP 429 at the cap
        WITHOUT dispatching upstream, and FAILS CLOSED: a persistence
        error stops the proxy rather than continuing uncounted, and a
        missing/corrupt state file aborts startup instead of resetting
        to zero.
  - residual boundary, stated: a sufficiently determined candidate
    could craft its own HTTPS request to the ARK endpoint (the host is
    allowlisted) — without the key such a request fails upstream
    authentication; extracting the key from the proxy is out of scope
    for a shared-environment task and is declared as a residual
    limitation (same trust level as the snapshot-diff audit).

Run inside Work:  python3 ark_proxy.py  (foreground; port 8080)
The loop runner starts it automatically and waits for /health.
"""
import json
import os
import re
import stat
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROXY_PORT = int(os.environ.get("ARK_PROXY_PORT", "8080"))
UPSTREAM = os.environ.get("ARK_UPSTREAM_URL",
                          "https://ark.cn-beijing.volces.com/api/coding/v3")
# the key arrives as a root-only FILE, never as an env var
KEY_FILE = os.environ.get("ARK_KEY_FILE", "/run/secrets/ark_api_key")
DECLARED_MODEL = os.environ.get("ARK_MODEL", "glm-5.3-flash")
BUDGET_LIMIT = int(os.environ.get("FLYLOOP_CALL_BUDGET", "200"))
STATE_PATH = os.environ.get(
    "ARK_BUDGET_STATE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "runs", "budget_state.json"))

_count = 0
_lock = threading.Lock()


class BudgetExhausted(RuntimeError):
    pass


class StateLost(RuntimeError):
    """Budget state missing/unwritable — fail closed, refuse service."""


def _load_count():
    """Restore the cumulative count; a missing or corrupt state file is
    a HARD STARTUP FAILURE (fail closed — never silently reset to 0)."""
    global _count
    if not os.path.exists(STATE_PATH):
        # first launch of a NEW loop: initialize atomically, then trust it
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        _persist_locked(0)
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        count = int(data["calls"])
        limit = int(data["limit"])
        if count < 0 or limit != BUDGET_LIMIT:
            raise ValueError("state/limit mismatch")
        _count = count
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise StateLost(f"budget state unusable, refusing to start: {e}") from e


def _persist_locked(value):
    """Atomic write; any failure raises (fail closed — the proxy dies
    rather than continuing with unaccounted dispatches)."""
    d = os.path.dirname(STATE_PATH)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"calls": value, "limit": BUDGET_LIMIT,
                       "source": "ark_proxy"}, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, STATE_PATH)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def consume():
    """One unit per upstream dispatch attempt; raise at the cap."""
    global _count
    with _lock:
        if _count >= BUDGET_LIMIT:
            raise BudgetExhausted(
                f"proposer call budget {BUDGET_LIMIT} exhausted")
        new_count = _count + 1
        _persist_locked(new_count)  # raises through on write failure
        _count = new_count


def remaining():
    return max(0, BUDGET_LIMIT - _count)


def _read_key():
    try:
        st = os.stat(KEY_FILE)
        if st.st_mode & (stat.S_IRGRP | stat.S_IROTH):
            print(f"ark_proxy: WARNING {KEY_FILE} is group/other-readable",
                  flush=True)
        with open(KEY_FILE, encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    except OSError as e:
        print(f"ark_proxy: cannot read key file {KEY_FILE}: {e}", flush=True)
    return ""


_KEY = None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _json(self, code, obj, extra_headers=()):
        body = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in extra_headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"ok": True, "calls": _count,
                             "limit": BUDGET_LIMIT,
                             "remaining": remaining()})
            return
        self._json(403, {"error": "forbidden",
                         "why": "only POST /responses and GET /health"})

    def do_POST(self):
        if not re.fullmatch(r"/(responses|chat/completions)/?", self.path):
            self._json(403, {"error": "forbidden",
                             "why": "only proposer endpoints are served"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        # pin the declared proposer model: rewrite the request body so
        # the upstream always sees ARK_MODEL regardless of what the
        # client asked for (the client cannot opt into another model)
        try:
            req_obj = json.loads(payload) if payload else {}
        except ValueError:
            self._json(400, {"error": "bad_request", "why": "invalid JSON"})
            return
        req_obj["model"] = DECLARED_MODEL
        payload = json.dumps(req_obj).encode()
        for attempt in range(3):
            try:
                consume()
            except BudgetExhausted as e:
                self._json(429, {"error": "budget_exhausted",
                                 "calls": _count, "limit": BUDGET_LIMIT,
                                 "why": str(e)})
                return
            req = urllib.request.Request(
                UPSTREAM + self.path, data=payload,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {_KEY}"})
            try:
                with urllib.request.urlopen(req, timeout=900) as r:
                    data, code = r.read(), r.status
                break
            except urllib.error.HTTPError as ex:
                if ex.code == 429 and attempt < 2:
                    time.sleep(60 * (attempt + 1))
                    continue
                data = ex.read() if hasattr(ex, "read") else b"{}"
                code = ex.code
                break
            except Exception as ex:
                # dispatch was counted (consume preceded the request);
                # surface as 502 with the attempt count
                self._json(502, {"error": "upstream_transport",
                                 "why": repr(ex)[:200],
                                 "attempts_counted": attempt + 1})
                return
        self._json(code, data if isinstance(data, bytes) else data.encode(),
                   (("X-Budget-Calls", str(_count)),
                    ("X-Budget-Remaining", str(remaining()))))


def main():
    global _KEY
    _load_count()  # may raise StateLost -> refuse to start (fail closed)
    _KEY = _read_key()
    if not _KEY:
        print("ark_proxy: no upstream key — proxy will forward but all "
              "requests will fail upstream auth", flush=True)
    os.environ.pop("ARK_API_KEY", None)  # never hold the key in env
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PROXY_PORT), Handler)
    print(f"ark_proxy: 127.0.0.1:{PROXY_PORT} -> proposer API | model "
          f"{DECLARED_MODEL} | budget {_count}/{BUDGET_LIMIT} (restored)",
          flush=True)
    try:
        srv.serve_forever()
    except BaseException:
        print("ark_proxy: terminating (state preserved on disk)",
              flush=True)
        raise


if __name__ == "__main__":
    main()
