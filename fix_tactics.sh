#!/bin/bash
cd /root/mbn/llm/selflearner_candidates
python3 - <<'PYEOF'
import io
s = io.open('C2.lean', encoding='utf-8').read()
s = s.replace('| zero => norm_num [Nat.tri]', '| zero => rfl')
io.open('C2.lean', 'w', encoding='utf-8', newline='\n').write(s)
s3 = io.open('C3.lean', encoding='utf-8').read()
s3 = s3.replace('rw [Finset.sum_range_succ, ih]', 'rw [ih]')
io.open('C3.lean', 'w', encoding='utf-8', newline='\n').write(s3)
print('patched')
PYEOF
cp C2.lean C3.lean /root/autodl-tmp/mathlib4/
export PATH=/root/.elan/bin:$PATH
for f in C2 C3; do
  timeout 280 lake env lean $f.lean > ${f}_out.txt 2>&1
  echo "== $f exit=$?"
  grep -c "error" ${f}_out.txt || echo 0
done
echo TACTIC_FIX_DONE
