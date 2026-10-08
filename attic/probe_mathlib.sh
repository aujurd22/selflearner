#!/bin/bash
# probe: mathlib4 project on /mnt/d + local elan -> lake env lean C1
cd /mnt/d/djr82/selflearner/mathlib4
ls lakefile.lean lean-toolchain lake-manifest.json 2>/dev/null
export PATH=/root/.elan/bin:$PATH
timeout 240 lake env lean C1.lean > probe_out.txt 2>&1
echo "probe_exit=$?"
grep -c "error" probe_out.txt || echo 0
grep "axioms" probe_out.txt | head -1
