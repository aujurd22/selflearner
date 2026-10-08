#!/bin/bash
# strong candidates D1-D4: create + verify locally (WSL mathlib env)
mkdir -p /root/mbn/llm/strong_cands
cd /root/mbn/llm/strong_cands

cat > D1.lean <<'LEOF'
import Mathlib.Tactic

/-- For n >= 1, every m in [2, n+1] divides (n+1)! + m, so the run
((n+1)!+2, ..., (n+1)!+(n+1)) consists of composite numbers (Wilson
corollary). -/
theorem sl_factorial_run (n : ℕ) (hn : 1 ≤ n) :
    ∀ m ∈ Finset.Icc 2 (n + 1), m ∣ (n + 1)! + m := by
  intro m hm
  have hm2 : m ≤ n + 1 := hm.2
  apply Nat.dvd_add_right
  have h : m ∣ (n + 1)! := Nat.factorial_dvd_factorial (by omega)
  exact h
LEOF

cat > D2.lean <<'LEOF'
import Mathlib.Tactic

/-- Sum of divisors of 2^k equals 2^(k+1) - 1. -/
theorem sl_sigma_two_pow (k : ℕ) :
    ∑ d in Nat.divisors (2 ^ k), d = 2 ^ (k + 1) - 1 := by
  induction k with
  | zero => simp [Nat.divisors_one]
  | succ n ih =>
    rw [Nat.pow_succ, Nat.divisors_pow_succ (Nat.Prime.two_gt_one)] if false then skip
    simp
LEOF

cat > C2.lean <<'LEOF'
import Mathlib.Tactic

/-- 8 times the n-th triangular number plus one is (2n+1) squared. -/
theorem sl_eight_tri_oct (n : ℕ) : 8 * Nat.tri n + 1 = (2 * n + 1) ^ 2 := by
  induction n with
  | zero => rfl
  | succ k ih => rw [Nat.tri_succ, ih]; ring
LEOF
echo CREATED
PY=/usr/bin/python3
$PY - <<'PYEOF'
import io
p = 'D2.lean'
s = io.open(p, encoding='utf-8').read()
s = s.replace('  | succ n ih =>\n    rw [Nat.pow_succ, Nat.divisors_pow_succ (Nat.Prime.two_gt_one)] if false then skip\n    simp',
              '  | succ n ih =>\n    rw [Nat.pow_succ]\n    simp [Nat.divisors_pow_succ Nat.Prime.two_gt_one]\n    omega')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('D2 fixed')
PYEOF
LEOF_MARKER_UNUSED=1
