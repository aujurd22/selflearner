import Mathlib.Tactic

/-- 8 times the n-th triangular number plus one is (2n+1) squared. -/
theorem sl_eight_tri_oct (n : ℕ) : 8 * Nat.tri n + 1 = (2 * n + 1) ^ 2 := by
  induction n with
  | zero => rfl
  | succ k ih => rw [Nat.tri_succ, ih]; ring
