import Mathlib.Tactic

/-- Three times the sum of i*(i+1) for i < n+2 equals the product
(n+1)(n+2)(n+3) — the classic k(k+1)(k+2)/3 identity, stated without
division. -/
theorem sl_sum_i_ipl (n : ℕ) :
    3 * ∑ i ∈ Finset.range (n + 2), i * (i + 1)
      = (n + 1) * (n + 2) * (n + 3) := by
  induction n with
  | zero => norm_num [Finset.sum_range_succ]
  | succ k ih => rw [ih]; ring
