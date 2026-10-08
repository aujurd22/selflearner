"""Shared client for the Volcano (ark.cn-beijing) Responses API.

Model: glm-5.3-flash.  API key supplied via env ARK_API_KEY or the
default from the user's console (do not commit real keys -- this
default is the user's own coding-console key, kept in the private repo).

Usage:
    from llm_client import ask
    reply = ask("prompt text")
"""
import json
import os
import time
import urllib.request

try:
    import budget  # kept for local (proxy-less) dev runs only
except ImportError:  # pragma: no cover
    budget = None

# In the rsi/verified-lemma-growth task container the proxy IS the
# endpoint: ARK_BASE_URL points at 127.0.0.1:8080 and the proxy counts
# every upstream attempt and pins the model. When ARK_PROXY_REQUIRED=1
# this client refuses to send anywhere else, so the audited path and
# the counted path are the same path.
BASE = os.environ.get("ARK_BASE_URL",
                      "https://ark.cn-beijing.volces.com/api/coding/v3")
_PROXY_REQUIRED = os.environ.get("ARK_PROXY_REQUIRED") == "1"
if _PROXY_REQUIRED and not BASE.startswith("http://127.0.0.1"):
    raise RuntimeError(
        "ARK_PROXY_REQUIRED=1 but ARK_BASE_URL is not the local proxy — "
        "refusing to send uncounted proposer traffic")


def _guarded_urlopen(req, timeout):
    """One hard gate before every send: in task mode the request MUST
    target the local proxy (the counted path)."""
    if _PROXY_REQUIRED:
        url = req.get_full_url()
        if not url.startswith("http://127.0.0.1"):
            raise RuntimeError(
                f"refusing uncounted dispatch to {url.split('/')[2]} — "
                "proposer traffic must go through the local proxy")
    return urllib.request.urlopen(req, timeout=timeout)
# Key MUST come from the environment (never committed -- GitHub Push
# Protection blocks any commit containing it, by design).
KEY = os.environ.get("ARK_API_KEY", "")
MODEL = os.environ.get("ARK_MODEL", "doubao-seed-2.1-lite")


def ask(prompt: str, temperature: float = 0.0,
        max_tokens: int = 16384) -> str:
    """Send a prompt, return the final text answer.

    GLM-5.3-flash is a reasoning model.  Verified parameter combo:
    reasoning effort=minimal keeps reasoning tokens ~200; "low" still
    burns 16k on hard prompts.  Prompts should carry an
    "Answer IMMEDIATELY" instruction for full effect.  429s get a long
    exponential backoff (the coding-console rate limit is strict).
    """
    body = json.dumps({
        "model": MODEL,
        "input": prompt,
        "temperature": temperature,
        "max_output_tokens": max_tokens,
        "reasoning": {"effort": "minimal"},
    }).encode()
    req = urllib.request.Request(
        BASE + "/responses", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {KEY}"})
    last_err = None
    for attempt in range(5):
        try:
            # P186-c lesson: a hung socket can wedge a 600s-timeout call for
            # ~50min across retries. effort=minimal answers arrive in <60s,
            # so bound each attempt at 150s (5 attempts ~13min worst case,
            # then the effort=low fallback below still gets its 900s).
            r = json.loads(_guarded_urlopen(req, 150).read())
            parts = []
            for item in r.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            parts.append(c["text"])
            return "\n".join(parts) if parts else ""
        except urllib.error.HTTPError as ex:
            last_err = ex
            if ex.code == 429:
                time.sleep(60 * (attempt + 1))
                continue
            raise
        except Exception as ex:          # timeout / transient
            last_err = ex
            time.sleep(10)
    # ALL attempts returned empty (the model burned the full reasoning
    # budget at effort=minimal): retry ONCE at effort=low, which is slow
    # (~600s) but terminates with a real answer on these prompts.
    body = json.dumps({
        "model": MODEL,
        "input": prompt,
        "temperature": temperature,
        "max_output_tokens": max_tokens,
        "reasoning": {"effort": "low"},
    }).encode()
    req = urllib.request.Request(
        BASE + "/responses", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {KEY}"})
    r = json.loads(_guarded_urlopen(req, 900).read())
    parts = []
    for item in r.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    parts.append(c["text"])
    return "\n".join(parts) if parts else ""


def ask_chat(prompt: str, temperature: float = 0.0,
             max_tokens: int = 16384) -> str:
    """chat/completions endpoint -- reasoning separated into
    reasoning_content, so the answer is always directly extracted
    (no reasoning-budget starvation)."""
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()
    # thinking.type=disabled is accepted across ark chat models (verified:
    # doubao-seed-2.1-lite AND deepseek-v4.1-flash; reasoning_chars -> 0)
    body = json.dumps({**json.loads(body),
                       "thinking": {"type": "disabled"}}).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {KEY}"})
    r = json.loads(_guarded_urlopen(req, 600).read())
    return r["choices"][0]["message"].get("content", "") or ""
