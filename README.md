# selflearner

A verified-knowledge self-learner: a propose-check loop that grows a
Lean 4 (mathlib) theorem library with machine-verified, admitted-only
writes. This repository is the reference implementation for the
OpenRSI task proposal `rsi/verified-lemma-growth`
(openrsi-proposal/proposal.md).

## What is here

- `parse_mathlib.py` — streaming text-level parser for Lean 4 sources
  into SQLite (`mathlib.db`) with an FTS5 index. Library: 181,316
  parsed mathlib theorems, 66,217 with full tactic proofs.
- `propose_check.py` — the loop: seed-domain sampling, LLM proposal,
  Lean compile check, Work-side admission gates (arm-switchable via
  `SELFLEARNER_ARM`: gated = compile + axiom policy + novelty +
  non-triviality; control = compile only), admit with provenance.
- `run_overnight.py` — the runner: starts the mandatory proposer
  proxy, runs the loop to budget exhaustion or deadline
  (`--deadline-h`), resumes without resetting the budget counter.
- `ark_proxy.py` — the proposer's dispatch gateway: counts one unit
  per upstream attempt (429 retries included), pins the model field,
  answers HTTP 429 at the declared budget cap without dispatching,
  persists the count atomically (restore-not-reset; missing/corrupt
  state aborts startup).
- `search.py` / `search_hybrid.py` — retrieval (bm25 / RRF hybrid).
- `baseline_snapshot/` — REFERENCE-ONLY artifact from the gated arm
  of the SL-60 pilot (18 lemmas). It predates the budget-reconciliation
  gate and is NOT a scoreable snapshot; the formal comparison uses
  fresh Work-produced controls.
- `openrsi-proposal/` — the task proposal (proposal.md), the Harbor
  task definition (task.toml, instruction.md), the Judge scorer
  (tests/judge_score.py with the budget-reconciliation gate, invoked
  via tests/test.sh), and the environment definition.
- `attic/` — retired one-off scripts from earlier iterations
  (kept for history, not part of the task).
- `docs/` — pilot logs, judge reports, design notes.

## The budget contract (summary)

The 200-dispatch budget is a declared protocol parameter, audited —
not cryptographically enforced (the Work agent runs as root in a
shared container; no in-container mechanism can make a credential
unreadable, and none is claimed). Enforcement is exclusion-based at
scoring time: the Judge's `budget_reconcile()` gate forces the
primary score to 0 unless `snapshot/log.jsonl` carries a complete,
monotonic, within-budget spend chain and every admitted lemma has a
proposing round in it.

## License

MIT (see LICENSE).
