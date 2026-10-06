#!/bin/bash
# copy mathlib4 to WSL-native FS (fast IO) + reverify the 3 timed-out
cp -r /mnt/d/djr82/selflearner/mathlib4 /root/mbn/llm/mathlib4 2>/dev/null
cd /root/mbn/llm/mathlib4
export PATH=/root/.elan/bin:$PATH
PASS=0; FAIL=0
for f in round1_h nhds_self sub_one_add_one; do
  timeout 280 lake env lean /root/mbn/llm/axioms_check/$f.lean > ${f}_axout.txt 2>&1
  rc=$?
  ax=$(grep "depends on axioms" ${f}_axout.txt | head -1)
  echo "== $f exit=$rc | $ax"
  if [ $rc -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); grep "error" ${f}_axout.txt | head -1; fi
done
echo "NATIVE_REVERIFY: pass=$PASS fail=$FAIL"
