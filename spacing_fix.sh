#!/bin/bash
pkill -9 -f exposure_spacing 2>/dev/null
pkill -9 -f "train_lm.py --arch gpt2" 2>/dev/null
sleep 2
pgrep -af "exposure_spacing|train_lm" | grep -v grep | head -3
rm -rf /root/autodl-tmp/mbn/llm/runs/exp_exp_spaced32 /root/autodl-tmp/mbn/llm/runs/exp_spaced32
rm -f /root/autodl-tmp/mbn/llm/exposure_spacing.log
grep -c "exp_exp" /root/autodl-tmp/mbn/llm/exposure_spacing.py
cd /root/autodl-tmp/mbn/llm
setsid nohup /root/miniconda3/bin/python exposure_spacing.py > /root/autodl-tmp/mbn/llm/exposure_spacing.log 2>&1 < /dev/null &
sleep 120
echo "=== log"; tail -4 /root/autodl-tmp/mbn/llm/exposure_spacing.log
echo "=== procs"; pgrep -f exposure_spacing.py | wc -l
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
echo CLEAN_START_DONE
