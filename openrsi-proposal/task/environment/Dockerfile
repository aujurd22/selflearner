FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv sqlite3 curl unzip git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages numpy sentence-transformers

# Lean toolchain (matches the pinned mathlib olean cache)
RUN curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y \
    --default-toolchain v4.35.0-rc3
ENV PATH="/root/.elan/bin:${PATH}"
ENV ELAN_HOME="/root/.elan"

# Prebuilt mathlib4 tree + library + loop code are staged from the
# task's release assets by the Engine (sha256 pinned in proposal.md);
# this Dockerfile provides the runtime baseline only.
RUN mkdir -p /workspace/library /workspace/mathlib4 /workspace/loop \
    /workspace/snapshot

WORKDIR /workspace
