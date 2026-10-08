#!/bin/bash
# materialize the BASELINE snapshot artifact: extract the 18 admitted
# lemmas from the gated SL-60 run into a standalone baseline dir
# (traceable baseline artifact — review Fix-3)
mkdir -p /root/mbn/llm/baseline_snapshot/admitted
python3 - <<'PYEOF'
import json
import os

out = "/root/mbn/llm/baseline_snapshot/admitted"
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
    with open(f"{out}/{name}.lean", "w", encoding="utf-8") as f:
        f.write(rec.get("code", ""))
diff = {"lemmas": []}
for line in open("/mnt/d/djr82/selflearner/runs/log_cloud.jsonl", encoding="utf-8"):
    try:
        rec = json.loads(line)
    except Exception:
        continue
    if rec.get("ok"):
        diff["lemmas"].append({"name": rec.get("name"),
                               "file": rec.get("file")})
with open("/root/mbn/llm/baseline_snapshot/library_diff.json", "w",
          encoding="utf-8") as f:
    json.dump(diff, f, indent=1)
print(f"baseline snapshot: {n} admitted lemmas materialized")
PYEOF
ls /root/mbn/llm/baseline_snapshot/admitted | wc -l
echo BASELINE_MATERIALIZED
