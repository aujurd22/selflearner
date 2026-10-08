#!/bin/bash
cd /root/mbn/llm/strong_cands
sed -i '/import Mathlib.Tactic/d' D1.lean D2.lean C2.lean
export PATH=/root/.elan/bin:$PATH
for f in D1 D2 C2; do
  timeout 280 lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  grep -c "error" ${f}_out.txt || echo 0
  grep "error" ${f}_out.txt | head -1
done
echo BARE_DONE
