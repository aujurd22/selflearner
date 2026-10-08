#!/bin/bash
# NUCLEAR: kill everything, purge pycache, single clean relaunch
pkill -9 -f flyloop 2>/dev/null
sleep 2
pgrep -f flyloop | head -3
find /root/autodl-tmp/flyloop/flyloop/__pycache__ -name "*.pyc" -delete 2>/dev/null
rm -rf /root/autodl-tmp/flyloop/runs/m6b_base_s2 /root/autodl-tmp/flyloop/runs/m6b_delta_s2
rm -f /root/autodl-tmp/flyloop/m6b_base_s2.log /root/autodl-tmp/flyloop/m6b_delta_s2.log
export FLYLOOP_COMPOSITE=1 FLYLOOP_BOOK_CAP=2 FLYLOOP_NOISE_EPS=0.25
export FLYLOOP_MATCH_MIN_FRAC=0.6 FLYLOOP_PREDSET=V4 FLYLOOP_ARMS=FULL-RES
export FLYLOOP_MAX_CYCLES=30000 FLYLOOP_RUNSEED=20261006
export FLYLOOP_PROBE_CADENCE=2
export FLYLOOP_PROBE_WEIGHTS="0.30,0.30,0.20,0.15,0.05"
export PY=/root/miniconda3/bin/python

cd /root/autodl-tmp/flyloop
env FLYLOOP_PORTS=53281,53282,53283,53284 setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6b_base_s2 --duration-h 8.0 \
  > m6b_base_s2.log 2>&1 < /dev/null &
env FLYLOOP_PORTS=53291,53292,53293,53294 FLYLOOP_DELTA_RETRIEVE=1 \
  setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6b_delta_s2 --duration-h 8.0 \
  > m6b_delta_s2.log 2>&1 < /dev/null &

sleep 120
echo "=== base worker"; tail -3 runs/m6b_base_s2/worker.log 2>/dev/null
echo "=== delta worker"; tail -3 runs/m6b_delta_s2/worker.log 2>/dev/null
echo "=== procs"; pgrep -f flyloop.supervisor | wc -l
echo NUCLEAR_DONE
