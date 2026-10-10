# Proposal: Verified-Lemma-Growth eval — Lean 4 theorem library growth under a fixed budget

## Summary

A new eval for measuring whether an LLM agent, working inside a Lean 4
/mathlib environment with retrieval over a parsed 181k-theorem library,
can accumulate **genuinely new, machine-verified lemmas** under a fixed
proposer-dispatch budget — and whether adding a verification-and-novelty
admission funnel changes that rate.

## Why this eval is different from existing math evals

- **Not a fixed benchmark**: the agent discovers new lemmas, so the
  ground truth changes with each run. The verifier is the Lean 4
  compiler + axiom policy — no human labeling needed.
- **Measures growth, not problem-solving**: existing math evals
  (MATH, GSM8K, miniF2F) test problem-solving on fixed questions. This
  eval tests whether an agent can contribute **new reusable knowledge**
  to a growing library.
- **Honest null result included**: our pilot showed 0/60 net-novel
  lemmas with a weak proposer — demonstrating the proposer is the
  bottleneck, not the verifier. This is itself a publishable finding.

## Design

- **Task**: agent works inside a Lean 4 / mathlib environment
  (toolchain v4.35.0-rc3, full olean cache) with retrieval over 181k
  parsed theorems.
- **Loop**: seed-domain sampling → LLM proposal → Lean compile →
  axiom policy → novelty adjudication → admission.
- **Two arms**: gated (compile + axiom + novelty + non-triviality) vs
  compile-only. One flag switches between them.
- **Budget**: 60 proposer dispatches per loop, ≥3 loops per arm.
- **Score**: count of admitted lemmas passing Lean re-verification +
  axiom policy + novelty adjudication + within-snapshot dedup.

## Existing implementation

Complete three-arm implementation, training script, attack suite, and
results are available at:
[aujurd22/intuition-mechanism/vcnet_mb](https://github.com/aujurd22/intuition-mechanism/tree/main/vcnet_mb)
and
[aujurd22/selflearner](https://github.com/aujurd22/selflearner).

## Ask

- Is this a good fit for the Evals framework?
- Should the Lean verification be implemented as a custom eval
  function, or does the framework have a better pattern for
  compiler-verified outputs?
- We're happy to contribute the eval code and dataset.
