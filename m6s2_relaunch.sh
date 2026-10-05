#!/bin/bash
# sync fixed flyloop files, kill all, relaunch M6 s2 only
cd /root/autodl-tmp/flyloop
git fetch origin -q 2>/dev/null || cp /root/autodl-tmp/awake_guard_new.py flyloop/awake_guard.py
git reset --hard origin/main -q 2>/dev/null
pkill -9 -f flyloop.supervisor 2>/dev/null
sleep 2
export FLYLOOP_COMPOSITE=1 FLYLOOP_BOOK_CAP=2 FLYLOOP_NOISE_EPS=0.25
export FLYLOOP_MATCH_MIN_FRAC=0.6 FLYLOOP_PREDSET=V4 FLYLOOP_ARMS=FULL-RES
export FLYLOOP_MAX_CYCLES=30000 FLYLOOP_RUNSEED=20261006
export PY=/root/miniconda3/bin/python
rm -rf runs/m6_m5_base_s2 runs/m6_delta_s2
env FLYLOOP_PORTS=53241,53242,53243,53244 setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6_m5_base_s2 --duration-h 8.0 \
  > m6_m5_base_s2.log 2>&1 < /dev/null &
env FLYLOOP_PORTS=53251,53252,53253,53254 FLYLOOP_DELTA_RETRIEVE=1 \
  setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6_delta_s2 --duration-h 8.0 \
  > m6_delta_s2.log 2>&1 < /dev/null &
sleep 90
echo "=== base"; tail -2 runs/m6_m5_base_s2/worker.log 2>/dev/null | head -2
echo "=== delta"; tail -2 runs/m6_delta_s2/worker.log 2>/dev/null | head -2
echo "=== procs"; pgrep -f flyloop.supervisor | wc -l
echo M6S2_RELAUNCHED
