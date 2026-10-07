#!/bin/bash
# Harbor verifier entry for rsi/verified-lemma-growth.
# Judge-side: compiles + re-verifies every submitted lemma and
# adjudicates novelty. Writes /logs/verifier/reward.json.
set -euo pipefail
unset PYTHONHOME PYTHONPATH PYTHONSTARTUP PYTHONUSERBASE
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

cd /
exec python3 /tests/judge_score.py
