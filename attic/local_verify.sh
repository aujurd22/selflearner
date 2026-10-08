#!/bin/bash
# verify D1/D2/C2 locally
cd /root/mbn/llm/strong_cands
export PATH=/root/.elan/bin:$PATH
for f in D1 D2 C2; do
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  grep -c "error" ${f}_out.txt || echo 0
done
echo LOCAL_VERIFY_DONE
