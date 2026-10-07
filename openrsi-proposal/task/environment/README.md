# verified-lemma-growth — Work environment

Lean 4 toolchain + the selflearner loop + the parsed mathlib library,
prebuilt into the image:

```
/workspace/
  library/mathlib.db          # 181,316 parsed mathlib theorems + FTS5
  library/vectors_release.npz # multilingual embedding index (sha256 in proposal)
  mathlib4/                   # mathlib sources + full olean cache (v4.35.0-rc3)
  loop/                       # propose_check.py, run_overnight.py, budget.py
  snapshot/                   # candidate deliverable (agent-owned)
```

## Build

Base `ubuntu:24.04` plus:

```bash
apt-get update && apt-get install -y python3 python3-pip sqlite3 curl unzip
pip3 install numpy sentence-transformers
# elan + Lean toolchain v4.35.0-rc3
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y --default-toolchain v4.35.0-rc3
# the prebuilt mathlib4 tree (sources + .lake/build/lib oleans) is copied
# from the release asset mathlib4-cache.tar.zst (sha256 in the proposal)
```

The embedding model is fetched at image build time and cached, so
Judge/Work never need model downloads at run time.
