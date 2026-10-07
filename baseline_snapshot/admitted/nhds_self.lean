import Mathlib.Topology.Basic

open scoped Topology

theorem nhds_self {X : Type*} [TopologicalSpace X] (x : X) :
    𝓝 x = 𝓝 x := by
  rfl