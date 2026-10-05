# Selflearner A/B adjudication — the day the novelty gate met its judge

**Date**: 2026-10-05 evening. Two arms × 20 rounds, identical proposer
(glm-5.3-flash effort=low, compile-error feedback retries), identical
budget. Gated arm = three-gate admission; ungated arm = compile-pass =
admit. Judge (independent): batch Lean re-verification + v2.5 hybrid
retrieval (RRF semantic+lexical) + naming-step LLM adjudication.

## Headline (honest): net novel growth = 0 in BOTH arms

All 19 admitted lemmas across both arms were adjudicated
**restatement or trivial** by the v2.5 judge (cross-checked by hand:
add_zero / zero_add / limsup special cases / interior-Nonempty
definition / pushforward-measure definition — every one is a
textbook-level restatement of existing mathlib content). The library
was rolled back to 181,309 with 16 tombstones (the retracted table
keeps names + reasons; 3 duplicates collapse onto the same names).

The gate's demonstrated value is therefore **contamination blocking,
not growth creation**:
- ungated arm admitted `add_zero` (name collision with mathlib,
  compile-void under re-verification), a `True := trivial`, and 4
  textbook restatements;
- gated arm blocked that entire class (4 name-collision and 2
  triviality rejections in the pilot) but its survivors were still
  restatements at the mathematical level.

## Why the proposer produces only restatements

glm-5.3-flash seeded with random mathlib files proposes the "shape" of
a textbook fact adjacent to the seeds. At effort=low it cannot do
original mathematics; at minimal it cannot even compile (7.7%). The
bottleneck is proposal quality, and no gate can create information the
proposer lacks.

## Judge v2.5 lessons (each paid for)

1. Semantic-only retrieval misses textbook restatements: 8
   `n + 0 = n`-shaped lemmas passed a cosine-0.93 gate across both
   arms; embeddings cannot separate a new lemma from same-topic
   neighbors (0.85 novel vs 0.84 restated). Fix shipped: hybrid
   RRF(semantic, lexical-FTS) retrieval + a naming-step prompt
   ("name the content first, then ask if mathlib has that theorem").
   Post-fix adjudication caught all 8 — including IsCyclic, which the
   v1 judge had passed and hand-review had also passed; the v2.5
   retrieval surfaced IsCyclic.ext and the naming step exposed the
   lemma as a specialization. **The judge out-adjudicated the human
   review.**
2. Batch Lean re-verification (one `lake env lean` for all lemmas) —
   per-lemma invocations were timing out under load.
3. Verdict parsing must scan the whole reply (the naming-step prompt
   puts the verdict word mid-text), and RESTATEMENT wins ties.

## Consequences

- Proposal pilot numbers (OpenRSI #177) updated by comment: pilot
  net growth is 0/0; the task's value claim rests on contamination
  blocking + the measurement infrastructure, and the honest zero is
  part of the package. If the community wants a nonzero-growth task,
  the proposer model is the knob, not the gates.
- The gate stack is worth keeping exactly as built: it is what makes
  a future stronger proposer SAFE to hook in. Gates do not create
  knowledge; they make knowledge claims auditable.
- Next lever (pre-registered order): stronger proposer on the same
  harness (the only untested variable), then M7.8 verified-throughput.
