# Related work comparison — OpenRSI context (2026-10-06)

Three directly-overlapping preprints (April–October 2026 window) were
surfaced by the OpenRSI rubric-review bot during our submission. All
three address pieces of the verified-lemma-growth problem; none runs
the admission-gate ablation that IS our task.

## 1. AViD Journal (Porto, arXiv:2608.14669)

**What**: LaTeX article → Lean 4 formalization → automated novelty
verdict via a three-dimension decision tree (prior existence via
Mathlib/TheoremSearch/Matlas search + temporal filter + LLM judge;
non-triviality via automated tactics; structural proof distance via
Jaccard over premise sets).

**Evaluated on**: arXiv papers withdrawn for declared duplication.
Qualitative only — three implementation-independent obstacles
identified (compilation != semantic fidelity; recall capped by index
coverage; arXiv strips sources on withdrawal). Explicitly preliminary:
no large-scale quantitative evaluation, no ablations of the
decision-tree gates/thresholds. Code released (github.com/ayrtonporto/avid-journal).

## 2. Self-expanding mathematical libraries (Patel et al., arXiv:2609.28603)

**What**: LLM-driven discovery of "interesting" theorems in formal
libraries. Intrinsic interestingness = proof-length/statement-length
ratio (short statement, long proof); shows correlation with
downstream utility. Trains a 27B difficulty predictor that beats
frontier general-purpose models. Pipeline: generate candidates →
rank → prove → iterate ("self-expanding library"). Mathlib overlap
drops 91.9% → 30.6%.

**NOT done**: correlation shown empirically, no theoretical
guarantee; interestingness is a crude proxy (no depth/elegance/
relevance); no open-problem claims; no ablation of admission gates;
no code/data released (CC BY-NC-SA).

## 3. PriorProof (Somani, arXiv:2607.16997)

**What**: automated time-anchored measure of proof-route
nonstandardness — dependency footprint of a Lean proof scored for
surprisal under a prior built from an earlier quarterly Mathlib
snapshot. No hand-built technique ontology; statement retrieval
learned from proof-derived contrastive pairs.

**Evaluated on**: blinded topology study, 100 presentations → 76
distinct pairs. Agreement with rater majority 69.7%; canonical
contrasts 91.7%. Nonmonotone score-gap quartiles. Best LM baseline
78.9%; McNemar p=0.210 (difference vs PriorProof not established at
this n). Code released (github.com/neelsomani/priorproof).
