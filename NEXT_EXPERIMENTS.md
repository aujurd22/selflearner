# Next experiments — designed while tonight's runs cook

Written 2026-10-05 evening, per the standing objective (keep the boxes
busy; design the next experiment while the current one runs).

## Running now (status board)

| # | experiment | where | done by | adjudication |
|---|---|---|---|---|
| 1 | M6 delta retrieval, realization 1 (RUNSEED default) | local CPU, 2 arms | 02:30 | pre-reg v10i_m6: visit-k distribution first (k>=13 gate), then paired delta-vs-M5 |
| 2 | M6 delta retrieval, realization 2 (RUNSEED=20261006) | cloud CPU, 2 arms | ~02:30 | same, cross-realization replication (G4' rule) |
| 3 | spacing effect, gpt2 (spaced32/massed32/massed64/massed16) | cloud 5090 | ~2h | massed >= spaced => spacing effect DOES NOT hold in LLM fixation |
| 4 | spacing effect, mamba2 (massed32/massed64/spaced64) | local 4070S | ~2.5h | completes the 2x2 (architecture x arrangement) |
| 5 | selflearner overnight 60 rounds (gated v2) | cloud CPU | morning | contamination-block rate + (expected) ~0 net novel at this proposer |

## Queued designs

### N1. In-context vs in-weights (the EXPOSURE_FINDINGS follow-up)

The exposure-curve probe reads fixation from a 2-token prompt. A model
can "know" a fact in two different ways: baked into weights (what we
measured) or retrievable in-context. Measurement: for each tier's
checkpoint, probe the fact twice — (a) 2-token prompt (in-weights) and
(b) the fact's source story as context + question (in-context).
Prediction: gpt2's apparent zero fixation is partly IN-CONTEXT
knowledge that the 2-token probe cannot see; mamba2's in-context
channel is bounded by its fixed state. This turns the architecture
gap from "mamba2 fixes, gpt2 doesn't" into a two-channel decomposition
— a much stronger result. Cheap: inference-only, reuses all 18
checkpoints from tonight.

### N2. Interference/retention curve (exposure curve v2)

After fixation at r=64: keep training on clean TinyStories and measure
retention of the fixed facts over N further tokens. Question: what
washes fixations out — and does a fact fixed at 128 exposures survive
interference better than one fixed at 32 (overtraining dividend)?
Directly relevant to the selflearner: admitted lemmas are only useful
if they persist.

### N3. Curriculum position sweep (spacing, second axis)

Tonight's spacing arms put massed blocks at spread positions. Sweep
block POSITION (early vs late in the stream): does late-training
proximity to the end of the stream (less subsequent interference)
lower the fixation threshold? This is the "cram before the exam"
effect, and it confounds any exposure-curve run whose fact placement
is not position-controlled.

### N4. M7.8 verified-throughput (flyloop; blocked on M6 verdict)

M7.7 said in-loop derivation dies because history entries are
unverified. M7.8 = verify-at-identification: run the cheap verifier
on book_test-retrieved candidates at push time, so the derivation
history only ever contains verified entries. If M6 ACCEPTED, the
delta ledger joins the verified pool. This is the flyloop-side test
of the same lesson selflearner taught today: gates do not create
knowledge, they make knowledge claims auditable — the question is
whether auditable inputs raise downstream composition to nonzero.

## Standing rules (carried forward)

- Numbers from verdict JSON / run counters, never console text.
- Paired contrasts same seed; replications new seed (RUNSEED split).
- Single-realization gains are downgraded, not accepted.
- Restatement/trivial gates stay on: today proved the proposer, not
  the gate, is the growth bottleneck — but a stronger proposer hooked
  into ungated admission would be unauditable.
