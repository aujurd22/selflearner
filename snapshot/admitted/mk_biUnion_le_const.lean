import Mathlib

theorem mk_biUnion_le_const {ι α : Type*} {s : Set ι} (hs : s.Nonempty) (t : Set α) :
    (⋃ i ∈ s, t) = t := by
apply le_antisymm
  · intro x hx
    obtain ⟨i, hi, hx⟩ := Set.mem_iUnion₂.1 hx
    exact hx
  · intro x hx
    obtain ⟨i, hi⟩ := hs
    exact Set.mem_iUnion₂.2 ⟨i, hi, hx⟩
