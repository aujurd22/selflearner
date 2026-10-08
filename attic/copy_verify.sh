#!/bin/bash
# copy candidates into mathlib4 + verify C1 with axiom report
cp /root/mbn/llm/axioms_check/*.lean /mnt/d/djr82/selflearner/mathlib4/
cd /mnt/d/djr82/selflearner/mathlib4
ls C1.lean anon_1791229039.lean 2>/dev/null | wc -l
export PATH=/root/.elan/bin:$PATH
timeout 280 lake env lean C1.lean > probe_out.txt 2>&1
echo "exit=$?"
grep "axioms" probe_out.txt | head -1
