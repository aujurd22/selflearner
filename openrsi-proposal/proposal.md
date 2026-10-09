# rsi/verified-lemma-growth — Task Proposal (v16, revision after automated review)

Revision of 2026-10-08 addressing the 2026-10-08 08:40 review. The
new mechanism is PROVIDER-SIDE ATTESTATION: the proxy's dispatch
ledger (agent-unwritable, provider-reported token usage + prompt/output
hashes per dispatch) travels with the snapshot and the Judge
cross-checks it before scoring; snapshots without a consistent ledger
score 0. Plus: the arm switch now REALLY covers the axiom gate (the
08:40 review correctly caught that the v15 edit had not landed), and
baseline_snapshot/ is REFERENCE-ONLY with the scored control produced
fresh under the full protocol. Also: a rubric-level clarification
request with three implementable resolutions has been posted to the
maintainers (see the discussion thread).
independent contributor audit of the pinned tree. The v14 central
mechanism (the Judge-side budget-reconciliation gate) is verified
PRESENT at the pinned commit this time (the 05:52 review inspected a
tree that predated the gate; the pin row now points at the commit that
carries it). v15 additionally: (a) aligns the arm switch —
SELFLEARNER_ARM toggles the ENTIRE admission stack (axiom policy +
novelty + non-triviality) so the control arm is genuinely
compile-only, while the Judge's axiom policy remains a uniform
measurement floor for both arms; (b) declares baseline_snapshot/
REFERENCE-ONLY (it predates the reconciliation gate, carries no
spend chain, and is not submitted for scoring; the formal comparison
uses fresh Work-produced controls only); (c) sizes the formal
comparison to fit the 48h window (60-dispatch loops, 6 loops total,
~15 h including Judge); (d) repo hygiene for reliable bundle fetches
(53 one-off scripts moved to attic/, __pycache__ untracked, README
rewritten, MIT LICENSE, MANIFEST.sha256 checksums for every
task-relevant file). CHANGELOG at the bottom.

| Section | Field | Proposal |
| --- | --- | --- |
| Contributor | Full name | JUNRONG DU |
| Contributor | Email | dududu9738@gmail.com |
| Research Question | Repository URL | https://github.com/aujurd22/selflearner |
| Research Question | Exact commit/tag | 3c5fdee7703c1e247740673865aab11313c54d4c (bare immutable commit SHA, single self-contained commit semantics: this commit contains the COMPLETE v15 state — proposal prose, ark_proxy.py, runner, client, Work-side admission gates with the arm switch, Judge scorer WITH the budget-reconciliation gate AND the provider-side dispatch cross-check, task.toml, tests/test.sh, environment definition, MANIFEST.sha256 — verified by git grep at this SHA. The discussion body is not part of the commit graph, so this reference is stable.) |
| Research Question | Scientific question | Under a declared proposer dispatch budget (60 proposer API dispatch attempts per loop — a protocol parameter whose execution is fully audited, see Evaluation), does a verifier-escorted propose-check loop with a three-gate admission funnel (Lean compilation + axiom policy + novelty + non-triviality) accumulate genuinely new, machine-verified lemmas against the Lean mathlib library at a higher rate than an ungated loop that only requires compilation? |
| Research Question | Why this is scientific research rather than pure engineering optimization | Falsifiable matched comparison: identical proposer model, identical declared dispatch budget with identical accounting, identical seed-domain sampler, identical prompt-assembly and retry policy in BOTH arms — the admission-gate stack is the only manipulated component (config flag in the same code). The loop is iterative change-run-observe-update. Knowledge gained: whether verifier-gated admission increases net new-knowledge accumulation or merely filters without changing proposal quality — a controlled measurement of what verifier escort is worth for autonomous knowledge growth. |
| Research Question | Starting environment and artifacts | All public at the pinned commit: SQLite library of 181,316 parsed mathlib theorems (66,217 with full tactic proofs) + FTS5 index (`parse_mathlib.py`); mathlib4 sources with full prebuilt olean cache (toolchain v4.35.0-rc3); loop code (`propose_check.py`, `run_overnight.py`); proposer proxy (`ark_proxy.py`) — the loop's declared dispatch gateway with per-attempt counting; Judge scorer (`openrsi-proposal/task/tests/judge_score.py` via `openrsi-proposal/task/tests/test.sh` — the ONLY scorer; the legacy pilot-time `judge_adjudicate.py` has been REMOVED); multilingual-embedding index (`vectors.npz`, GitHub release vectors-v1 (github.com/aujurd22/selflearner/releases/tag/vectors-v1), sha256 46ff6610e1dc8b5772b8f32efa8252453c09aa8a6e145917af33ee792ead63a0). Pilot logs (`runs/overnight_20261005/`, `docs/pilot_logs/`, judge reports) are tracked in the repository at the pinned commit. |
| Research Question | Agent's final deliverable | A candidate snapshot: `admitted/*.lean`, `log.jsonl` (complete round record including per-round `calls_before`/`calls_after` budget spend), `library_diff.json`, plus the runner budget summary. Judge re-runs `lake env lean` + `#print axioms` on every lemma from source, re-adjudicates novelty, and runs the budget-reconciliation gate (below) BEFORE scoring. |
| Research Question | Files/components the agent may modify | Its own candidate-lemma files; proposer prompt assembly; retry strategy — **identical permissions in both arms** (the arms differ ONLY in the admission-gate flag). NOT the verifier, gate thresholds, library index, scoring code, the proxy, or the budget state (protocol components; tampering is detected by the reconciliation gate and voids the score). |
| Research Question | Prohibited actions | Modifying or bypassing the Lean verifier or gate code; editing the proxy or its persistent budget state; editing existing mathlib entries, sources, or olean cache; fabricating compile logs (Judge re-verifies everything from source, including axiom dependencies); introducing non-standard axioms (axiom-farm escape — blocked at BOTH admission time and Judge time by the `#print axioms` policy); producing lemmas outside the audited loop (the reconciliation gate excludes any lemma without a proposing round in log.jsonl from the primary count); training or fine-tuning any model. |
| Reference Baseline | Baseline implementation or artifact | TWO components: (1) **`baseline_snapshot/`** — the pilot run's 18 admitted lemmas + library_diff.json, a REFERENCE-ONLY artifact (it predates the budget-reconciliation gate and carries no log.jsonl spend chain; it is NOT submitted for scoring and earns nothing — its role is to show the gate-stack output shape); (2) the control configuration of the same code (`SELFLEARNER_ARM=control`) for generating FRESH matched controls during the formal loops — those ARE scored under the full reconciliation protocol. **Arm matching statement: both arms share the same proposer model, prompt assembly, retry policy, seed-domain sampler, and declared dispatch budget; the admission-gate flag is the sole difference.** |
| Reference Baseline | Repository evidence paths | `propose_check.py`, `run_overnight.py`, `ark_proxy.py`, `docs/pilot_logs/`, `runs/overnight_20261005/`, `baseline_snapshot/`, `openrsi-proposal/task/` (task.toml + tests + environment). **Provenance of baseline_snapshot/**: produced by the GATED arm of the SL-60 pilot (glm-5.3-flash effort=low, 60 rounds, single loop, 2026-10-06) — REFERENCE-ONLY, not scoreable. The control for the formal comparison is Work-produced fresh (`SELFLEARNER_ARM=control`, identical 60-dispatch budget) and is scored under the full reconciliation protocol; the pilot's ungated numbers (9 admitted under a 20-round protocol, not call-budget-matched) are pilot evidence only. |
| Reference Baseline | Baseline evaluation path | `OVERNIGHT_TAG=<new> python3 run_overnight.py run --deadline-h 12` with the gate flag off (a new OVERNIGHT_TAG declares a new loop with a fresh budget state file; --deadline-h is a first-class CLI argument and formal launches pass a value covering the full 60-dispatch budget). The reference-only baseline_snapshot/ is NOT submitted for scoring; the control snapshot (SELFLEARNER_ARM=control) is scored under the identical adjudication protocol as candidate snapshots. |
| Reference Baseline | Baseline metric reported by the repository | Ungated pilot (1 loop, 20 rounds): 9 admitted, 5 compiled under Judge re-verification, 1 confirmed restatement, 1 trivial, 1 colliding with an existing mathlib name (compile-void). Single-loop; the formal comparison requires ≥3 loops per arm, median-aggregated. |
| Evaluation | Fixed evaluation protocol | **Budget contract (v15, honest semantics): the dispatch budget (60 attempts per loop in the formal comparison) is a PROTOCOL PARAMETER whose execution is audited, not a cryptographic guarantee. In the shared-root Work container the agent runs as root and could reach the provider directly — no in-container mechanism can make the credential unreadable, and this proposal does not claim otherwise (the harness's own Agent model has the same property: the claude/codex CLI receives its provider key in the container environment). Enforcement is therefore EXCLUSION-BASED at scoring time: the Judge runs `budget_reconcile()` on `snapshot/log.jsonl` BEFORE computing the primary score, and a snapshot fails reconciliation — primary score forced to 0 — if (1) `log.jsonl` is missing or unreadable, (2) any round record lacks integer `calls_before <= calls_after`, (3) the chain is non-monotonic (counter went backwards: state tampering), (4) the final count exceeds the declared budget (60 dispatches per loop in the formal comparison), or (5) an admitted lemma has no proposing round in the log (provenance chain broken). A reconciliation failure is reported with its reason and the audited chain in report.json; the snapshot's lemmas keep their compile/novelty verdicts as diagnostics but earn nothing. Honest residual, stated: a determined root agent could fabricate a fully self-consistent log — the score contract is defined over AUDITED loop output and this residual is accepted rather than hidden; fabricating the log violates the prohibitions above and voids the snapshot.** Dispatch accounting is uniform: the proxy counts one unit immediately before each upstream `urlopen`, so a 429 backoff retry counts again and a connection failure after dispatch counts — one rule, no pre-dispatch exempt category. The lifecycle fails closed on every branch: per-unit atomic persistence BEFORE dispatch (a persistence error kills the proxy), and a MISSING, corrupt, or limit-mismatched state file at startup aborts the proxy (verified in test) — deletion-then-restart cannot reset to zero; a genuinely NEW loop is declared via a fresh state file path (new OVERNIGHT_TAG). The proxy also pins the request model field to the declared proposer model. Aggregation: each loop produces ONE scored snapshot; the loop's score is its primary count; the formal result is the median of the >=3 per-loop scores per arm (zero-valid snapshots are VALID results: score 0, included in the median). Judge protocol per snapshot: (1) budget reconciliation gate PLUS provider-side dispatch cross-check (`dispatch_reconcile`): the snapshot must carry the proxy's `dispatch.jsonl` ledger (per-dispatch prompt hash, provider-reported token usage, output hash — written only by the proxy process); the gate forces primary score 0 when the ledger is missing, has fewer entries than the log chain's final count (logged dispatches without provider trace), or a majority of successful entries lack provider usage — a fabricated self-consistent log no longer suffices because the provider-side token trail must corroborate it; (2) `lake env lean` re-verification under the Judge container's network allowlist with a credential-scrubbed subprocess environment; (2) `lake env lean` re-verification under the Judge container's network allowlist with a credential-scrubbed subprocess environment; (3) `#print axioms` dependency check bound to the candidate's declared name; only Lean's four standard Prover axioms allowed; (4) triviality gate; (5) novelty adjudication with hybrid retrieval — RRF(semantic+lexical FTS) feeding the judge, plus CROSS-CANDIDATE dedup: every NOVEL lemma is re-adjudicated against the earlier NOVEL lemmas of the same snapshot; canonical-form duplicates are marked DUPLICATE and score 0. INFRA semantics: an unlaunchable compile stage (toolchain missing) is INFRA — unscored, excluded from all secondary rates; Work-side calls already spent are consumed (real dispatches, no refund). Candidate-only evaluation. |
| Evaluation | Evaluation mode and input | Direct evaluation of the submitted snapshot (lemma set + logs). No retraining anywhere in the task. |
| Evaluation | Reward or score definition | Primary: count of lemmas passing budget reconciliation, provider-dispatch cross-check, Judge re-verification, axiom policy, AND novelty adjudication (direction: higher; unit: lemmas; aggregation: median across ≥3 loops per arm). The Judge writes `/logs/verifier/reward.json` = `{"primary_novel_count": <int>}` (numeric, finite; forced to 0 when reconciliation fails). **Within-snapshot dedup rule**: canonical form = whitespace-canonicalized with the declared name dropped and every identifier mapped to a positional placeholder by first occurrence — statements identical up to alpha-renaming collapse to one key; later duplicates of an in-snapshot NOVEL lemma are marked DUPLICATE and contribute exactly 0; every NOVEL lemma is additionally re-adjudicated against earlier NOVEL lemmas of the same snapshot. Secondary: restatement rate, triviality rate, invalid rate, duplicate rate — over SCOREABLE entries only (INFRA excluded), reported alongside. Invalid-lemma semantics: failing any gate = excluded from primary count, counted in the secondary invalid rate; a zero-valid snapshot = valid score-0 result. |
| Evaluation | Feedback visible to the agent | Per round: compile success/failure with the full compiler error text, axiom-policy violations if any, gate decisions with reasons, running admitted-lemma tally, per-round budget spend (`calls_before`/`calls_after`) and remaining call budget. |
| Evaluation | Evaluation information hidden from the agent | Judge novelty verdicts during the run (the agent must not optimize against the judge), the held-out restatement probe set (post-hoc audit of Judge novelty-adjudication reliability only — never gates admission, scoring, or the reward). **Visibility**: judge_score.py ships in the repository for audit; inside Work it is mounted READ-ONLY — "hidden" means runtime verdicts are withheld from agent feedback, not that the code is secret. **Allowed axioms enumerated**: propext, Classical.choice, Quot.sound, Lean.ofReduceBool; any other dependency = FAIL (checked at Work-side admission AND at Judge time). **Fixed adjudication rules**: statement text sanitized (instruction-stripping), delimited as data; judge names the content first, then verdict; verdict read ANCHORED at the head of the reply (startswith on the uppercased first 40 chars — later mentions of either word inside reasoning text cannot flip it); unrecognizable = conservative RESTATEMENT. **Non-triviality rule**: `: True`/`: False` statements are RESTATEMENT-class before adjudication. **Judge provider**: DeepSeek official API (deepseek-flash, temp 0, current V4-era model — deepseek-chat was retired 2026-07-24) — different family AND provider from the proposer (GLM on Volcano ARK). |
| Evaluation | Measures preventing reward hacking | (1) Judge re-verifies every lemma from source in a fresh environment; (2) `#print axioms` dependency check bound to the candidate's declared theorem name — enforced at Work-side admission AND re-checked by the Judge; (2b) execution-surface restriction: the Judge container's network allowlist admits only the DeepSeek adjudication endpoint; the compile subprocess env is scrubbed of every credential-bearing variable; `unshare -rn` is applied as OPTIONAL second-layer hardening when the runtime permits (availability probed; failure is a supported route — the active isolation level is recorded in report.json `compile_isolation`); the executable-content screen bans `set_option` kernel-check overrides (`debug.skipKernelTC`, `checkBinderAnnotations false`), `macro`/`elab`/`run_cmd`/`IO`/`#eval`/`#check`/`#print` tokens; (3) **the novelty adjudicator is DeepSeek deepseek-flash (temp 0) — a different model family AND provider than the proposer (GLM on Volcano ARK)**, over a Judge allowlist containing ONLY api.deepseek.com; (4) candidate and neighbor text sanitized and delimited as data; (5) snapshot diff audit; (6) JSONL completeness and replayability; (7) **budget-reconciliation gate** (see Fixed evaluation protocol): unauditable, over-budget, or provenance-broken snapshots score 0. Residual limitations, stated: Judge uses the Work snapshot (shared-environment model, not an independent clean Base); the compile subprocess shares the container filesystem (no-route + scrubbed env + token screen; full elaboration sandboxing is not implemented); the adjudicator is itself an LLM and imperfect — the restatement rate ships as a reported secondary metric; the budget is audited, not cryptographically enforced (shared-root container; the harness's own Agent model shares this property). |
| Evaluation | Noise handling and meaningful improvement | ≥3 loops per arm, median aggregation. Pilot plausibility: compile-pass rates moved 7.7% → 45-67% across proposer configurations at n=20 rounds. Formal claims are made only on Judge-adjudicated net counts with per-loop spread. |
| Workspace | Is web search required? | No. |
| Workspace | May the agent use external services? | The AGENT may use exactly one service: the Volcano ARK LLM API (proposer, glm-5.3-flash effort=low) — reached through the loop's declared gateway, the local proxy (`ARK_BASE_URL=http://127.0.0.1:8080`; `ARK_PROXY_REQUIRED=1` makes the shipped client refuse any non-proxy proposer URL). **Honest boundary (v14): the agent runs as root in the Work container and could reach the allowlisted ARK endpoint directly — a secrecy boundary is not achievable in this container model, and none is claimed.** The budget contract is exclusion-based at scoring time (the reconciliation gate above), not secrecy-based: unaudited or over-budget snapshots score 0. The proxy counts every upstream attempt and pins the model field. Work's network allowlist names the real ARK endpoint (the harness iptables model always blocks loopback, so a loopback-only egress is not expressible — this supersedes every earlier loopback statement). **The JUDGE additionally uses the DeepSeek official API (deepseek-flash, temp 0) for novelty adjudication — Judge-side only, key injected only into the Judge container, never present in Work.** Enforced in task.toml as per-phase allowlists: `[agent] allowlist = ["ark.cn-beijing.volces.com"]`; `[verifier] allowlist = ["api.deepseek.com"]`; `[environment]` baseline `no-network`. Keys are host-side secrets (`${ARK_API_KEY}`, `${DEEPSEEK_API_KEY}`) injected at execution time and redacted from diagnostics. No web search, no other services. |
| Workspace | May the agent construct or collect additional data? | No additional external data. The agent may only append lemmas derived from the proposer. |
| Workspace | Leakage and reward-hacking safeguards | Seed domains sampled from files disjoint from any hint material; the proposer never sees Judge verdicts; the restatement probe set held out; verifier, gate code, scorer, proxy, and budget state read-only/protocol inside Work; snapshot diff audit on submission; reconciliation gate at scoring. |
| Theoretical & empirical foundations | flymemory (form law, anchoring, eviction), intuition-mechanism (shadow theorem, CV gate, evidence hierarchy), mbn (fixation/spacing/retention/no-savings), flypoet (k-WTA 25%) -- gate design rationale and cross-scale corroboration; see repos |
| Task-Generation Readiness | Contributor-owned decisions (all made) | (1) Reference artifact: baseline_snapshot/ (materialized, 18 lemmas). (2) Baseline matching under strategy change: strategy evolution only BETWEEN loops, identically in both arms (runner reads both configs from one file). (3) Aggregation: median across >=3 loops per arm. (4) Invalid semantics: invalid lemma = excluded from primary count + counted in the secondary invalid rate; zero-valid snapshot = valid score-0 result; unlaunchable compile stage = INFRA (unscored, excluded from rates); already-spent Work-side calls are consumed and not refunded. (5) Judge novelty model: DeepSeek official API (deepseek-flash, temp 0) — different family AND provider from the proposer; client inline in judge_score.py, key from `DEEPSEEK_API_KEY` injected via `[verifier.env]`. (6) Executable-content boundary — IMPLEMENTED: task-level allowlist denies the compile stage all network except the adjudication endpoint; credential-scrubbed compile env; token screen; `unshare -rn` optional hardening with import-time probe (level recorded in report.json `compile_isolation`). (6b) Budget lifecycle — FAIL-CLOSED IMPLEMENTED: per-unit atomic persistence before dispatch; missing/corrupt/limit-mismatched state aborts startup (missing = refuse to start, verified); no reset command in the CLI (a new loop = new OVERNIGHT_TAG = fresh state path). (6c) Budget reconciliation — IMPLEMENTED in the Judge: five rejection rules above, tested (honest chain accepted; backwards chain, over-budget, missing log rejected); failure forces primary score 0 with the reason in report.json. (6d) Provider-side dispatch attestation — IMPLEMENTED: ark_proxy.py appends an agent-unwritable ledger (prompt hash, provider-reported input/output/total tokens from the ARK Responses `usage` object, output text hash) per upstream dispatch; the runner copies the ledger into the snapshot; the Judge's `dispatch_reconcile` gate cross-checks ledger-vs-log-chain and forces score 0 on missing/short/usage-less ledgers. (7) Within-snapshot dedup — IMPLEMENTED twice: canonical-form duplicate marking (alpha-renaming invariant) AND cross-candidate re-adjudication; duplicates score 0. (8) Reward output: `/logs/verifier/reward.json` with the numeric primary score. |
| Compute Feasibility | Compute resources per single experiment run | CPU-only. Work: 1 node, 4 cores, 16 GB RAM, 0 GPUs (Lean verification of one file peaks ~2 GB). Judge: same profile, ~2 GB peak. External: proposer + judge API calls only. Fits one physical node, zero GPUs. |
| Compute Feasibility | Estimated runtime per single experiment run | The loop terminates at budget exhaustion or the wall-clock deadline (--deadline-h is a first-class CLI flag; formal launches pass a value covering the full 60-dispatch budget). Measured basis: same-day pilots at ~6 min/round with 1-3 dispatches per round; at 60 dispatches per loop, one loop is ~2 h Work + ~0.5 h Judge (serial; not additive). **Formal vs descriptive outcome (v15, sized to fit)**: the formal comparison requires >=3 loops per arm (=6 total). At 60 dispatches per loop (~2 h Work + ~0.5 h Judge each, serial), six loops total ~15 h including Judge — comfortably inside the 48h window, so the scoreable formal comparison is the DEFAULT deliverable; only an infrastructure failure falls back to a labeled DESCRIPTIVE REPORT (per-loop snapshots, no median-based formal claim). Both outcomes are declared in advance. |
| Compute Feasibility | Early-stopping signals / lower-cost proxy experiments | If both arms produce zero Judge-verified lemmas for 3 consecutive loops, the seed-domain sampler is re-drawn (recorded); otherwise run to budget exhaustion. |
| Compute Feasibility | (review item) Replacement/retry accounting | Feedback retries: each retry call consumes 1 budget unit. The proxy counts a unit immediately before each upstream `urlopen` — at that point the request is dispatched-by-construction, so transport failures after dispatch AND connect-time failures both count (one uniform rule, no pre-dispatch exempt category). 429 backoff retries count again. Resampling of an already-scored snapshot: not performed. INFRA snapshots: already-spent Work-side calls are consumed and not refunded. |
| Compute Feasibility | (review item) Arm-strategy matching | The agent's editable surface (prompt assembly, retry strategy) is FROZEN to the same implementation in both arms for the formal comparison; strategy evolution only between loops, identically in both arms (shared runner code; the gate flag is the sole arm difference). |

## CHANGELOG (v16 — responses to the 2026-10-08 08:40 review + the
## contributor tree audit)

1. **Provider-side dispatch attestation implemented** (Evaluation
   Integrity + Data and Network fails): the proxy appends an
   agent-unwritable ledger of every upstream dispatch — prompt hash,
   provider-reported token usage (ARK Responses `usage` object,
   verified against the live API), output text hash. The snapshot
   must carry it; the Judge's `dispatch_reconcile` gate cross-checks
   the ledger against the log spend chain (entries >= chain final,
   usage present) and forces primary score 0 otherwise. A fabricated
   self-consistent log no longer suffices: the provider-side token
   trail must corroborate it. Remaining residual (declared): the
   content binding is log-level, and a root agent can still read the
   credential — a rubric-level clarification with three implementable
   resolutions has been posted to the maintainers.
2. **Arm switch actually landed this time** (Readiness fail): the
   08:40 review correctly caught that the v15 prose claimed
   SELFLEARNER_ARM switches the axiom gate but the edit had not
   landed in propose_check.py. It has now (check_candidate runs
   axiom_ok only in the gated arm); control = genuinely compile-only,
   Judge axiom policy uniform for both arms.
3. **baseline_snapshot/ = REFERENCE-ONLY** (Traceable Baseline):
   declared not-scoreable (no spend chain); the scored control is
   produced fresh under the full protocol. Additionally, a fresh
   scored gated reference (baseline_v2) will be produced with the
   v16 protocol before the formal loops and committed with its
   log.jsonl + dispatch.jsonl.

## CHANGELOG (v15 — responses to the 2026-10-08 05:52 review + the
## contributor tree audit)

1. **Pin verified against the implementation** (Source Repository +
   Evaluation Integrity): the 05:52 review inspected a tree that
   predated the reconciliation gate. v15's pin points at the commit
   that carries the gate (`budget_reconcile()` in
   openrsi-proposal/task/tests/judge_score.py, invoked before
   scoring; fail-closed wrapper writes reward.json=0 on ANY uncaught
   error), verified by `git grep` at the pinned SHA.
2. **Arm switch aligned** (Readiness fail): the control arm is now
   genuinely compile-only — SELFLEARNER_ARM=control disables the
   axiom gate AND the novelty gate together (previously the axiom
   gate ran unconditionally, contaminating the control). The Judge's
   axiom policy remains a uniform measurement floor for both arms.
3. **Baseline declared REFERENCE-ONLY** (Traceable Baseline fail):
   baseline_snapshot/ predates the reconciliation gate and carries no
   spend chain; it is NOT submitted for scoring and earns nothing.
   The formal comparison uses fresh Work-produced controls
   (SELFLEARNER_ARM=control) scored under the full protocol.
4. **Formal comparison sized to the window** (Compute + Readiness):
   the declared per-loop budget is 60 dispatches; six loops
   (~15 h including Judge) fit inside 48h, making the scoreable
   formal comparison the DEFAULT deliverable.
5. **Repo hygiene for reliable bundle fetches**: 53 one-off scripts
   moved to attic/, __pycache__ untracked, README rewritten to match
   the deliverable, MIT LICENSE added, MANIFEST.sha256 lists the 18
   task-relevant files with checksums (a bundle missing files can now
   be distinguished from a repo missing files).
6. **Credential injection removed from agent.env** (Data and Network):
   ARK_API_KEY no longer appears in [agent.env]; the runner forwards
   it only to the proxy process's own environment.
7. **Adjudication anchored**: the verdict word is read from the head
   of the judge reply (startswith, first 40 chars); in-reasoning
   mentions cannot flip the verdict.

## CHANGELOG (v14 — responses to the 2026-10-08 05:20 review)

1. **Budget contract made honest and exclusion-based** (Evaluation
   Integrity + Data and Network fails): v13's "audit-grade" framing
   claimed the calls_before/after chain could detect direct provider
   requests — the review correctly showed it cannot, and that
   re-verification does not repair a budget breach. v14 stops
   claiming detection: the budget is a protocol parameter whose
   execution is audited, and the ENFORCEMENT is exclusion at scoring
   time — the Judge's new `budget_reconcile()` gate forces the
   primary score to 0 for snapshots with a missing/unreadable log, a
   broken or non-monotonic spend chain, a final count over the
   declared budget, or admitted lemmas with no proposing round
   (implemented and unit-tested: honest chain accepted; backwards,
   over-budget, and missing-log rejected). The shared-root secrecy
   impossibility is stated plainly and matched to the harness's own
   Agent model (provider key in the container environment).
2. **Pin restored to single-commit semantics** (Source Repository +
   Traceable Baseline fails): the v13 "content snapshot" framing
   (763c85b authoritative, later prose edits not re-pinned) left
   implementation provenance unresolved. The pin is now the complete
   self-contained v14 implementation commit; only proposal prose
   changes after it, and the row says so explicitly.
3. **Loopback statements fully removed** (Source Repository fail):
   the v12/v13 bodies still carried v11-era loopback-only claims
   that contradicted the real-endpoint allowlist. All such text is
   superseded; the allowlist rows match task.toml exactly.
4. **Formal vs descriptive outcome distinguished** (Readiness
   fail): the 48h-window deliverable is explicitly labeled — a
   DESCRIPTIVE REPORT (no median-based formal claim) when fewer
   than 3 loops per arm complete, and the scoreable formal
   comparison only at >=3 per arm. Both outcomes are declared in
   advance.
5. **Superseded scorer stays removed; launcher contradictions stay
   fixed** (carried from v13): no `judge_adjudicate.py` in the tree,
   no reset command in the CLI, `--deadline-h` first-class.

## Earlier revisions

- v13 (2026-10-08): Work-side axiom admission gate, missing-state
  refuse-to-start, reset command removed, --deadline-h flag, honest
  credential boundary (superseded by v14's exclusion-based contract).
- v12 (2026-10-08): proxy as credentialed client, fail-closed
  lifecycle, superseded scorer removed.
- v11 (2026-10-08): mandatory proxy, unshare demoted to optional
  hardening, uniform dispatch accounting, bare-SHA pin.
- v10 (2026-10-08): transport-layer counter, scorer/contract match,
  legal per-phase allowlists, tests/test.sh + environment definition.
- v2 (2026-10-06): axiom policy, counter, judge API boundary, arm
  matching, compute arithmetic, repository completeness.

## Retry history

2026-10-06 overnight failure (episode 37491258007, fourth attempt
across 17 hours, no content changes). 2026-10-07: six rubric reviews
(bundled-fetch asterisk bug + v2-era fails). 2026-10-08 04:26: tag
unresolvable, helper-only counter, accounting contradiction, unshare
compatibility. 2026-10-08 04:50: proxy egress contradiction,
credential boundary, budget lifecycle. 2026-10-08 05:10: network text
contradiction, root-readable key, missing-state branch, Work-side
axiom gate. 2026-10-08 05:20: proxy non-auditability, pin semantics,
48h outcome ambiguity — all addressed in this v14.

## Metric definitions (v17 preview — reviewer-guided refinement)

Three complementary indicators, pre-registered:

| metric | question answered | role |
|---|---|---|
| verification yield | fraction of generated candidates passing independent formal verification | correctness of the funnel |
| novel-yield rate | new, non-trivial, verified theorems per 100 real proposer dispatches | primary (budget-normalized) |
| knowledge-growth efficiency | net reusable theorems per wall-clock hour / per USD | cost-normalized secondary |

Novelty is adjudicated in three layers, with the third layer's error
rate measured (not assumed):
1. syntax/canonicalization dedup (exact + alpha-renamed duplicates);
2. in-library similarity screen (restatements, equivalent formulations,
   simple corollaries via RRF lexical+semantic retrieval);
3. substantive-novelty adjudication (LLM judge over structure evidence)
   — the judge is NOT treated as ground truth: a held-out probe set
   plus human spot-checks measure its misjudgment rate, reported as
   part of the results.

