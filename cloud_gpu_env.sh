#!/bin/bash
# kill duplicate old supervisors (keep newest pair), then GPU task env
OLD=$(pgrep -f "flyloop.supervisor" | sort -n | head -2)
for p in $OLD; do kill -9 $p 2>/dev/null; done
sleep 1
pgrep -af "flyloop.supervisor|run_overnight" | head -4
echo "=== GPU env probe"
/root/miniconda3/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
ls /root/miniconda3/lib/python3*/site-packages/ 2>/dev/null | grep -iE "^(transformers|trl|datasets|accelerate)" | head -5
echo GPUENV_PROBED
