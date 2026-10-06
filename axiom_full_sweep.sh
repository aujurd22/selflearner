#!/bin/bash
# full axiom sweep: all 6 unique SL candidates (gated v3 arm) with report
cd /root/mbn/llm/mathlib4
export PATH=/root/.elan/bin:$PATH
PASS=0; FAIL=0
> /root/mbn/llm/axioms_full_report.txt
for f in nhds_self round1 round1_h selflearner_lemma sub_one_add_one zpowers_zpow_sup_eq_zpowers; do
  timeout 280 lake env lean /root/mbn/llm/axioms_check/$f.lean > /tmp/ax_$f.txt 2>&1
  rc=$?
  ax=$(grep "depends on axioms" /tmp/ax_$f.txt | head -1)
  echo "== $f exit=$rc | $ax" >> /root/mbn/llm/axioms_full_report.txt
  if [ $rc -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); grep "error" /tmp/ax_$f.txt | head -2 >> /root/mbn/llm/axioms_full_report.txt; fi
done
echo "FULL_SWEEP: pass=$PASS fail=$FAIL" >> /root/mbn/llm/axioms_full_report.txt
cat /root/mbn/llm/axioms_full_report.txt
