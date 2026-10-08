# miniF2F coverage & evaluation — how selflearner's library maps to the benchmark

[miniF2F](https://github.com/openai/miniF2F) is the standard formal
math benchmark (AMC/AIME/IMO/ Putnam + imo_shortlist problems, Lean 4
version maintained at [yangky11/miniF2F-lean4](https://github.com/yangky11/miniF2F-lean4)).

## What selflearner contributes

1. **A parsed mathlib library** — 181,316 theorems, 66,217 with full
   tactic proofs, in SQLite + FTS5
   ([selflearner](https://github.com/aujurd22/selflearner),
   `parse_mathlib.py`). For miniF2F workers this is a reusable
   retrieval corpus: "which mathlib lemmas look like this problem's
   key step" via bm25 or hybrid RRF (`search_hybrid.py`).
2. **A propose-check loop** whose admission funnel (compile + axiom
   policy + novelty + non-triviality) is directly applicable to
   miniF2F-style proving attempts.
3. **Evaluation** — TODO: script that, for each miniF2F test problem,
   measures (a) which of our 181k library theorems the problem's
   canonical solution cites (coverage), (b) pass@k of our loop's
   proposer seeded with the problem statement.

Status: skeleton only. PRs welcome — see the reference repo.
