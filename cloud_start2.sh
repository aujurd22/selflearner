#!/bin/bash
# cloud start v2: pull latest code, launch M6 s2 arms + selflearner overnight
set -e
echo "=== [1] flyloop -> 47f8bff"
cd /root/autodl-tmp/flyloop
git fetch origin -q && git reset --hard origin/main -q
git log --oneline -1

echo "=== [2] selflearner code"
cd /root/autodl-tmp/selflearner
if [ ! -d code ]; then
  git clone -q https://github.com/aujurd22/selflearner.git code
fi
cd code && git fetch origin -q && git reset --hard origin/master -q && git log --oneline -1
# data files already live in the parent dir
for f in mathlib.db vectors.npz mathlib4; do
  ln -sfn /root/autodl-tmp/selflearner/$f /root/autodl-tmp/selflearner/code/$f
done

echo "=== [3] launch M6 s2 arms"
cd /root/autodl-tmp/flyloop
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

echo "=== [4] launch selflearner overnight (gated, 60 rounds)"
cd /root/autodl-tmp/selflearner/code
export ARK_API_KEY=$(cat /root/.intuition/ark_key)
export OVERNIGHT_TAG=_cloud
setsid nohup $PY run_overnight.py run 60 low \
  > overnight_cloud_console.log 2>&1 < /dev/null &

sleep 75
echo "=== M6 s2 base"; tail -2 /root/autodl-tmp/flyloop/m6_m5_base_s2.log
echo "=== M6 s2 delta"; tail -2 /root/autodl-tmp/flyloop/m6_delta_s2.log
echo "=== selflearner"; tail -3 /root/autodl-tmp/selflearner/code/overnight_cloud_console.log
echo ALL_STARTED
