#!/bin/bash
cd /root/mbn/llm/selflearner_candidates
sed -i 's/| zero => norm_num \[Nat.tri\]/| zero => rfl/' C2.lean
sed -i 's/rw \[Finset.sum_range_succ, ih\]/rw [ih]/' C3.lean
grep -n "zero =>" C2.lean
grep -n "rw \[" C3.lean | head -2
cp C2.lean C3.lean /root/autodl-tmp/mathlib4/
export PATH=/root/.elan/bin:$PATH
for f in C2 C3; do
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  grep -c "error" ${f}_out.txt || echo 0
done
echo TACTIC_FIX2_DONE
