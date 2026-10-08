#!/bin/bash
# install elan + Lean toolchain into local WSL (one-time, ~5 min)
curl -sSfL https://elan.lean-lang.org/elan-init.sh -o /tmp/elan-init.sh
sh /tmp/elan-init.sh -y --default-toolchain leanprover/lean4:v4.35.0-rc3 2>&1 | tail -3
export PATH=/root/.elan/bin:$PATH
lake --version 2>&1 | head -1
lean --version 2>&1 | head -1
echo ELAN_LOCAL_DONE
