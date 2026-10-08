"""Aristotle proposer adapter for selflearner (M7.8 strong-proposer arm).

Drop-in: exposes the same ask_effort(prompt, ...) signature the loop
expects, but routes the proposal to Harmonic's Aristotle API and hands
back the Lean source of the produced project.

Flow (per proposal):
  1. `aristotle submit <prompt>` -- creates a project, cloud proves.
  2. poll `aristotle show <project>` until Task complete.
  3. `aristotle download <project>` + extract Main.lean text.
  4. Return the Main.lean source; the loop's existing check_candidate()
     (Lean compile + axiom gate) treats it like any candidate.

Cost/quota note: each proposal consumes Aristotle quota. Use a small
round budget (the arm is for the strong-proposer comparison, not for
bulk growth). Set ARISTOTLE_BUDGET to cap projects per run.

Usage (from selflearner root):
  export ARISTOTLE_API_KEY=arstl_...
  python run_overnight.py run 0 low            # with SELFLEARNER_PROPOSER=aristotle
or directly:
  python aris_proposer.py "state a small lemma about Nat.add_comm"
"""
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

KEY = os.environ.get("ARISTOTLE_API_KEY", "")
BUDGET = int(os.environ.get("ARISTOTLE_BUDGET", "10"))
_WORK = os.path.join(tempfile.gettempdir(), "aris_projects")
os.makedirs(_WORK, exist_ok=True)
_projects_made = 0


def _cli(args, timeout=120):
    env = dict(os.environ, ARISTOTLE_API_KEY=KEY)
    r = subprocess.run(["aristotle", *args], capture_output=True,
                       text=True, timeout=timeout, env=env)
    return r.stdout + r.stderr


def ask_effort(prompt, effort="low", temperature=0.4, max_tokens=8192):
    """Same signature as propose_check.ask_effort. Returns Lean source
    of Aristotle's produced project (or "" on failure)."""
    global _projects_made
    if _projects_made >= BUDGET:
        print("[aris] project budget exhausted", flush=True)
        return ""
    _projects_made += 1
    try:
        out = _cli(["submit", prompt], timeout=120)
        m = re.search(r"Project created: ([0-9a-f-]{36})", out)
        if not m:
            print(f"[aris] no project id in: {out[:120]}", flush=True)
            return ""
        pid = m.group(1)
    except Exception as ex:
        print(f"[aris] submit failed: {ex!r}"[:140], flush=True)
        return ""
    # poll until complete (Aristotle cloud proving: 5-30 min typical)
    for _ in range(60):
        time.sleep(30)
        try:
            status = _cli(["tasks", pid], timeout=60)
        except Exception:
            continue
        if re.search(r"\b(CANCELLED|FAILED|COMPLETED)\b", status):
            break
        if "IN_PROGRESS" in status:
            continue
    try:
        _cli(["download", pid], timeout=300, )
    except Exception as ex:
        print(f"[aris] download failed: {ex!r}"[:140], flush=True)
        return ""
    # find the tarball downloaded into cwd
    import glob
    tars = sorted(glob.glob(f"{pid}*.tar.gz") + glob.glob("*" + pid[:8] + "*.tar.gz"))
    if not tars:
        return ""
    t = tars[0]
    with tempfile.TemporaryDirectory() as td:
        with tarfile.open(t) as tf:
            tf.extractall(td)
        mains = []
        for root, _dirs, files in os.walk(td):
            for f in files:
                if f.endswith(".lean"):
                    mains.append(os.path.join(root, f))
        if not mains:
            return ""
        # biggest .lean = most likely the produced proof file
        main = max(mains, key=lambda p: os.path.getsize(p))
        return open(main, encoding="utf-8").read()
    return ""


if __name__ == "__main__":
    if not KEY:
        print("set ARISTOTLE_API_KEY")
        sys.exit(1)
    prompt = sys.argv[1] if len(sys.argv) > 1 else \
        "State and prove a small lemma about natural number addition " \
        "that is not literally already named in mathlib."
    src = ask_effort(prompt)
    print(src[:2000] if src else "(empty)")
