#!/bin/bash
# C2 rewrite with Nat.tri + C3 corrected identity, reverify
cd /root/autodl-tmp/mbn/llm/selflearner_candidates

cat > C2.lean <<'LEOF'
import Mathlib.Tactic

/-- 8 times the n-th triangular number plus one is (2n+1) squared. -/
theorem sl_eight_tri_oct (n : ℕ) : 8 * Nat.tri n + 1 = (2 * n + 1) ^ 2 := by
  induction n with
  | zero => norm_num [Nat.tri]
  | succ k ih => rw [Nat.tri_succ, ih]; ring
LEOF

cat > C3.lean <<'LEOF'
import Mathlib.Tactic

/-- Three times the sum of i*(i+1) for i < n+2 equals the product
(n+1)(n+2)(n+3) — the classic k(k+1)(k+2)/3 identity, stated without
division. -/
theorem sl_sum_i_ipl (n : ℕ) :
    3 * ∑ i ∈ Finset.range (n + 2), i * (i + 1)
      = (n + 1) * (n + 2) * (n + 3) := by
  induction n with
  | zero => norm_num [Finset.sum_range_succ]
  | succ k ih =>
    rw [Finset.sum_range_succ, ih]
    ring
LEOF

cd /root/autodl-tmp/mathlib4
export PATH=/root/.elan/bin:$PATH
for f in C2 C3; do
  cp /root/autodl-tmp/mbn/llm/selflearner_candidates/$f.lean ./$f.lean
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  grep -c "error" ${f}_out.txt 2>/dev/null || echo 0
done
echo FIX3_DONE
