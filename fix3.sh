#!/bin/bash
# fix3: stop all dead loops, add missing mathlib4 project files, clean logs, relaunch
pkill -9 -f run_overnight 2>/dev/null
pkill -9 -f flyloop.supervisor 2>/dev/null
pkill -9 -f exposure_spacing 2>/dev/null
pkill -9 -f "lake env lean" 2>/dev/null
sleep 2
cd /root/autodl-tmp/mathlib4
cp /root/autodl-tmp/mathlib4fix/* . 2>/dev/null
ls lakefile.lean lean-toolchain lake-manifest.json 2>/dev/null
export PATH=/root/.elan/bin:$PATH
timeout 90 lake env lean --version 2>&1 | head -1 || echo "lake probe slow-but-alive"

rm -f /root/autodl-tmp/selflearner/code/overnight_cloud_console.log
rm -f /root/autodl-tmp/selflearner/code/runs/overnight_*/log_cloud.jsonl
rm -f /root/autodl-tmp/mbn/llm/exposure_spacing.log
rm -rf /root/autodl-tmp/mbn/llm/runs/exp_exp_spaced32

export FLYLOOP_COMPOSITE=1 FLYLOOP_BOOK_CAP=2 FLYLOOP_NOISE_EPS=0.25
export FLYLOOP_MATCH_MIN_FRAC=0.6 FLYLOOP_PREDSET=V4 FLYLOOP_ARMS=FULL-RES
export FLYLOOP_MAX_CYCLES=30000 FLYLOOP_RUNSEED=20261006
export PY=/root/miniconda3/bin/python

cd /root/autodl-tmp/flyloop
rm -rf runs/m6_m5_base_s2 runs/m6_delta_s2
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

cd /root/autodl-tmp/mbn/llm
setsid nohup $PY exposure_spacing.py \
  > exposure_spacing.log 2>&1 < /dev/null &

sleep 150
echo "=== M6 base"; tail -2 /root/autodl-tmp/flyloop/runs/m6_m5_base_s2/worker.log 2>/dev/null | head -2
echo "=== M6 delta"; tail -2 /root/autodl-tmp/flyloop/runs/m6_delta_s2/worker.log 2>/dev/null | head -2
echo "=== SL"; tail -3 /root/autodl-tmp/selflearner/code/overnight_cloud_console.log
echo "=== spacing"; tail -2 /root/autodl-tmp/mbn/llm/exposure_spacing.log
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
echo FIX3_DONE
