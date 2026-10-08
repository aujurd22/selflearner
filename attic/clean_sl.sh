#!/bin/bash
# cleanup orphan sandboxes + verify lean toolchain + restart SL clean
pkill -9 -f mcp_v3.py 2>/dev/null
ls /root/.elan/toolchains/ 2>/dev/null
export PATH=/root/.elan/bin:$PATH
lake --version 2>&1 | head -1
rm -f /root/autodl-tmp/selflearner/code/overnight_cloud_console.log
rm -f /root/autodl-tmp/selflearner/code/runs/overnight_*/log_cloud.jsonl
cd /root/autodl-tmp/selflearner/code
export ARK_API_KEY=$(cat /root/.intuition/ark_key)
export OVERNIGHT_TAG=_cloud
setsid nohup /root/miniconda3/bin/python run_overnight.py run 60 low \
  > overnight_cloud_console.log 2>&1 < /dev/null &
sleep 120
tail -3 overnight_cloud_console.log
echo CLEAN_SL_DONE
