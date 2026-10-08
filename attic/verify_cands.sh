#!/bin/bash
# verify candidates INSIDE the mathlib4 project dir (lake needs lakefile)
cd /root/autodl-tmp/mathlib4
LAKE=/root/.elan/bin/lake
for f in C1 C2 C3 C4; do
  cp /root/mbn/llm/selflearner_candidates/$f.lean ./$f.lean
  timeout 280 $LAKE env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  head -3 ${f}_out.txt
done
rm -f ./C1.lean ./C2.lean ./C3.lean ./C4.lean ./C?_out.txt
echo VERIFY_DONE
