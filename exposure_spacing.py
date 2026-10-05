"""Spacing effect on parameter fixation: massed vs spaced repetition.

Follow-up to the exposure curve (2026-10-05): the local mamba2 run used
EVENLY-SPACED repetitions and found the fixation threshold at 16-32
repetitions (train_acc1 0.24 -> 0.91). This experiment isolates the
ARRANGEMENT variable: same total exposure count (32), same fact set,
two arms --
  spaced: 32 insertions evenly spaced through the 20M-token stream
          (identical to the exposure-curve protocol, r=32 tier)
  massed: the same 32 insertions back-to-back at one position
          (a single contiguous block per fact)
Cognitive-science prediction (spacing effect): massed needs more
repetitions for the same fixation, i.e. at 32 total exposures massed
<< spaced. Architecture: gpt2 (cloud 5090), matching the cloud
exposure-curve arm.

Also runs a massed-64 arm to locate the massed threshold if 32 is
insufficient.

Run on the cloud 5090:  python3 exposure_spacing.py
"""
import json
import os
import subprocess
import sys

import numpy as np

ROOT = "/root/autodl-tmp/mbn/llm"
TOKENS = f"{ROOT}/data/tokens.bin"
OUT = f"{ROOT}/exposure_spacing.json"
N_TOKENS = 20_000_000
VOCAB = 16384
SEED = 20261005

# reuse the fact set + spacing logic from the exposure curve
sys.path.insert(0, ROOT)
from exposure_gpt2 import pick_pools, probe  # noqa: E402

ARMS = [("spaced32", 32, "spaced"), ("massed32", 32, "massed"),
        ("massed64", 64, "massed"), ("massed16", 16, "massed")]


def build(full, facts, repeats, mode, path):
    seg = np.array(full[:N_TOKENS], dtype=np.uint16).copy()
    if repeats > 0:
        if mode == "spaced":
            slots = np.linspace(200_000, N_TOKENS - 200_000,
                                num=repeats * len(facts) + 1).astype(int)[1:]
            k = 0
            for rep in range(repeats):
                order = np.random.RandomState(SEED + rep).permutation(
                    len(facts))
                for fi in order:
                    s, r, o = facts[fi]
                    pos = slots[k]
                    seg[pos:pos + 4] = (s, r, o, seg[pos + 3])
                    k += 1
        else:  # massed: back-to-back block per fact, block positions spaced
            slots = np.linspace(200_000, N_TOKENS - 200_000,
                                num=len(facts) + 1).astype(int)[1:]
            for fi, (s, r, o) in enumerate(facts):
                pos = slots[fi]
                for rep in range(repeats):
                    p = pos + rep * 4
                    if p + 4 < N_TOKENS:
                        seg[p:p + 4] = (s, r, o, seg[p + 3])
    seg.tofile(path)


def main():
    full, facts, train_f, held_f, sep = pick_pools()
    print(f"facts {len(facts)} (train {len(train_f)}/held {len(held_f)})",
          flush=True)
    for name, repeats, mode in ARMS:
        data = f"{ROOT}/data/exp_{name}.bin"
        outdir = f"{ROOT}/runs/exp_{name}"
        if not os.path.exists(data):
            build(full, train_f, repeats, mode, data)
            print(f"[{name}] corpus built", flush=True)
        if not os.path.exists(f"{outdir}/final_state.pt"):
            print(f"[{name}] training...", flush=True)
            p = subprocess.run(
                [sys.executable, f"{ROOT}/train_lm.py", "--arch", "gpt2",
                 "--tokens", data, "--max-tokens", str(N_TOKENS),
                 "--out", outdir],
                capture_output=True, text=True)
            if "TRAINING DONE" not in p.stdout:
                print(f"[{name}] TRAIN FAILED\n{p.stdout[-600:]}\n"
                      f"{p.stderr[-600:]}", flush=True)
                continue
        res = probe("gpt2", facts, f"exp_{name}")
        res.update(repeats=repeats, mode=mode)
        store = json.load(open(OUT)) if os.path.exists(OUT) else {}
        store[name] = res
        json.dump(store, open(OUT, "w"), indent=1)
        print(f"[{name}] {res}", flush=True)
    print("SPACING DONE", flush=True)


if __name__ == "__main__":
    main()
