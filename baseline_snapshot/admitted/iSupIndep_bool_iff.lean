import Mathlib.Tactic

lemma iSupIndep_bool_iff {α : Type*} [CompleteLattice α] (f : Bool → α) :
    iSupIndep f ↔ Disjoint (f false) (f true) := by
  rw [iSupIndep_def]
  refine ⟨fun h => ?_, fun h i => ?_⟩
  · simpa using h false
  · fin_cases i <;> simpa [disjoint_comm] using h