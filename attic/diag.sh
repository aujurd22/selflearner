#!/bin/bash
pkill -9 -f run_overnight 2>/dev/null
sleep 1
rm -f /root/autodl-tmp/selflearner/code/runs/overnight_*/log_cloud.jsonl
cd /root/autodl-tmp/flyloop
grep -E "Error|error|Traceback" -A 3 runs/m6_m5_base_s2.log | tail -8
echo "=== worker.log tail"
tail -6 runs/m6_m5_base_s2/worker.log 2>/dev/null
