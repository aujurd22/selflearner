import Mathlib.Algebra.Field.Basic

theorem selflearner (K : Type*) [Field K] (a : K) (ha : a ≠ 0) : a * a⁻¹ = 1 :=
  mul_inv_cancel₀ ha

