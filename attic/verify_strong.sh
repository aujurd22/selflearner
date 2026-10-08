#!/bin/bash
# verify strong candidates D1-D4 (absolute lake path, no PATH export)
cd /root/mbn/llm/strong_cands
LAKE=/root/.elan/bin/lake
for f in D1 D2 D3 D4; do
  [ -f $f.lean ] || continue
  timeout 280 $LAKE env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  grep -c "error" ${f}_out.txt 2>/dev/null || echo 0
  grep "error" ${f}_out.txt 2>/dev/null | head -1
done
echo STRONG_VERIFY_DONE
