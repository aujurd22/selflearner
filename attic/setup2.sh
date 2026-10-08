#!/bin/bash
# setup2: extract sandbox_mem + verify lean toolchain + relaunch all three
set -x
cd /root/autodl-tmp/flyloop
tar -xzf /root/autodl-tmp/sandbox_mem.tar.gz
ls sandbox_mem/ | head -3
export PATH=/root/.elan/bin:$PATH
which lake
lake --version 2>&1 | head -1

export FLYLOOP_COMPOSITE=1 FLYLOOP_BOOK_CAP=2 FLYLOOP_NOISE_EPS=0.25
export FLYLOOP_MATCH_MIN_FRAC=0.6 FLYLOOP_PREDSET=V4 FLYLOOP_ARMS=FULL-RES
export FLYLOOP_MAX_CYCLES=30000 FLYLOOP_RUNSEED=20261006
export PY=/root/miniconda3/bin/python

env FLYLOOP_PORTS=53241,53242,53243,53244 setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6_m5_base_s2 --duration-h 8.0 \
  > m6_m5_base_s2.log 2>&1 < /dev/null &
env FLYLOOP_PORTS=53251,53252,53253,53254 FLYLOOP_DELTA_RETRIEVE=1 \
  setsid nohup $PY -m flyloop.supervisor \
  --run-dir runs/m6_delta_s2 --duration-h 8.0 \
  > m6_delta_s2.log 2>&1 < /dev/null &

cd /root/autodl-tmp/selflearner/code
export ARK_API_KEY=$(cat /root/.intuition/ark_key)
export OVERNIGHT_TAG=_cloud
export PATH=/root/.elan/bin:$PATH
setsid nohup $PY run_overnight.py run 60 low \
  > overnight_cloud_console.log 2>&1 < /dev/null &

sleep 75
echo "=== M6 s2 base"; tail -2 /root/autodl-tmp/flyloop/m6_m5_base_s2.log
echo "=== M6 s2 delta"; tail -2 /root/autodl-tmp/flyloop/m6_delta_s2.log
echo "=== selflearner"; tail -3 /root/autodl-tmp/selflearner/code/overnight_cloud_console.log
echo ALL_STARTED
