#!/bin/bash
# SELF-CONTAINED: create candidates + verify all 4 in mathlib4 project
mkdir -p /root/autodl-tmp/mbn/llm/selflearner_candidates
cd /root/autodl-tmp/mbn/llm/selflearner_candidates

cat > C1.lean <<'LEOF'
import Mathlib.Tactic

/-- Sum of the first n odd numbers equals n squared. -/
theorem sl_odd_sum_sq (n : ℕ) : ∑ i ∈ Finset.range n, (2 * i + 1) = n ^ 2 := by
  induction n with
  | zero => simp
  | succ k ih =>
    rw [Finset.sum_range_succ, ih]
    ring
LEOF

cat > C2.lean <<'LEOF'
import Mathlib.Tactic

/-- 8 times the n-th triangular number plus one is (2n+1) squared. -/
theorem sl_eight_tri_oct (n : ℕ) : 8 * (∑ i ∈ Finset.range n, i) + 1 = (2 * n + 1) ^ 2 := by
  induction n with
  | zero => simp
  | succ k ih =>
    rw [Finset.sum_range_succ, ih]
    ring
LEOF

cat > C3.lean <<'LEOF'
import Mathlib.Tactic

/-- 3 * sum(i*(i+1)) for i < n equals n*n*(n+1) - n*n*(n-1) form, stated
without truncated subtraction by splitting on n = 0. -/
theorem sl_sum_i_ipl (n : ℕ) :
    3 * (∑ i ∈ Finset.range n, i * (i + 1)) + n * n * n = n ^ 3 + 3 * (∑ i ∈ Finset.range n, i) := by
  induction n with
  | zero => simp
  | succ k ih =>
    rw [Finset.sum_range_succ, ih]
    ring
LEOF

cat > C4.lean <<'LEOF'
import Mathlib.Tactic

/-- Nicomachus: the square of the sum of the first n naturals equals the
sum of their cubes (both sides via the triangular-number formula). -/
theorem sl_cubes_tri (n : ℕ) :
    (∑ i ∈ Finset.range n, i ^ 3) = (∑ i ∈ Finset.range n, i) ^ 2 := by
  induction n with
  | zero => simp
  | succ k ih =>
    have htri : ∑ i ∈ Finset.range (k + 1), i = k * (k + 1) / 2 := by
      rw [Finset.sum_range_succ]
      simp [Nat.div_add_mod_mul_two (k * (k + 1)) rfl]
      ring
    rw [Finset.sum_range_succ, ih, htri]
    push_cast
    ring
LEOF

cd /root/autodl-tmp/mathlib4
export PATH=/root/.elan/bin:$PATH
for f in C1 C2 C3 C4; do
  cp /root/autodl-tmp/mbn/llm/selflearner_candidates/$f.lean ./$f.lean
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  head -2 ${f}_out.txt
done
echo SELFCONTAINED_DONE
