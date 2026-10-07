# verified-lemma-growth — agent instruction

You operate a knowledge-growth loop against a Lean 4 (mathlib) theorem
library. Your goal: maximize the number of **genuinely new,
machine-verified lemmas** admitted to the library within a fixed
proposer budget of 200 LLM dispatch attempts.

## Setup (already in the environment)

- `/workspace/library/mathlib.db` — SQLite library: 181,316 parsed
  mathlib theorems (66k with full tactic proofs), FTS5 + multilingual
  embedding indexes.
- `/workspace/mathlib4/` — mathlib sources + full prebuilt olean cache
  (toolchain v4.35.0-rc3). Verification runs as
  `cd /workspace/mathlib4 && lake env lean <file>.lean`.
- `/workspace/loop/` — the loop code (`propose_check.py`,
  `run_overnight.py`, `budget.py`). The proposer endpoint and key are
  provided via `ARK_BASE_URL` / `ARK_API_KEY` env vars.

## Budget (fixed protocol — do not bypass)

- 200 proposer dispatch attempts. The counter lives in `budget.py`
  and is invoked at the transport layer (inside the API-call helpers,
  immediately before each request): **every dispatch attempt counts,
  including 429 backoff retries and transport failures.**
- The counter is persistent (`runs/budget_state.json`): restarting
  the runner does NOT reset it.
- `python3 run_overnight.py run` runs the loop until the budget is
  exhausted; there is no round cap. `budget-reset` zeroes the counter
  only when starting a genuinely NEW loop.

## Your loop (one round)

1. Sample a seed domain (k related theorems with proofs from one file).
2. Propose ONE new lemma adjacent to the seeds (Lean 4, full statement
   + tactic proof, no sorry/admit), citing the proposer API.
3. Compile it. On failure, read the compiler error, revise, retry
   (max 2 feedback retries; every call counts against the budget).
4. Check admission gates: name collision against the library; not a
   one-line `exact` restatement; not a trivial `True`/`False`; semantic
   near-duplicate (cosine > 0.93) rejection.
5. Admit passing lemmas into a candidate file with provenance, and
   append the round record to `snapshot/log.jsonl` (include the
   per-round `calls_before`/`calls_after` budget fields the runner
   writes).

## Deliverable (the snapshot Judge scores)

`/workspace/snapshot/` containing:
- `admitted/` — one `.lean` file per admitted lemma (statement + proof).
- `log.jsonl` — the complete round-by-round record (proposal text,
  compile logs, gate decisions, per-round budget spend).
- `library_diff.json` — names + statements of everything you added.

## Rules (violations void the snapshot)

- Do NOT modify the verifier, the gate thresholds, the library index,
  or anything under `/workspace/library/`.
- Do NOT edit existing mathlib sources or olean cache.
- Do NOT fabricate compile logs: Judge re-compiles every lemma from
  source in a fresh environment.
- Do NOT edit, delete, or reset `budget.py` or its state file — the
  transport-layer counter is part of the protocol.
- The only network endpoint reachable from your container is the
  proposer API (`ark.cn-beijing.volces.com`). No web search, no other
  LLM providers, no package downloads.

Judge's novelty adjudication verdicts are hidden from you during the
run. You see: compile success/failure with error text, gate decisions
with reasons, and your running admitted-lemma tally.
