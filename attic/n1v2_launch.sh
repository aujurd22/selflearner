#!/bin/bash
# N1 v2 launch: kill stale instances, verify paths, start dual-occurrence probe
pkill -9 -f exposure_incontext 2>/dev/null
sleep 1
cd /root/autodl-tmp/mbn/llm
grep -c "s_rel_o" exposure_incontext.py
grep -c "autodl-tmp" exposure_incontext.py
setsid nohup /root/miniconda3/bin/python exposure_incontext.py gpt2 \
  > exposure_incontext_gpt2v2.log 2>&1 < /dev/null &
sleep 180
tail -5 exposure_incontext_gpt2v2.log
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
echo N1V2_STARTED
