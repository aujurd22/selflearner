#!/bin/bash
# single-file verify: round1_h on native FS
export PATH=/root/.elan/bin:$PATH
cd /root/mbn/llm/mathlib4
timeout 280 lake env lean /root/mbn/llm/axioms_check/round1_h.lean > r1h_ax.txt 2>&1
echo "exit=$?"
grep "axioms" r1h_ax.txt | head -1
grep -c error r1h_ax.txt
