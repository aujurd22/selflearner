#!/bin/bash
# five-way liveness sweep
echo "=== cloud M6 s2 base"; tail -1 /root/autodl-tmp/flyloop/runs/m6_m5_base_s2/STATUS.md 2>/dev/null | head -c 120; echo
echo "=== cloud M6 s2 delta"; tail -1 /root/autodl-tmp/flyloop/runs/m6_delta_s2/STATUS.md 2>/dev/null | head -c 120; echo
echo "=== cloud SL"; tail -2 /root/autodl-tmp/selflearner/code/overnight_cloud_console.log 2>/dev/null
echo "=== cloud spacing"; tail -2 /root/autodl-tmp/mbn/llm/exposure_spacing.log 2>/dev/null
echo "=== local M6"; tail -1 /mnt/d/djr82/flyloop/m6_m6_m5_base_console.log 2>/dev/null | head -c 120; echo
echo "=== local mamba spacing"; tail -2 /root/mbn/llm/exposure_spacing_mamba.log 2>/dev/null
echo "=== GPUs"; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null
