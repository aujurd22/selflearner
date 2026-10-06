# rsi/verified-lemma-growth — Task Proposal (v2, revision after automated review)

Revision of 2026-10-06 addressing all five hard-gate failures of the
2026-10-05 automated review (see CHANGELOG at bottom). The full
contributor-owned decisions that the review flagged as missing are now
made explicit in the Evaluation rows.

| Section | Field | Proposal |
| --- | --- | --- |
| Contributor | Full name | JUNRONG DU |
| Contributor | Email | dududu9738@gmail.com |
| Research Question | Repository URL | https://github.com/aujurd22/selflearner |
| Research Question | Exact commit/tag | **102f666** (resubmission snapshot; includes judge_adjudicate.py, judge_score.py with axiom policy, and full pilot logs `docs/pilot_logs/` that the 4470971 review snapshot lacked) |
| Research Question | Scientific question | Under a fixed LLM-proposer budget (200 proposer API calls per loop, retries counted by an in-runner call counter), does a verifier-escorted propose-check loop with a three-gate admission funnel (Lean compilation + axiom policy + novelty + non-triviality) accumulate genuinely new, machine-verified lemmas against the Lean mathlib library at a higher rate than an ungated loop that only requires compilation? |
| Research Question | Why this is scientific research rather than pure engineering optimization | Falsifiable matched comparison: identical proposer model, identical budget (enforced by an in-runner counter), identical seed-domain sampler, identical prompt-assembly and retry policy in BOTH arms — the admission-gate stack is the only manipulated component (config flag in the same code). The loop is iterative change-run-observe-update. Knowledge gained: whether verifier-gated admission increases net new-knowledge accumulation or merely filters without changing proposal quality — the first controlled measurement of what verifier escort is worth for autonomous knowledge growth. |
| Research Question | Starting environment and artifacts | All public at the pinned commit: SQLite library of 181,316 parsed mathlib theorems (66,217 with full tactic proofs) + FTS5 index (`parse_mathlib.py`); mathlib4 sources with full prebuilt olean cache (toolchain v4.35.0-rc3); loop code (`propose_check.py`, `run_overnight.py` with call counter); Judge scorer (`judge_adjudicate.py`, `openrsi-proposal/task/tests/judge_score.py`); multilingual-embedding index (`vectors.npz`, GitHub release [vectors-v1](https://github.com/aujurd22/selflearner/releases/tag/vectors-v1), sha256 46ff6610e1dc8b5772b8f32efa8252453c09aa8a6e145917af33ee792ead63a0). Pilot logs (`runs/overnight_20261005/`, judge reports) included in the repo at the pinned commit. |
| Research Question | Agent's final deliverable | A candidate snapshot: `admitted/*.lean`, `log.jsonl` (complete round record including per-round call counts), `library_diff.json`. Judge re-runs `lake env lean` + `#print axioms` on every lemma from source and re-adjudicates novelty. |
| Research Question | Files/components the agent may modify | Its own candidate-lemma files; proposer prompt assembly; retry strategy — **identical permissions in both arms** (the arms differ ONLY in the admission-gate flag). NOT the verifier, gate thresholds, library index, or scoring code (read-only, snapshot-diff audited). |
| Research Question | Prohibited actions | Modifying or bypassing the Lean verifier or gate code; editing existing mathlib entries, sources, or olean cache; fabricating compile logs (Judge re-verifies everything from source, including axiom dependencies); introducing non-standard axioms (axiom-farm escape — blocked by the judge's `#print axioms` policy); any network endpoint other than the proposer API; training or fine-tuning any model. |
| Reference Baseline | Baseline implementation or artifact | The ungated configuration of the same code at the same commit (`NOVELTY_GATE=0`: compile-pass = admit, all other code paths identical) — a configuration-type baseline, no training; Solution materializes it by setting one environment variable. **Arm matching statement: both arms share the same proposer model, prompt assembly, retry policy, seed-domain sampler, and call budget; the admission-gate flag is the sole difference.** |
| Reference Baseline | Repository evidence paths | `propose_check.py` (gate on/off branch + `novelty_check`), `run_overnight.py` (call counter + budget enforcement), `docs/pilot_logs/` (pilot logs, judge reports, and all experiment JSONs; the `runs/` path in an earlier snapshot returned 404 — resolved by this commit), `judge_adjudicate.py` (adjudication protocol). |
| Reference Baseline | Baseline evaluation path | `python run_overnight.py run 20 low` with the gate flag off; Judge scores the baseline snapshot under the identical adjudication protocol as candidate snapshots. |
| Reference Baseline | Baseline metric reported by the repository | Ungated pilot (1 loop, 20 rounds): 9 admitted, 5 compiled under Judge re-verification, 1 confirmed restatement, 1 trivial, 1 colliding with an existing mathlib name (compile-void). Single-loop; the formal comparison requires ≥3 loops per arm, median-aggregated. |
| Evaluation | Fixed evaluation protocol | **Budget: 200 proposer API calls per loop, enforced by an in-runner counter (`FLYLOOP_CALL_BUDGET`, loop halts at 0 remaining; every proposal request and feedback-retry request increments the counter; transport failures consume budget unless the request never left the runner).** Judge protocol per snapshot: (1) fresh `lake env lean` re-verification of every admitted lemma; (2) `#print axioms` dependency check — only Lean's four standard Prover axioms (propext, Classical.choice, Quot.sound, Lean.ofReduceBool) allowed; (3) triviality gate; (4) novelty adjudication with hybrid retrieval — RRF(semantic top-k embedding, lexical FTS) feeding a cross-model-family LLM judge prompted to name the candidate's mathematical content before verdict. Candidate-invalid (compile failure, parse failure, axiom-policy violation) = unscored and budget-counted. Candidate-only evaluation; the baseline snapshot is scored once under the identical protocol. |
| Evaluation | Evaluation mode and input | Direct evaluation of the submitted snapshot (lemma set + logs). No retraining anywhere in the task. |
| Evaluation | Reward or score definition | Primary: count of lemmas passing Judge re-verification AND axiom policy AND novelty adjudication (direction: higher; unit: lemmas; aggregation: median across ≥3 loops per arm). Secondary: restatement rate, triviality rate, compile-failure rate — reported alongside, never hidden. The non-triviality gate is part of admission (pre-score), so trivial lemmas never enter the reward-relevant set; their would-be count is reported as a secondary metric. Candidate-invalid = unscored. |
| Evaluation | Feedback visible to the agent | Per round: compile success/failure with the full compiler error text, axiom-policy violations if any, gate decisions with reasons, running admitted-lemma tally, **remaining call budget**. |
| Evaluation | Evaluation information hidden from the agent | Judge novelty verdicts during the run (the agent must not optimize against the judge), the held-out restatement probe set (role: post-hoc audit of Judge novelty-adjudication reliability only — it never gates admission, scoring, or the reward), the scoring code. |
| Evaluation | Measures preventing reward hacking | (1) Judge re-verifies every lemma from source in a fresh environment; (2) `#print axioms` dependency check blocks the axiom-farm escape; (3) the novelty adjudicator is a different model family than the proposer, with hybrid (semantic+lexical) retrieval; (4) snapshot diff audit; (5) JSONL completeness and replayability. Residual limitations stated: Judge uses the Work snapshot (shared-environment model, not an independent clean Base); the adjudicator is itself an LLM and imperfect — the restatement rate ships as a reported secondary metric rather than being assumed away. |
| Evaluation | Noise handling and meaningful improvement | ≥3 loops per arm, median aggregation. Pilot plausibility: compile-pass rates moved 7.7% → 45-67% across proposer configurations at n=20 rounds. Formal claims are made only on Judge-adjudicated net counts with per-loop spread. Deterministic re-verification of a fixed artifact is not repeated for ceremony. |
| Workspace | Is web search required? | No. |
| Workspace | May the agent use external services? | **Exactly two, both declared**: (1) the Volcano ARK LLM API (proposer, glm-5.3-flash effort=low) — purpose: candidate-lemma generation and compile-error revision; boundary: prompt content = seed theorem statements + prior-round feedback only; interface: ARK Responses API + runtime-injected key. (2) The **novelty adjudication API used only by the Judge, not by the agent** (a different model family on the same ARK endpoint, judge-side key injected only into the Judge container at runtime via a contributor-held secret, never exposed to the agent or present in any Work-side file) — this is a Judge-side evaluation dependency declared here to resolve the single-service ambiguity; it performs no Work-side compute. |
| Workspace | May the agent construct or collect additional data? | No additional external data. The agent may only append lemmas derived from the proposer. |
| Workspace | Leakage and reward-hacking safeguards | Seed domains sampled from files disjoint from any hint material; the proposer never sees Judge verdicts; the restatement probe set held out; verifier, gate code, and judge scorer read-only inside the Work container; snapshot diff audit on submission. |
| Compute Feasibility | Compute resources per single experiment run | CPU-only. Work: 1 node, 4 cores, 16 GB RAM, 0 GPUs (Lean verification of one file peaks ~2 GB). Judge: same profile, ~2 GB peak. External: proposer + judge API calls only (no GPU compute). Fits one physical node, zero GPUs. |
| Compute Feasibility | Estimated runtime per single experiment run | **Revised with the call-budget semantics the review requested**: at the observed ~6 min/round (1-3 calls each) and a 200-call budget, one loop = 200 calls ≈ 20 rounds ≈ 2 h Work + 0.5 h Judge ≈ 2.5 h → ~9.6 loops in 24 h, ~19.2 in 48 h (review's corrected figure adopted). ≥10-loop minimum met in 48 h; if the 24h figure is required instead, the budget is scaled to 150 calls (15 rounds, 12 loops in 24 h). Basis: same-day measurement of two 20-round pilots. |
| Compute Feasibility | Early-stopping signals / lower-cost proxy experiments | If both arms produce zero Judge-verified lemmas for 3 consecutive loops, the seed-domain sampler is re-drawn (recorded); otherwise run to budget. |
| Compute Feasibility | (review item) Replacement/retry accounting | Feedback retries: each retry call consumes 1 budget unit. Transport failures where the request reached the provider: consumed. Connection failures before dispatch: not consumed (runner logs distinguish these). Resampling of an already-scored snapshot: not performed (single snapshot per loop). |
| Compute Feasibility | (review item) Arm-strategy matching | The agent's editable surface (prompt assembly, retry strategy) is FROZEN to the same implementation in both arms for the duration of the formal comparison; strategy evolution is allowed only between loops, identically in both arms (the loop code is shared and the gate flag is the sole arm difference — enforced by the runner reading both arms' configs from the same file). |

## CHANGELOG (v2 vs the 2026-10-05 rejected draft)

1. **Axiom policy added** (Eval Integrity fail): `#print axioms` dependency
   check in the Judge — only Lean's four standard Prover axioms allowed.
   Blocks the axiom-farm escape (`axiom foo : P` + `theorem := foo`).
2. **Call budget counter added** (Metric fail): in-runner counter,
   loop-halts-at-zero enforcement, summary reporting — the 200-call
   protocol is now enforced, not just described.
3. **Judge API boundary declared** (Data/Network fail): the novelty
   adjudicator runs on the same ARK endpoint with a judge-side key never
   exposed to the agent; it performs no Work-side compute.
4. **Arm-strategy matching declared** (Metric fail): prompt assembly and
   retry policy are frozen identical across arms during the formal
   comparison.
5. **Compute estimate corrected** (Compute note): 9.6/24h, 19.2/48h —
   the review's arithmetic adopted.
6. **Repository completeness**: the pinned commit now includes
   `judge_adjudicate.py`, `judge_score.py`, pilot logs, and judge
   reports that the 4470971 snapshot lacked; `vectors.npz` ships as a
   release asset with sha256.
7. **Non-triviality placement clarified**: trivial lemmas are gated
   pre-admission and reported as a secondary metric; they never enter
   the primary-score set.

## v2 RESUBMISSION NOTE (2026-10-06)

This revision addresses all five hard-gate failures of the 2026-10-05
automated review:

1. **Source Repository**: pinned commit updated to 102f666 (contains
   judge_adjudicate.py, judge_score.py with the axiom policy, and full
   pilot logs under docs/pilot_logs/ — the runs/ paths that returned
   404 are resolved); vectors.npz shipped as release asset vectors-v1
   with sha256.
2. **Metric**: 200-call budget now enforced by an in-runner counter
   (FLYLOOP_CALL_BUDGET); retry/transport accounting specified;
   arm-strategy matching declared (frozen identical across arms).
3. **Evaluation Integrity**: #print axioms dependency check added to
   the Judge scorer (only Lean's four standard Prover axioms allowed);
   judge scorer shipped in task/tests/; hidden probe set role defined
   (post-hoc audit of judge reliability, never gates admission);
   judge_adjudicate.py's role clarified (development-time adjudication
   protocol; the submitted task ships judge_score.py as the scorer).
4. **Data/Network**: the novelty adjudicator's model, endpoint, and
   key-injection boundary fully declared (Judge-side only).
5. **Readiness**: all contributor-owned decisions now explicit in the
   Evaluation rows (call accounting, triviality placement, arm
   matching, axiom policy, probe role, key injection).

The axiom policy has been battle-tested: 6 SL-candidate lemmas from
the pilot were re-verified under the policy (6/6 pass, zero
non-standard axioms) — see axiom_batch.sh and
axioms_full_report.txt in the repository.

## Review retry note

The 2026-10-06 02:22 rubric review failed before completion (no error
details emitted). This edit triggers a retry of the identical v2
proposal — no content changes.
