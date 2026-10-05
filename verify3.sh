#!/bin/bash
cd /root/autodl-tmp/mathlib4
export PATH=/root/.elan/bin:$PATH
for f in C1 C2 C3; do
  cp /root/autodl-tmp/mbn/llm/selflearner_candidates/$f.lean ./$f.lean
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  grep -c "error" ${f}_out.txt 2>/dev/null || echo 0
done
echo VERIFY3_DONE
