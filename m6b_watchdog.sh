#!/bin/bash
# M6b dense watchdog: poll arms; when both finish -> auto visit-k stats
LOG=/d/djr82/flyloop/m6b_watchdog.log
echo "$(date) watchdog start" >> $LOG
while true; do
  BASE_ALIVE=$(pgrep -f "flyloop.supervisor.*m6b_dense_s1" | wc -l)
  DELTA_ALIVE=$(pgrep -f "flyloop.supervisor.*m6b_dense_delta_s1" | wc -l)
  if [ "$BASE_ALIVE" -eq 0 ] && [ "$DELTA_ALIVE" -eq 0 ]; then
    echo "$(date) both arms finished -> auto adjudication" >> $LOG
    wsl -d Ubuntu-24.04 -u root -- python3 - <<'PYEOF' >> $LOG 2>&1
import json
from collections import Counter
sched = json.load(open("/mnt/d/djr82/flyloop/runs/m6b_dense_s1/world_schedule.json"))
fam1 = sched["1"]
recalls = [e for e in fam1 if e["type"] == "RECALL"]
visits = Counter(e["rule_id"] for e in recalls)
print("PERIODIC episodes:", len(fam1), "| RECALL:", len(recalls))
print("max visit k:", max(visits.values()) if visits else 0)
print("DELTA_GATE:", "PASS" if visits and max(visits.values()) >= 13 else "FAIL")
PYEOF
    echo "$(date) adjudication done, watchdog exit" >> $LOG
    break
  fi
  sleep 120
done
