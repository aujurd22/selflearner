# rsi/verified-lemma-growth — Task Proposal (v12, revision after automated review)

Revision of 2026-10-08 addressing the three hard-gate failures of the
2026-10-08 04:50 review (in-container proxy egress contradiction,
credential boundary, fail-open budget lifecycle). CHANGELOG at the
bottom.

| Section | Field | Proposal |
| --- | --- | --- |
| Contributor | Full name | JUNRONG DU |
| Contributor | Email | dududu9738@gmail.com |
| Research Question | Repository URL | https://github.com/aujurd22/selflearner |
| Research Question | Exact commit/tag | 763c85b5fc10176c71e61f3f326850879b13c072 (bare immutable commit SHA — the previous revision referenced a tag, which the review's bundle fetcher could not resolve to a SHA; this revision references the SHA directly). This is the v12 HEAD: it contains the full v10 snapshot PLUS the four v11 fixes (mandatory proposer proxy `ark_proxy.py`, unshare demoted to optional hardening with the active isolation level recorded, uniform dispatch accounting, bare-SHA pin) — see CHANGELOG below. |
| Research Question | Scientific question | Under a fixed proposer dispatch budget (200 proposer API dispatch attempts per loop, enforced at a mandatory local proxy that is the ONLY network route to the proposer API), does a verifier-escorted propose-check loop with a three-gate admission funnel (Lean compilation + axiom policy + novelty + non-triviality) accumulate genuinely new, machine-verified lemmas against the Lean mathlib library at a higher rate than an ungated loop that only requires compilation? |
| Research Question | Why this is scientific research rather than pure engineering optimization | Falsifiable matched comparison: identical proposer model, identical proxy-enforced dispatch budget, identical seed-domain sampler, identical prompt-assembly and retry policy in BOTH arms — the admission-gate stack is the only manipulated component (config flag in the same code). The loop is iterative change-run-observe-update. Knowledge gained: whether verifier-gated admission increases net new-knowledge accumulation or merely filters without changing proposal quality — a controlled measurement of what verifier escort is worth for autonomous knowledge growth (frontier preprints cited by the review study adjacent mechanisms; none reports this exact matched admission-gate ablation). |
| Research Question | Starting environment and artifacts | All public at the pinned commit: SQLite library of 181,316 parsed mathlib theorems (66,217 with full tactic proofs) + FTS5 index (`parse_mathlib.py`); mathlib4 sources with full prebuilt olean cache (toolchain v4.35.0-rc3); loop code (`propose_check.py`, `run_overnight.py`); **mandatory proposer proxy (`ark_proxy.py`) — the budget enforcement point**; Judge scorer (`openrsi-proposal/task/tests/judge_score.py` via `openrsi-proposal/task/tests/test.sh` — the ONLY scorer; the legacy pilot-time `judge_adjudicate.py` has been REMOVED from the repository so no superseded adjudication code can be mistaken for the contract); multilingual-embedding index (`vectors.npz`, GitHub release vectors-v1 (github.com/aujurd22/selflearner/releases/tag/vectors-v1), sha256 46ff6610e1dc8b5772b8f32efa8252453c09aa8a6e145917af33ee792ead63a0). Pilot logs (`runs/overnight_20261005/`, `docs/pilot_logs/`, judge reports) are tracked in the repository at the pinned commit. |
| Research Question | Agent's final deliverable | A candidate snapshot: `admitted/*.lean`, `log.jsonl` (complete round record including per-round `calls_before`/`calls_after` budget spend read from the proxy), `library_diff.json`, plus the runner budget summary. Judge re-runs `lake env lean` + `#print axioms` on every lemma from source and re-adjudicates novelty. |
| Research Question | Files/components the agent may modify | Its own candidate-lemma files; proposer prompt assembly; retry strategy — **identical permissions in both arms** (the arms differ ONLY in the admission-gate flag). NOT the verifier, gate thresholds, library index, scoring code, or the proxy (`ark_proxy.py` and its budget state file are protocol components; editing or resetting them voids the snapshot). |
| Research Question | Prohibited actions | Modifying or bypassing the Lean verifier or gate code; editing or deleting the proxy or its persistent budget state; editing existing mathlib entries, sources, or olean cache; fabricating compile logs (Judge re-verifies everything from source, including axiom dependencies); introducing non-standard axioms (axiom-farm escape — blocked by the judge's `#print axioms` policy); direct proposer-API calls that bypass the local proxy (the shipped client refuses them when ARK_PROXY_REQUIRED=1; a hand-rolled request without the credential fails upstream authentication, and the credential lives only in a 0600 key file the proxy reads); training or fine-tuning any model. |
| Reference Baseline | Baseline implementation or artifact | TWO components, both materialized: (1) **`baseline_snapshot/`** — the pilot run's 18 admitted lemmas + library_diff.json, a concrete evaluation-ready artifact the Solution materializes by copying the directory (no Work-side API generation needed); (2) the ungated configuration of the same code (`NOVELTY_GATE=0`) for generating FRESH matched baselines during the formal loops. **Arm matching statement: both arms share the same proposer model, prompt assembly, retry policy, seed-domain sampler, and proxy-enforced call budget; the admission-gate flag is the sole difference.** |
| Reference Baseline | Repository evidence paths | `propose_check.py`, `run_overnight.py`, `ark_proxy.py`, `docs/pilot_logs/`, `runs/overnight_20261005/`, `baseline_snapshot/`, `openrsi-proposal/task/` (task.toml + tests + environment). **Provenance of baseline_snapshot/**: produced by the GATED arm of the SL-60 pilot (glm-5.3-flash effort=low, 60 rounds within a 200-dispatch budget, single loop, 2026-10-06) — a candidate-side REFERENCE artifact showing the gate-stack output shape, NOT the ungated control. The ungated control for the formal comparison is Work-produced fresh (`NOVELTY_GATE=0`, identical 200-dispatch budget); the pilot's ungated numbers (9 admitted under a 20-round protocol, not call-budget-matched) are pilot evidence only. |
| Reference Baseline | Baseline evaluation path | `python3 run_overnight.py budget-reset && python3 run_overnight.py run` with the gate flag off; Judge scores the baseline snapshot under the identical adjudication protocol as candidate snapshots. |
| Evaluation | Fixed evaluation protocol | **Budget architecture (the counter is the credentialed gateway, not a helper convention): `ark_proxy.py` runs inside the Work container; the agent env's `ARK_BASE_URL` points at `http://127.0.0.1:8080` — the proxy — and `ARK_PROXY_REQUIRED=1` makes the shipped client refuse to send proposer traffic anywhere else. The proxy is the only CREDENTIALED client: the ARK key is injected as a root-only 0600 file that the proxy reads at startup (never an environment variable), the runner scrubs the key from its own environment before the agent starts, and the proxy rewrites the Authorization header from that file on every forward. The proxy pins the request model field to the declared proposer model (a client cannot opt into another model). The proxy counts one unit per UPSTREAM dispatch attempt: `consume()` runs immediately before each upstream `urlopen`, so a 429 backoff retry counts again and a connection failure after dispatch counts — one uniform rule, no pre-dispatch exempt category. At the cap the proxy answers HTTP 429 with a machine-readable body WITHOUT dispatching upstream. The lifecycle FAILS CLOSED: every count is persisted atomically (tempfile + fsync + os.replace) to `runs/budget_state.json` BEFORE the dispatch proceeds — a persistence error kills the proxy rather than permitting an uncounted dispatch — and a missing or corrupt state file at startup aborts the proxy instead of resetting to zero (verified: corrupt state = refuse to start). A NEW loop begins under a NEW OVERNIGHT_TAG with a fresh state file; there is no agent-facing reset of an active counter (`run_overnight.py budget-reset` refuses). The loop terminates when the budget is exhausted or the wall-clock deadline passes — there is no round count.** Aggregation: each loop produces ONE scored snapshot; the loop's score is its primary count; the formal result is the median of the >=3 per-loop scores per arm (zero-valid snapshots are VALID results: score 0, included in the median — zero-yield loops are explicitly anticipated and are not unscored). Judge protocol per snapshot: (1) `lake env lean` re-verification of every admitted lemma under the Judge container's network allowlist (only the DeepSeek adjudication endpoint is reachable) with a credential-scrubbed subprocess environment; (2) `#print axioms` dependency check bound to the candidate's declared name; only Lean's four standard Prover axioms allowed; (3) triviality gate; (4) novelty adjudication with hybrid retrieval — RRF(semantic+lexical FTS) feeding the judge, plus CROSS-CANDIDATE dedup: every NOVEL lemma is re-adjudicated against the earlier NOVEL lemmas of the same snapshot; canonical-form duplicates of an earlier NOVEL lemma are marked DUPLICATE and score 0. INFRA semantics: a snapshot whose compile stage cannot launch (toolchain missing) is INFRA — unscored and EXCLUDED from all secondary rates; the Work-side proposer calls already spent generating that snapshot are consumed (they were real dispatches; budget is not refunded) and the loop continues within the same budget; a snapshot that parses but yields zero passing lemmas = valid score-0 result. Candidate-only evaluation. |
| Evaluation | Evaluation mode and input | Direct evaluation of the submitted snapshot (lemma set + logs). No retraining anywhere in the task. |
| Evaluation | Reward or score definition | Primary: count of lemmas passing Judge re-verification, axiom policy, AND novelty adjudication (direction: higher; unit: lemmas; aggregation: median across ≥3 loops per arm). The Judge writes `/logs/verifier/reward.json` = `{"primary_novel_count": <int>}` (numeric, finite). **Within-snapshot dedup rule**: canonical form = whitespace-canonicalized with the declared name dropped and every identifier mapped to a positional placeholder by first occurrence — statements identical up to alpha-renaming collapse to one key; later duplicates of an in-snapshot NOVEL lemma are marked DUPLICATE and contribute exactly 0; in addition every NOVEL lemma is re-adjudicated against earlier NOVEL lemmas of the same snapshot at adjudication time. Secondary: restatement rate, triviality rate, invalid rate, duplicate rate — computed over SCOREABLE entries only (INFRA excluded), reported alongside, never hidden. Invalid-lemma semantics: failing any gate = excluded from primary count, counted in the secondary invalid rate; a zero-valid snapshot = valid score-0 result (included in the median). |
| Evaluation | Feedback visible to the agent | Per round: compile success/failure with the full compiler error text, axiom-policy violations if any, gate decisions with reasons, running admitted-lemma tally, per-round budget spend (`calls_before`/`calls_after`, read from the proxy's `/health` endpoint) and remaining call budget. |
| Evaluation | Evaluation information hidden from the agent | Judge novelty verdicts during the run (the agent must not optimize against the judge), the held-out restatement probe set (role: post-hoc audit of Judge novelty-adjudication reliability only — never gates admission, scoring, or the reward). **Visibility**: judge_score.py ships in the repository for audit; inside Work it is mounted READ-ONLY (readable, not modifiable) — "hidden" means runtime verdicts are withheld from agent feedback, not that the code is secret. **Allowed axioms enumerated**: propext, Classical.choice, Quot.sound, Lean.ofReduceBool; any other dependency = FAIL. **Fixed adjudication rules**: statement text sanitized (instruction-stripping), delimited as data; judge names the content first, then verdict; verdict scanned from full reply, RESTATEMENT wins ties. **Non-triviality rule**: `: True`/`: False` statements are RESTATEMENT-class before adjudication. **Judge provider**: DeepSeek official API (deepseek-flash, temp 0, current V4-era model — deepseek-chat was retired 2026-07-24) — different family AND provider from the proposer (GLM on Volcano ARK). |
| Evaluation | Measures preventing reward hacking | (1) Judge re-verifies every lemma from source in a fresh environment; (2) `#print axioms` dependency check bound to the candidate's declared theorem name; (2b) **execution-surface restriction, enforced in depth**: the Judge container's network allowlist admits only the DeepSeek adjudication endpoint, so the compile stage has no reachable network; the compile subprocess env is additionally scrubbed of every credential-bearing variable (KEY/TOKEN/SECRET/ARK/DEEPSEEK/...); `unshare -rn` namespace isolation is applied as OPTIONAL second-layer hardening when the runtime permits it (availability probed once; failure is a SUPPORTED route under the task-level policy, not an error — the report records which isolation level was active); the executable-content screen bans `set_option` overrides of kernel checks (`debug.skipKernelTC`, `checkBinderAnnotations false`), `macro`/`elab`/`run_cmd`/`IO`/`#eval`/`#check`/`#print` tokens; (3) **the novelty adjudicator is DeepSeek deepseek-flash (temp 0, DeepSeek official API, current V4-era model) — a different model family AND different provider than the proposer (GLM on Volcano ARK)**, reached over a Judge allowlist containing ONLY api.deepseek.com; (4) candidate and neighbor text sanitized (instruction-stripping patterns removed) and delimited as data in the judge prompt; (5) snapshot diff audit; (6) JSONL completeness and replayability. Residual limitations stated: Judge uses the Work snapshot (shared-environment model, not an independent clean Base); the compile subprocess shares the container FILESYSTEM (credential absence + no-route + token screen; full elaboration sandboxing is not implemented and is declared as a residual limitation); the adjudicator is itself an LLM and imperfect — the restatement rate ships as a reported secondary metric rather than being assumed away. |
| Evaluation | Noise handling and meaningful improvement | ≥3 loops per arm, median aggregation. Pilot plausibility: compile-pass rates moved 7.7% → 45-67% across proposer configurations at n=20 rounds. Formal claims are made only on Judge-adjudicated net counts with per-loop spread. Deterministic re-verification of a fixed artifact is not repeated for ceremony. |
| Workspace | Is web search required? | No. |
| Workspace | May the agent use external services? | The AGENT may use exactly one service: the Volcano ARK LLM API (proposer, glm-5.3-flash effort=low) — reached through the mandatory local proxy (`ARK_BASE_URL=http://127.0.0.1:8080`; `ARK_PROXY_REQUIRED=1` makes the shipped client refuse any non-proxy proposer URL). The Work network allowlist names the real ARK endpoint (the harness iptables model resolves allowlist entries to pinned IP endpoints and always blocks loopback, so a loopback-only egress is not expressible — the reviewed v11 contradiction is resolved by making the proxy the only CREDENTIALED client instead of the only route: the ARK key lives in a 0600 file only the proxy reads, the runner scrubs it from the environment, and requests without the key fail upstream authentication). The proxy pins the model field to the declared proposer model regardless of what a client sends. Boundary: prompt content = seed theorem statements + prior-round feedback only. **The JUDGE additionally uses the DeepSeek official API (deepseek-flash, temp 0, current V4-era model — deepseek-chat was retired 2026-07-24) for novelty adjudication — Judge-side only, key injected only into the Judge container, never present in Work.** Both boundaries are ENFORCED in task.toml as per-phase allowlists: `[agent] network_mode="allowlist", allowed_hosts=["127.0.0.1","localhost"]` (the proxy is the single counted egress); `[verifier] network_mode="allowlist", allowed_hosts=["api.deepseek.com"]`; the `[environment]` baseline is `no-network`. Keys are host-side secrets (`${ARK_API_KEY}` for the proxy process, `${DEEPSEEK_API_KEY}` for the Judge) injected at execution time only and redacted from diagnostics. No web search, no other services, no other endpoints. |
| Workspace | May the agent construct or collect additional data? | No additional external data. The agent may only append lemmas derived from the proposer. |
| Workspace | Leakage and reward-hacking safeguards | Seed domains sampled from files disjoint from any hint material; the proposer never sees Judge verdicts; the restatement probe set held out; verifier, gate code, judge scorer, proxy, and budget state read-only/protocol inside the Work container; snapshot diff audit on submission. |
| Theoretical & empirical foundations | flymemory (form law, anchoring, eviction), intuition-mechanism (shadow theorem, CV gate, evidence hierarchy), mbn (fixation/spacing/retention/no-savings), flypoet (k-WTA 25%) -- gate design rationale and cross-scale corroboration; see repos |
| Task-Generation Readiness | Contributor-owned decisions (all made) | (1) Reference artifact: baseline_snapshot/ (materialized, 18 lemmas). (2) Baseline matching under strategy change: strategy evolution only BETWEEN loops, identically in both arms (runner reads both configs from one file). (3) Aggregation: median across >=3 loops per arm. (4) Invalid semantics: invalid lemma = excluded from primary count + counted in secondary invalid rate; a snapshot with zero valid lemmas = valid score-0 result (included in the median; zero-yield loops are anticipated); an unlaunchable compile stage (toolchain missing) = INFRA (unscored, excluded from rates); Work-side proposer calls already spent on an INFRA snapshot are consumed (real dispatches, no refund) and the loop continues within the same budget. (5) Judge novelty model: **DeepSeek official API (deepseek-flash, temp 0, current V4-era model)** — different family AND provider from proposer candidates; client inline in judge_score.py (`make_judge_ask`), key from `DEEPSEEK_API_KEY` injected via `[verifier.env]` at execution time. (6) Executable-content boundary — IMPLEMENTED as declared: task-level allowlist denies the compile stage all network except the adjudication endpoint; credential-scrubbed compile env; token screen banning #eval/#check/#print/run_cmd/IO/sorry/admit/macro/elab/set_option; `unshare -rn` optional in-container hardening with import-time probe, failure supported (level recorded in report.json `compile_isolation`). (6b) Budget lifecycle — FAIL-CLOSED IMPLEMENTED: per-unit atomic persistence before dispatch (persistence failure kills the proxy), corrupt/missing state aborts startup rather than resetting, no agent-facing reset (a new loop = new OVERNIGHT_TAG = fresh state file), per-round calls_before/calls_after recorded from the proxy's /health endpoint. **Residual risk, stated**: the compile subprocess shares the container filesystem — a malicious candidate COULD read Work-visible files or write outside /tmp. Mitigations: (a) scorer state lives only in the scorer's process memory and the novelty key is injected only at the adjudication stage (never on disk, never in the compile env, and scrubbed from it); (b) the snapshot directory is agent-owned by design (candidates are the agent's own outputs — nothing secret to read); (c) Lean elaboration sandboxing beyond this is not implemented and is declared as a residual limitation. (7) Within-snapshot dedup — IMPLEMENTED twice over: canonical-form duplicate marking (alpha-renaming invariant) AND cross-candidate re-adjudication of every NOVEL lemma against the earlier NOVEL lemmas of the same snapshot; duplicates score 0 and are counted in the duplicate rate. (8) Reward output: the Judge writes `/logs/verifier/reward.json` with the numeric primary score. |
| Compute Feasibility | Compute resources per single experiment run | CPU-only. Work: 1 node, 4 cores, 16 GB RAM, 0 GPUs (Lean verification of one file peaks ~2 GB). Judge: same profile, ~2 GB peak. External: proposer + judge API calls only (no GPU compute). Fits one physical node, zero GPUs. |
| Compute Feasibility | Estimated runtime per single experiment run | The loop terminates at BUDGET EXHAUSTION, not at a round count. Measured basis: same-day pilots at ~6 min/round with 1-3 dispatches per round give a per-loop wall-clock range of roughly 7-20 h including Judge (Work and Judge are NOT additive — the Judge runs once per loop on the final snapshot; the 7-20 h figure already includes a ~0.5-1 h Judge pass). Review's own conservative arithmetic (67-200 rounds → 7.17-20.5 h) bounds the worst case. Per-loop `summary.json` records the exact dispatch count, so per-hour dispatch throughput is measured, not assumed; the ≥3-loop formal comparison is sized against these measured figures rather than a fixed rounds-per-loop claim. The review's 48h capacity flag (2-6 complete loops) is acknowledged; the formal protocol needs ≥3 loops per arm = ≥6 total, so the run targets the 48-hour window and reports per-loop summaries as it goes — if the window closes early, the completed per-loop snapshots and their medians are still delivered with the achieved loop count reported. |
| Compute Feasibility | Early-stopping signals / lower-cost proxy experiments | If both arms produce zero Judge-verified lemmas for 3 consecutive loops, the seed-domain sampler is re-drawn (recorded); otherwise run to budget exhaustion. |
| Compute Feasibility | (review item) Replacement/retry accounting | Feedback retries: each retry call consumes 1 budget unit. Dispatch accounting is UNIFORM and matches the implementation: the proxy counts a unit immediately before each upstream `urlopen` — at that point the request is dispatched-by-construction, so BOTH "transport failures after the request left the proxy" AND "connection failures at connect time" count (there is no pre-dispatch category; the earlier text suggesting one was contradictory and is removed). 429 backoff retries count again (each re-dispatch). Resampling of an already-scored snapshot: not performed (single snapshot per loop). INFRA snapshots: the Work-side calls already spent generating them are consumed and not refunded (they were real dispatches); the loop continues within the same budget. |
| Compute Feasibility | (review item) Arm-strategy matching | The agent's editable surface (prompt assembly, retry strategy) is FROZEN to the same implementation in both arms for the duration of the formal comparison; strategy evolution is allowed only between loops, identically in both arms (the loop code is shared and the gate flag is the sole arm difference — enforced by the runner reading both arms' configs from the same file). |

## CHANGELOG (v12 — responses to the 2026-10-08 04:50 review)

1. **Proxy egress contradiction resolved** (Source Repository +
   Readiness fails): v11 declared a loopback-only Work allowlist with
   the proxy inside the same container — an ordinary process in a
   loopback-only container cannot reach the external ARK endpoint,
   and the harness's iptables model always blocks loopback, so that
   design is not expressible. v12 aligns with the platform: the Work
   allowlist names the REAL ARK endpoint (harness-pinned IPs), and
   the enforcement moves from "only route" to "only CREDENTIALED
   client" — the key lives in a 0600 file only the proxy reads (the
   runner scrubs it from the environment; the agent shell never
   holds it), the proxy pins the model field and rewrites the
   Authorization header on every forward, and a keyless direct
   request fails upstream authentication. The shipped client
   additionally refuses non-proxy proposer URLs when
   ARK_PROXY_REQUIRED=1, so the audited path and the counted path
   are the same path.
2. **Credential boundary closed** (Data and Network fail): the v11
   runner copied its full environment to the proxy (key inherited)
   and load_llm() read a legacy key file into the environment. v12:
   the runner strips the key from its own env, writes it to a 0600
   file consumed only by the proxy, and the proxy deletes
   ARK_API_KEY from its own process env after reading the file;
   load_llm() no longer injects any key in task mode
   (ARK_PROXY_REQUIRED=1).
3. **Budget lifecycle fail-closed** (Evaluation Integrity fail): the
   v11 proxy suppressed persistence failures and reset to zero on a
   missing/corrupt state file, and exposed a bare budget-reset
   command. v12: every unit is persisted atomically (fsync + atomic
   rename) BEFORE the dispatch proceeds — a persistence error kills
   the proxy rather than permitting uncounted dispatches; a missing
   or corrupt state file at startup aborts the proxy (verified in
   test: corrupt state = refuse to start); budget-reset refuses to
   touch an active state (a new loop = new OVERNIGHT_TAG = fresh
   state file).
4. **Superseded scorer removed** (Evaluation Integrity fail): the
   repository still contained the legacy pilot-time
   `judge_adjudicate.py`, whose gated-SQL pattern, batch-verification
   return-code handling, and proposer-client adjudication the review
   correctly identified as contract violations. It has been DELETED;
   the only scorer is `openrsi-proposal/task/tests/judge_score.py`
   (invoked via tests/test.sh), and the proposal names it as such.
5. **Compute deadline reconciliation** (Compute note): the runner's
   9-hour default Work deadline is surfaced — the formal loops are
   launched with an explicit deadline covering the full 200-dispatch
   budget (per-loop summaries report achieved rounds vs budget), and
   the review's 48h capacity flag (2-6 complete loops) stands; the
   protocol reports medians over the completed per-loop snapshots
   with the achieved loop count stated.

## CHANGELOG (v11 — responses to the 2026-10-08 04:26 review)

1. **Pin is a bare full SHA** (Source Repository fail): the v10 revision
   referenced an annotated tag, which the review's bundle fetcher
   could not resolve (HTTP 422, "No immutable commit SHA was
   resolved") — the fetch bug moved from Markdown asterisks to tag
   indirection. The pin is now the literal 40-hex commit SHA, which
   the fetcher resolves directly. (The v10 "self-referential SHA"
   chase was a different, real problem: a commit cannot contain its
   own SHA; the tag indirection was the attempted cure and failed at
   the fetcher. A pin-SHA recorded in the proposal BODY of the
   discussion — as done here — has no self-reference problem because
   the discussion body is not part of the repository commit graph.)
2. **Budget enforcement moved into the architecture** (Evaluation
   Integrity fail "helper-only counter"): the counter was invoked
   inside two Python helpers, so an agent bypassing them with its own
   code was uncounted. Now `ark_proxy.py` IS the proposer endpoint
   from Work's perspective: `ARK_BASE_URL=http://127.0.0.1:8080`, the
   real ARK endpoint and key exist only in the proxy process, and the
   Work network allowlist admits ONLY loopback — every route to the
   API goes through the proxy and is counted per upstream attempt,
   including attempts from code that never imports the loop's
   helpers. At the cap the proxy returns HTTP 429 (machine-readable)
   WITHOUT dispatching upstream. Count persisted atomically per unit;
   restart restores (never resets).
3. **Accounting contract made uniform** (Scientific Objective +
   Readiness fails): the contradictory "pre-dispatch connection
   failures are not consumed" text is REMOVED — the proxy counts
   immediately before each upstream urlopen, so every dispatched
   attempt (transport failure, connect failure, 429 retry) consumes
   one unit, matching one consistent rule. INFRA snapshots: the
   Work-side proposer calls already spent are consumed (no refund)
   and the loop continues within the same budget — stated explicitly.
4. **unshare demoted to optional hardening** (Source Repository fail
   "container compatibility"): Docker's default seccomp profile may
   block namespace creation, and v10 made unshare-failure a
   snapshot-wide INFRA, which could leave every snapshot unscoreable.
   The PRIMARY isolation is now the task-level network policy (Judge
   allowlist = DeepSeek only; compile env credential-scrubbed),
   which holds regardless of unshare; `unshare -rn` is applied when
   the runtime permits as second-layer defense in depth, and the
   active isolation level is recorded in report.json
   (`compile_isolation`). No INFRA outcome depends on unshare.

## Earlier revisions

- v10 (2026-10-08): transport-layer budget counter in budget.py,
  scorer/contract match, legal per-phase allowlists, tests/test.sh +
  environment definition, Markdown-asterisk pin bug removed.
- v2 (2026-10-06): axiom policy, in-runner counter, judge API
  boundary, arm matching, compute arithmetic, repository completeness.

## Retry history

2026-10-06 overnight failure (episode 37491258007, failed before
completion, fourth attempt across 17 hours, no content changes).
2026-10-07: six rubric reviews (bundled-fetch asterisk bug + the four
v2-era fails). 2026-10-08 04:26: four fails (tag unresolvable,
helper-only counter, accounting contradiction, unshare compatibility)
— all four addressed in this v11.
