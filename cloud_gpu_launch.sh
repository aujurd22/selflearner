#!/bin/bash
# launch GPT2-arm exposure curve on the 5090
cd /root/autodl-tmp/mbn/llm
mv /root/autodl-tmp/mbn/data/tokens.bin /root/autodl-tmp/mbn/data/tokens.bin.staged 2>/dev/null
mkdir -p data
mv /root/autodl-tmp/mbn/data/tokens.bin.staged data/tokens.bin 2>/dev/null
cp /root/autodl-tmp/mbn/data/train_lm.py /root/autodl-tmp/mbn/llm/train_lm.py 2>/dev/null
ls -la data/tokens.bin
export PY=/root/miniconda3/bin/python
setsid nohup $PY exposure_gpt2.py > exposure_gpt2.log 2>&1 < /dev/null &
sleep 120
tail -6 exposure_gpt2.log
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
echo GPT2_ARM_LAUNCHED
