#!/bin/bash
# relaunch M6b after the real worker.py fix landed (02:36)
pkill -9 -f "flyloop.supervisor" 2>/dev/null
sleep 2
rm -rf /root/autodl-tmp/flyloop/runs/m6b_base_s2 /root/autodl-tmp/flyloop/runs/m6b_delta_s2
rm -f /root/autodl-tmp/flyloop/m6b_base_s2.log /root/autodl-tmp/flyloop/m6b_delta_s2.log
export FLYLOOP_COMPOSITE=1 FLYLOOP_BOOK_CAP=2 FLYLOOP_NOISE_EPS=0.25
export FLYLOOP_MATCH_MIN_FRAC=0.6 FLYLOOP_PREDSET=V4 FLYLOOP_ARMS=FULL-RES
export FLYLOOP_MAX_CYCLES=30000 FLYLOOP_RUNSEED=20261006
export FLYLOOP_PROBE_CADENCE=2
export FLYLOOP_PROBE_WEIGHTS="0.30,0.30,0.20,0.15,0.05"
export PY=/root/miniconda3/bin/python

cd /root/autodl-tmp/flyloop
env FLYLOOP_PORTS=53301,53302,53303,53304 setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6b_base_s2 --duration-h 8.0 \
  > m6b_base_s2.log 2>&1 < /dev/null &
env FLYLOOP_PORTS=53311,53312,53313,53314 FLYLOOP_DELTA_RETRIEVE=1 \
  setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6b_delta_s2 --duration-h 8.0 \
  > m6b_delta_s2.log 2>&1 < /dev/null &

sleep 150
echo "=== base"; tail -3 runs/m6b_base_s2/worker.log 2>/dev/null
echo "=== delta"; tail -3 runs/m6b_delta_s2/worker.log 2>/dev/null
echo "=== procs"; pgrep -f "flyloop.supervisor" | wc -l
echo M6B_RELAUNCHED2
