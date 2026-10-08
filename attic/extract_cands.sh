#!/bin/bash
# extract 18 admitted candidates from log_cloud.jsonl -> .lean files -> axiom check
cd /root/mbn/llm
mkdir -p axioms_check
python3 - <<'PYEOF'
import json
import os

out = "/root/mbn/llm/axioms_check"
os.makedirs(out, exist_ok=True)
n = 0
for line in open("/mnt/d/djr82/selflearner/runs/log_cloud.jsonl", encoding="utf-8"):
    try:
        rec = json.loads(line)
    except Exception:
        continue
    if not rec.get("ok"):
        continue
    n += 1
    name = rec.get("name") or f"anon_{n}"
    code = rec.get("code", "")
    with open(f"{out}/{name}.lean", "w", encoding="utf-8") as f:
        f.write(code)
print(f"extracted {n} candidates")
PYEOF
ls axioms_check/ | head -5
echo EXTRACT_DONE
