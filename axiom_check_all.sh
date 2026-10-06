#!/bin/bash
# axiom check all 18 candidates inside mathlib4 project (WSL, /mnt/d)
cd /mnt/d/djr82/selflearner/mathlib4
cp /root/mbn/llm/axioms_check/*.lean . 2>/dev/null
export PATH=/root/.elan/bin:$PATH
PASS=0; FAIL=0
for f in *.lean; do
  case "$f" in C1*|C2*|C3*|C4*|D1*|D2*) continue;; esac
  timeout 280 lake env lean "$f" > axiom_out.txt 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); echo "== $f exit=$rc"; head -2 axiom_out.txt; fi
done
echo "AXIOM_CHECK: pass=$PASS fail=$FAIL"
rm -f ./*.lean.axiom_out.txt
