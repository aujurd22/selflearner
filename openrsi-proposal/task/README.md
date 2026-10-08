# rsi/verified-lemma-growth — task draft

AutoResearch task for the OpenRSI Index (draft 0.1.0, pre
proposal-agent review). CPU-only lane: 4 cores / 16 GB RAM / 0 GPUs.

## What the task measures

Whether a verifier-escorted propose-check loop with a three-gate
admission funnel (Lean compilation + novelty + non-triviality)
accumulates **genuinely new, machine-verified lemmas** faster than an
ungated compile-only loop, under an identical fixed LLM-proposer
budget against Lean mathlib.

## Layout

- `task.toml` — Harbor task manifest (CPU-only; Work allowlist is
  loopback-only: the proposer proxy is the single counted egress;
  Judge allowlist: DeepSeek only).
- `instruction.md` — the research agent's brief.
- `tests/test.sh` — Harbor verifier entry (executes judge_score.py).
- `tests/judge_score.py` — Judge-only scorer: Lean re-verification of
  every admitted lemma under the task-level network policy with a
  credential-scrubbed subprocess env (unshare -rn as optional second
  layer when the runtime permits), triviality gate, hybrid-retrieval
  novelty adjudication (semantic + lexical RRF legs feeding a
  cross-model LLM judge), cross-candidate in-snapshot dedup. Never
  trusts candidate-reported logs. Writes /logs/verifier/reward.json.

## Budget enforcement architecture

The proposer budget is enforced at a network chokepoint, not by
client-side convention:

- `ark_proxy.py` runs inside Work and IS the proposer endpoint from
  the agent's perspective (`ARK_BASE_URL=http://127.0.0.1:8080`);
- the real ARK endpoint and key exist only in the proxy process env
  (host-secret injection), never in the agent shell;
- the Work network allowlist admits ONLY loopback, so a candidate
  bypassing the loop's Python helpers (curl, raw sockets, its own
  code) still cannot reach the API except through the proxy;
- the proxy counts one unit per upstream dispatch attempt (429
  backoff retries each count), answers HTTP 429 at the cap without
  dispatching upstream, and persists the count atomically
  (restore-not-reset on restart).

## Evidence from the pilot (2026-10-05, 20 rounds/arm, judge
adjudication)

| arm | admitted | compiled (judge re-run) | confirmed restatements | trivial |
|---|---|---|---|---|
| gated | 9 | 8 | 2 | 0 |
| ungated | 9 | 5 | 1 (+1 name collision with mathlib, compile-void) | 1 |

Compile-fail per admitted lemma: the ungated arm admitted 4 lemmas
that do not compile (including `add_zero`, which collides with
mathlib); the gated arm's compile gate caught that class entirely.

Honest limitation measured in the same pilot: a semantic-only novelty
gate admitted 8 textbook restatements of `Nat.add_zero` ("n + 0 = n")
across both arms — embeddings cannot separate a new lemma from its
same-topic neighbors (cosine 0.85 novel vs 0.84 restated). The Judge's
hybrid retrieval leg (lexical FTS + semantic RRF) is the fix this task
ships with; the residual limitation is stated rather than hidden.

## Provenance

Source: github.com/aujurd22/selflearner (the propose-check loop is
`propose_check.py` + `run_overnight.py`; the library builder is
`parse_mathlib.py`; pilot logs and judge reports in `runs/`).
