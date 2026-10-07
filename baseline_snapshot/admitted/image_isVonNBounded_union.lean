import Mathlib.Tactic

open Bornology

lemma image_isVonNBounded_union
    {𝕜 E α : Type*} [NormedField 𝕜] [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {f : α → E} {s t : Set α} :
    IsVonNBounded 𝕜 (f '' (s ∪ t)) ↔
      IsVonNBounded 𝕜 (f '' s) ∧ IsVonNBounded 𝕜 (f '' t) := by
  rw [Set.image_union, isVonNBounded_union]