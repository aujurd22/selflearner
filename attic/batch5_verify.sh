#!/bin/bash
# batch5 FINAL: C2 nat.tri version (cloud-verified proof reused) + C3 rw-ih-ring + C4 additive ring
cd /root/mbn/llm/strong_cands

cat > C2.lean <<'LEOF'
import Mathlib.Tactic

/-- 8 times the n-th triangular number plus one is (2n+1) squared. -/
theorem sl_eight_tri_oct (n : ℕ) : 8 * Nat.tri n + 1 = (2 * n + 1) ^ 2 := by
  induction n with
  | zero => rfl
  | succ k ih => rw [Nat.tri_succ, ih]; ring
LEOF

cat > C3.lean <<'LEOF'
import Mathlib.Tactic

/-- Three times the sum of i*(i+1) for i < n+2 equals (n+1)(n+2)(n+3). -/
theorem sl_sum_i_ipl (n : ℕ) :
    3 * ∑ i ∈ Finset.range (n + 2), i * (i + 1)
      = (n + 1) * (n + 2) * (n + 3) := by
  induction n with
  | zero => norm_num [Finset.sum_range_succ]
  | succ k ih => rw [ih]; ring
LEOF

cat > C4.lean <<'LEOF'
import Mathlib.Tactic

/-- The gap between consecutive odd squares: (2n+1)^2 + 8n+8 = (2n+3)^2
(additive form — avoids truncated subtraction). -/
theorem sl_odd_sq_gap (n : ℕ) : (2 * n + 1) ^ 2 + 8 * n + 8 = (2 * n + 3) ^ 2 := by
  ring
LEOF

cd /root/mbn/llm/mathlib4
export PATH=/root/.elan/bin:$PATH
PASS=0; FAIL=0
for f in C2 C3 C4; do
  cp /root/mbn/llm/strong_cands/$f.lean ./$f.lean
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  rc=$?
  echo "== $f exit=$rc"
  if [ $rc -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); grep "error" ${f}_out.txt | head -2; fi
done
echo "BATCH5: pass=$PASS fail=$FAIL"
