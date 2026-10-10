import Mathlib

theorem source_inter_preimage_target {α β : Type*} (e : PartialEquiv α β) :
    e.source ∩ e ⁻¹' e.target = e.source := by
ext x
  constructor
  · rintro ⟨hx, hx'⟩
    exact hx
  · intro hx
    exact ⟨hx, e.map_source hx⟩
