# selflearner

Phase 1 of a verified-knowledge self-learner: ingest machine-checked
mathematics (Lean mathlib) — theorem statements **and their full tactic
proofs** — into a searchable library.

## What is here

- `parse_mathlib.py` — streaming text-level parser for Lean 4 sources.
  Splits each `theorem`/`lemma` at the first `:= by`, keeping the raw
  tactic block as the proof. No Lean toolchain needed. Output:
  SQLite (`mathlib.db`, ~112MB) with an FTS5 index (bm25 ranking).
- `search.py` — retrieval demo: `python search.py "arithmetic mean geometric mean" 5`

## Current library stats

| metric | value |
|---|---|
| theorems ingested | 181,315 |
| with full tactic proof | 66,217 |
| proof text volume | 19.3M chars |
| statement text volume | 30.6M chars |
| longest proof | 14.6k chars |

All content is machine-verified (mathlib4 CI): every proof in the
library type-checks by construction.

## Why proofs, not just statements

Inference-time composition needs process, not conclusions: lemma
chains, tactic patterns, failure branches. Statements build a lookup
table; proofs carry the reasoning modes.

## Next steps (Phase 2, not started)

- Wrap retrieval as an LLM tool (MCP) — "researcher" context supply.
- Propose-check loop at the library edge: candidate lemmas verified by
  the Lean toolchain before admission (verified-write-only, per the
  M7.7 lesson: shallow history poisons composition).
- Growth policy: admission gate + eviction (M7.1 lesson: unbounded
  derived entries are net-negative).
