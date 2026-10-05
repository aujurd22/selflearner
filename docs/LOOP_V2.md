# Loop v2 design — cross-repo audit → upgrade list

Baseline (v1) ran 2h on 2026-10-05 evening; v2 goes overnight.
Each upgrade cites the sibling-repo result that motivates it.

## v2 changes (implemented 2026-10-05)

1. **Semantic novelty gate** (intuition-mechanism P205: C∧V∧T∧N lacks the
   N channel — doubao passed exams by mechanical extrapolation of
   memorized rules). Candidate statement is embedded and compared to the
   theorem vector index: cosine top-1 > 0.93 => DUP.

   **Measured limit (2026-10-05)**: a genuinely new lemma
   (IsCyclic.pow_eq_one_iff) sits at 0.85 cosine to its same-topic
   nearest neighbor (IsCyclic.exists_apply_ne_one), while a paraphrased
   restatement of Nat.infinite sits at 0.84 — the two distributions
   OVERLAP, so embedding thresholds cannot separate novel from
   restated. The gate at 0.93 only catches verbatim-level duplication;
   finer novelty needs an LLM adjudicator shown the semantic top-3
   ("is this a restatement?") — queued as v2.5, not run tonight (avoid
   stacking untested variables into the overnight arm).

2. **Fail-streak domain switch + mid-run diag** (flyloop: 25%-progress
   diag catches dead machinery early; marathon-era lesson that a stuck
   regime must be exited, not endured). 4 consecutive fails => force a
   new seed file and log `domain_switch`; every 25% of rounds prints a
   diag line (pass rate so far, top fail bucket).

3. **Retract tombstones** (flymemory L4: dedup/merge silently swallows
   small edits; lineage must be explicit). `retract()` now records into
   a `retracted` table (name, reason, time) instead of bare DELETE.

4. **Seed provenance** (flyloop G4'/RUNSEED: conclusions must survive a
   seed change; config-bound results must be labeled). The run seed and
   per-round seed-file choice are written into log.jsonl.

## Already in place (v1), now with their provenance

- Compile-error feedback with retries — intuition P240: pure scalar
  feedback is worse than nothing (−0.64 bits/call); the Lean error text
  is the asset. Retry budget: 2.
- effort=low proposer — measured 2/3 vs 1/13 (2026-10-05 A/B).
- Verified-write-only admission, three gates — flyloop M7 arc: the
  composition ceiling is the verified-entry accumulation rate; early
  unverified re-injection poisons (M7.7 REJECT).
- Declarative-statement knowledge cards — flymemory M5T: 100% vs 2.6%.
- External exact store (SQLite) carries recall, model only proposes —
  mbn: MBNA is NOT data-efficient; parameterized recall loses.

## Deliberately deferred

- Aggregate-query protocol (flymemory L5): multi-turn tool-ish retrieval
  for "how many lemmas about X" — demo-level, not loop-critical.
- Counterfactual rename exams (P205 full form): the semantic gate is the
  cheap approximation; full rename-exam protocol is a Phase 3 item.
- Dead-entry diagnostics (never-retrieved entries): needs a usage log on
  the search path first; scheduled with the MCP wrapping.
- Docstring statement-form normalization (M5T for lemma docstrings):
  cosmetic, batch later.
