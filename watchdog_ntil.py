"""Watchdog: monitor NTIL long run + ARC matrix tail.

Checks every 10 minutes. If the run finishes, crashes, or stalls
(no new rows for 20 minutes), prints a summary and exits.
"""
import json
import os
import sys
import time

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "runs", "overnight_20261010", "log_ntil.jsonl")
STALL_MIN = 20
CHECK_EVERY = 600  # seconds

last_size = 0
last_change = time.time()

while True:
    time.sleep(CHECK_EVERY)
    try:
        size = os.path.getsize(LOG) if os.path.exists(LOG) else 0
    except OSError:
        print(f"[{time.strftime('%H:%M:%S')}] log not found yet", flush=True)
        continue

    if size != last_size:
        last_size = size
        last_change = time.time()

    # count rounds
    rounds = 0
    admitted = 0
    max_dispatch = 0
    try:
        raw = open(LOG, "rb").read().replace(b"\x00", b"")
        for line in raw.decode("utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("rnd"):
                rounds += 1
                max_dispatch = max(max_dispatch, r.get("calls_after", 0))
                if r.get("ok"):
                    admitted += 1
    except Exception:
        pass

    stall_min = (time.time() - last_change) / 60
    print(f"[{time.strftime('%H:%M:%S')}] rounds={rounds} "
          f"admitted={admitted} dispatch={max_dispatch}/60 "
          f"stall={stall_min:.0f}m", flush=True)

    if max_dispatch >= 60:
        print("DONE: 60-dispatch budget exhausted", flush=True)
        break
    if stall_min >= STALL_MIN:
        print(f"STALL: no new log entries for {stall_min:.0f} minutes",
              flush=True)
        break
