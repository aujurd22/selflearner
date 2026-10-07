import Mathlib.Tactic
import Mathlib.Data.Matrix.Basic

/-- A corollary of `Matrix.commute_diagonal`: diagonal matrices commute with each other. -/
lemma diagonal_mul_comm {n : Type*} {α : Type*}
    [NonUnitalNonAssocCommSemiring α] [Fintype n] [DecidableEq n]
    (d₁ d₂ : n → α) :
    Matrix.diagonal d₁ * Matrix.diagonal d₂ =
      Matrix.diagonal d₂ * Matrix.diagonal d₁ :=
  (Matrix.commute_diagonal d₁ d₂).eq