#!/bin/bash
# verify C3/C4 in mathlib4 project dir
cd /root/autodl-tmp/mathlib4
cp /root/mbn/llm/selflearner_candidates/C3.lean /root/mbn/llm/selflearner_candidates/C4.lean .
export PATH=/root/.elan/bin:$PATH
for f in C3 C4; do
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  head -2 ${f}_out.txt
done
echo C34_DONE
