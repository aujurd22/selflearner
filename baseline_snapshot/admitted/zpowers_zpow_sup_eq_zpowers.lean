import Mathlib.Tactic

namespace Subgroup

theorem zpowers_zpow_sup_eq_zpowers {G : Type*} [Group G] {g : G} {i j : ℤ}
    (h : (i.gcd j : ℤ) = 1) :
    zpowers (g ^ i) ⊔ zpowers (g ^ j) = zpowers g := by
  rw [zpowers_zpow_sup, h, zpow_one]

end Subgroup