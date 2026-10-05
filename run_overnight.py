"""Overnight growth run: propose-check loop until round budget or deadline.

Appends every round to runs/overnight_<date>/log.jsonl (resumable:
already-seen (file,name) rounds are skipped). Morning report:
python run_overnight.py report

Usage:
  python run_overnight.py run [rounds=60] [effort=low]
  python run_overnight.py report
"""
import json
import os
import random
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import propose_check as pc  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(ROOT, "runs")


def log_path():
    tag = os.environ.get("OVERNIGHT_TAG", "")
    d = os.path.join(RUNS, "overnight_" + time.strftime("%Y%m%d"))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"log{tag}.jsonl")


def run(rounds=60, effort="low", deadline_h=9.0):
    call_budget = int(os.environ.get("FLYLOOP_CALL_BUDGET", "200"))
    call_count = [0]
    orig_ask_effort = pc.ask_effort

    def counted_ask(prompt, effort=effort, temperature=0.4, max_tokens=8192):
        call_count[0] += 1
        return orig_ask_effort(prompt, effort=effort,
                               temperature=temperature,
                               max_tokens=max_tokens)

    def budget_left():
        return call_budget - call_count[0]

    run_seed = random.randrange(2**32)
    random.seed(run_seed)  # flyloop RUNSEED: domain choices must reproduce
    ask = pc.load_llm()
    ask_fn = (lambda p: pc.ask_effort(p, effort=effort)) if effort != "minimal" \
        else None
    con = sqlite3.connect(pc.DB)
    lp = log_path()
    done = 0
    if os.path.exists(lp):
        with open(lp, encoding="utf-8") as f:
            done = sum(1 for _ in f)
    t0 = time.time()
    prev = None
    passed = failed = 0
    streak = 0
    fail_first = {}
    rnd = done
    print(f"run_seed={run_seed} resume_from={done}", flush=True)
    with open(lp, "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(seed=run_seed, resumed=done,
                                t=time.strftime("%H:%M:%S"))) + "\n")
    while (rnd < rounds and (time.time() - t0) < deadline_h * 3600
           and budget_left() > 0):
        rnd += 1
        try:
            r = pc.one_round(con, ask, rnd, prev, ask_fn or counted_ask)
        except Exception as e:  # noqa: BLE001
            r = dict(rnd=rnd, ok=False, why=f"EXC {e!r}"[:300])
        passed += r["ok"]
        failed += not r["ok"]
        if r["ok"]:
            prev = pc.build_prev(r.get("code", ""), r.get("name", ""))
            streak = 0
        else:
            streak += 1
            bucket = r.get("why", "")[:40].split(":")[0]
            fail_first[bucket] = fail_first.get(bucket, 0) + 1
            if streak >= 4:  # dead-regime exit: force a fresh domain
                random.shuffle(pc._FILES)
                streak = 0
                r["domain_switch"] = True
        r["t"] = time.strftime("%H:%M:%S")
        with open(lp, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        if rnd % max(1, rounds // 4) == 0:  # flyloop: diag at quarter marks
            print(f"[diag {100*rnd//rounds}%] pass={passed} fail={failed} "
                  f"top_fail={max(fail_first, key=fail_first.get, default='-')}",
                  flush=True)
        tag = (f"PASS {r.get('name')} tries={r.get('tries', 1)}"
               if r["ok"] else f"FAIL {r.get('why', '')[:100]}")
        print(f"[{rnd}] {r.get('file', '?')} {tag}", flush=True)
    n = con.execute("SELECT COUNT(*) FROM thm").fetchone()[0]
    kb = con.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
    summary = dict(finished=time.strftime("%Y-%m-%d %H:%M"),
                   rounds=rnd, passed=passed, failed=failed,
                   thm_total=n, kb_total=kb)
    with open(os.path.join(os.path.dirname(lp),
                           f"summary{os.environ.get('OVERNIGHT_TAG', '')}.json"),
              "w") as f:
        json.dump(summary, f, indent=1)
    summary["llm_calls"] = call_count[0]
    summary["call_budget"] = call_budget
    print("OVERNIGHT DONE", summary, flush=True)


def report():
    lp = log_path()
    if not os.path.exists(lp):
        print("no log yet"); return
    recs = [json.loads(x) for x in open(lp, encoding="utf-8")]
    passed = [r for r in recs if r["ok"]]
    print(f"rounds={len(recs)} pass={len(passed)} "
          f"({100*len(passed)/max(1,len(recs)):.0f}%)")
    fails = {}
    for r in recs:
        if not r["ok"]:
            key = r.get("why", "")[:60].split(":")[0]
            fails[key] = fails.get(key, 0) + 1
    print("fail buckets:", fails)
    con = sqlite3.connect(pc.DB)
    print("\nadmitted lemmas:")
    for name, stmt in con.execute(
            "SELECT name, statement FROM thm WHERE attrs LIKE '%provenance=proposed%'"):
        print("-", name, "::", " ".join(stmt.split())[:150])


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(int(sys.argv[2]) if len(sys.argv) > 2 else 60,
            sys.argv[3] if len(sys.argv) > 3 else "low")
    elif sys.argv[1] == "report":
        report()
