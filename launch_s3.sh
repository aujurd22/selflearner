#!/bin/bash
# M6 seed3 (third realization, dense world) on the local Windows box
cd /d/djr82/flyloop
export FLYLOOP_COMPOSITE=1 FLYLOOP_BOOK_CAP=2 FLYLOOP_NOISE_EPS=0.25
export FLYLOOP_MATCH_MIN_FRAC=0.6 FLYLOOP_PREDSET=V4 FLYLOOP_ARMS=FULL-RES
export FLYLOOP_MAX_CYCLES=30000 FLYLOOP_RUNSEED=20261007
export FLYLOOP_PROBE_CADENCE=2
export FLYLOOP_PROBE_WEIGHTS="0.30,0.30,0.20,0.15,0.05"
rm -rf runs/m6b_base_s3 runs/m6b_delta_s3
python -m flyloop.supervisor \
  --run-dir runs/m6b_base_s3 --duration-h 8.0 \
  > m6b_base_s3.log 2>&1 < /dev/null &
python -m flyloop.supervisor \
  --run-dir runs/m6b_delta_s3 --duration-h 8.0 FLYLOOP_DELTA_RETRIEVE=1 \
  > m6b_delta_s3.log 2>&1 < /dev/null &
sleep 5
echo LAUNCHED_S3
