import Mathlib.MeasureTheory.Measure.MeasureSpace

open MeasureTheory

lemma measure_mono' {α : Type*} [MeasurableSpace α] {μ : Measure α} {s t : Set α}
    (h : s ⊆ t) : μ s ≤ μ t := by
  exact measure_mono h