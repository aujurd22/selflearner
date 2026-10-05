#!/bin/bash
# M6b launch (dense-PERIODIC world): base vs delta, RUNSEED=20261006
pkill -9 -f flyloop.supervisor 2>/dev/null
sleep 2
cd /root/autodl-tmp/flyloop
rm -rf runs/m6b_base_s2 runs/m6b_delta_s2
export FLYLOOP_COMPOSITE=1 FLYLOOP_BOOK_CAP=2 FLYLOOP_NOISE_EPS=0.25
export FLYLOOP_MATCH_MIN_FRAC=0.6 FLYLOOP_PREDSET=V4 FLYLOOP_ARMS=FULL-RES
export FLYLOOP_MAX_CYCLES=30000 FLYLOOP_RUNSEED=20261006
export FLYLOOP_PROBE_CADENCE=2
export FLYLOOP_PROBE_WEIGHTS="0.30,0.30,0.20,0.15,0.05"
export PY=/root/miniconda3/bin/python

env FLYLOOP_PORTS=53261,53262,53263,53264 setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6b_base_s2 --duration-h 8.0 \
  > m6b_base_s2.log 2>&1 < /dev/null &
env FLYLOOP_PORTS=53271,53272,53273,53274 FLYLOOP_DELTA_RETRIEVE=1 \
  setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6b_delta_s2 --duration-h 8.0 \
  > m6b_delta_s2.log 2>&1 < /dev/null &

sleep 90
echo "=== base"; tail -2 runs/m6b_base_s2/worker.log 2>/dev/null
echo "=== delta"; tail -2 runs/m6b_delta_s2/worker.log 2>/dev/null
echo "=== procs"; pgrep -f flyloop.supervisor | wc -l
echo M6B_LAUNCHED
