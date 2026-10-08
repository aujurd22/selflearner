#!/bin/bash
# SL restart with the semantic-leg fix (SELFLEARNER_SEMANTIC=0)
pkill -9 -f run_overnight 2>/dev/null
sleep 2
cd /root/autodl-tmp/selflearner/code
rm -f overnight_cloud_console.log
rm -f runs/overnight_*/log_cloud.jsonl
export ARK_API_KEY=$(cat /root/.intuition/ark_key)
export OVERNIGHT_TAG=_cloud
export SELFLEARNER_SEMANTIC=0
export PATH=/root/.elan/bin:$PATH
setsid nohup /root/miniconda3/bin/python run_overnight.py run 60 low \
  > overnight_cloud_console.log 2>&1 < /dev/null &
sleep 100
tail -3 overnight_cloud_console.log
pgrep -f run_overnight | wc -l
echo SL_V3_RESTARTED
