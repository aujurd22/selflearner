#!/bin/bash
echo "=== M6 base"; tail -3 /root/autodl-tmp/flyloop/m6_m5_base_s2.log 2>/dev/null
echo "=== M6 delta"; tail -2 /root/autodl-tmp/flyloop/m6_delta_s2.log 2>/dev/null
echo "=== SL console"; tail -3 /root/autodl-tmp/selflearner/code/overnight_cloud_console.log 2>/dev/null
echo "=== M6 worker err"; tail -4 /root/autodl-tmp/flyloop/runs/m6_m5_base_s2/worker.log 2>/dev/null
echo "=== SL worker err"; tail -4 /root/autodl-tmp/selflearner/code/runs/overnight_20261005/worker.log 2>/dev/null
echo "=== procs"; pgrep -af "flyloop.supervisor|run_overnight" | head -5
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
