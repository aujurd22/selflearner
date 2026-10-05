#!/bin/bash
# fix C2/C3/C4 proofs and re-verify all
cd /root/autodl-tmp/mbn/llm/selflearner_candidates

cat > C2.lean <<'LEOF'
import Mathlib.Tactic

/-- 8 times the n-th triangular number plus one is (2n+1) squared. -/
theorem sl_eight_tri_oct (n : ℕ) : 8 * (∑ i ∈ Finset.range n, i) + 1 = (2 * n + 1) ^ 2 := by
  induction n with
  | zero => simp
  | succ k ih =>
    rw [Finset.sum_range_succ]
    simp only
    omega
LEOF

cat > C3.lean <<'LEOF'
import Mathlib.Tactic

/-- 3 * sum(i*(i+1)) plus n^3 equals n^3 + 3 * sum(i) — equivalently the
classic sum(i*(i+1)) = 2 * triangular identity in additive form. -/
theorem sl_sum_i_ipl (n : ℕ) :
    3 * (∑ i ∈ Finset.range n, i * (i + 1)) + n * n * n = n ^ 3 + 3 * (∑ i ∈ Finset.range n, i) := by
  induction n with
  | zero => simp
  | succ k ih =>
    rw [Finset.sum_range_succ]
    ring_nf
    omega
LEOF

cat > C4.lean <<'LEOF'
import Mathlib.Tactic

/-- Sum of powers of two below 2^n equals 2^n - 1 (no subtraction in the
summand; the statement uses truncated subtraction on the total). -/
theorem sl_sum_two_pow (n : ℕ) : ∑ i ∈ Finset.range n, 2 ^ i = 2 ^ n - 1 := by
  induction n with
  | zero => simp
  | succ k ih =>
    rw [Finset.sum_range_succ, ih]
    omega
LEOF

cd /root/autodl-tmp/mathlib4
export PATH=/root/.elan/bin:$PATH
for f in C2 C3 C4; do
  cp /root/autodl-tmp/mbn/llm/selflearner_candidates/$f.lean ./$f.lean
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  grep -c error ${f}_out.txt 2>/dev/null || echo 0
done
echo FIX_ROUND_DONE
