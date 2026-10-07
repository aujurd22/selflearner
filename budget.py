"""Transport-layer proposer-call budget (rsi/verified-lemma-growth).

Every outbound proposer dispatch attempt decrements the declared
budget. Counting lives HERE -- below the loop, above the socket -- so
both propose_check.ask_effort (its own urllib loop) and llm_client.ask
share one counter no matter which driver the agent uses.

Rules implemented (proposal.md, Fixed evaluation protocol):
  - one unit per dispatch attempt: 429/backoff retries and transport
    failures after the request was dispatched consume budget;
  - resume-safe: the cumulative count persists in a JSON state file,
    so restarting the runner does NOT reset the counter;
  - exhausted: consume() raises BudgetExhausted BEFORE dispatch.

Editing or deleting this module (or its state file) voids the
snapshot (instruction.md, Rules).
"""
import json
import os
import tempfile


class BudgetExhausted(RuntimeError):
    """Raised before dispatch when the declared budget is spent."""


_state_path = None
_count = 0
_limit = 0


def init(path, limit):
    """Bind the counter to a persistent state file and a call limit.

    Must be called by the runner before any dispatch. If the state file
    exists (resume), the cumulative count is restored, not reset."""
    global _state_path, _count, _limit
    _limit = int(limit)
    _state_path = path
    _count = 0
    if path and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                _count = int(json.load(f).get("calls", 0))
        except (ValueError, OSError):
            _count = 0


def count():
    return _count


def remaining():
    return max(0, _limit - _count) if _limit else None


def consume():
    """Count one dispatch attempt; raise BudgetExhausted at the cap.

    Call sites invoke this immediately before urllib.urlopen, so every
    attempt that leaves the runner (including 429 retries) is counted."""
    global _count
    if _limit and _count >= _limit:
        raise BudgetExhausted(f"proposer call budget {_limit} exhausted")
    _count += 1
    _persist()


def _persist():
    if not _state_path:
        return
    try:
        d = os.path.dirname(_state_path)
        if d:
            os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"calls": _count, "limit": _limit}, f)
        os.replace(tmp, _state_path)
    except OSError:
        pass
