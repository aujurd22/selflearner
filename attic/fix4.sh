#!/bin/bash
pkill -9 -f exposure_spacing 2>/dev/null
sleep 1
cd /root/autodl-tmp/mbn/llm
cp /root/autodl-tmp/mbn/data/train_lm.py ./train_lm.py 2>/dev/null
ls -la train_lm.py
rm -rf __pycache__ runs/exp_exp_spaced32 runs/exp_spaced32 runs/exp_massed32 runs/exp_massed64 runs/exp_massed16
rm -f exposure_spacing.log
setsid nohup /root/miniconda3/bin/python exposure_spacing.py \
  > exposure_spacing.log 2>&1 < /dev/null &
sleep 180
echo "=== log"; tail -5 exposure_spacing.log
echo "=== train proc"; pgrep -af "train_lm" | grep -v grep | head -2
ls runs/ | head -6
echo SPACING_RETRY_DONE
