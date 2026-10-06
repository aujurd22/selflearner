#!/bin/bash
# batch3 FINAL: correct target dir (/root/mbn/llm/mathlib4, the complete copy)
cd /root/mbn/llm/strong_cands

cat > C2.lean <<'LEOF'
import Mathlib.Tactic

/-- 8 times the n-th triangular number plus one is (2n+1) squared. -/
theorem sl_eight_tri_oct (n : ℕ) : 8 * (∑ i ∈ Finset.range n, i) + 1 = (2 * n + 1) ^ 2 := by
  induction n with
  | zero => simp
  | succ k ih =>
    rw [Finset.sum_range_succ]
    simp
    omega
LEOF

cat > C3.lean <<'LEOF'
import Mathlib.Tactic

/-- Three times the sum of i*(i+1) for i < n+2 equals (n+1)(n+2)(n+3). -/
theorem sl_sum_i_ipl (n : ℕ) :
    3 * ∑ i ∈ Finset.range (n + 2), i * (i + 1)
      = (n + 1) * (n + 2) * (n + 3) := by
  induction n with
  | zero => norm_num [Finset.sum_range_succ]
  | succ k ih =>
    rw [Finset.sum_range_succ, Finset.mul_sum, ih]
    ring
LEOF

cat > D2.lean <<'LEOF'
import Mathlib.Tactic

/-- Sum of divisors of 2^k equals 2^(k+1) - 1. -/
theorem sl_sigma_two_pow (k : ℕ) :
    ∑ d in Nat.divisors (2 ^ k), d = 2 ^ (k + 1) - 1 := by
  induction k with
  | zero => simp [Nat.divisors_one]
  | succ n ih =>
    rw [Nat.pow_succ]
    simp [Nat.divisors_pow_succ Nat.Prime.two_gt_one]
    omega
LEOF

cat > C4.lean <<'LEOF'
import Mathlib.Tactic

/-- The gap between consecutive odd squares: (2n+3)^2 - (2n+1)^2 = 8n+8. -/
theorem sl_odd_sq_gap (n : ℕ) : (2 * n + 3) ^ 2 - (2 * n + 1) ^ 2 = 8 * n + 8 := by
  omega
LEOF

cd /root/mbn/llm/mathlib4
export PATH=/root/.elan/bin:$PATH
PASS=0; FAIL=0
for f in C2 C3 D2 C4; do
  cp /root/mbn/llm/strong_cands/$f.lean ./$f.lean
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  rc=$?
  echo "== $f exit=$rc"
  if [ $rc -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); grep "error" ${f}_out.txt | head -2; fi
done
echo "BATCH3: pass=$PASS fail=$FAIL"
