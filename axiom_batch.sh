#!/bin/bash
# batch axiom check: 6 SL candidates in mathlib4 project
cd /mnt/d/djr82/selflearner/mathlib4
cp /root/mbn/llm/axioms_check/*.lean . 2>/dev/null
export PATH=/root/.elan/bin:$PATH
PASS=0; FAIL=0
for f in nhds_self round1 round1_h selflearner_lemma sub_one_add_one zpowers_zpow_sup_eq_zpowers; do
  timeout 280 lake env lean $f.lean > axiom_out_$f.txt 2>&1
  rc=$?
  ax=$(grep "depends on axioms" axiom_out_$f.txt | head -1)
  echo "== $f exit=$rc | $ax"
  if [ $rc -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); head -2 axiom_out_$f.txt; fi
done
echo "AXIOM_BATCH: pass=$PASS fail=$FAIL"
