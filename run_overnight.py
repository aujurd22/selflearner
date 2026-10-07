"""Overnight growth run: propose-check loop bounded by the proposer
CALL BUDGET (not a round count).

Budget semantics (rsi/verified-lemma-growth, fixed protocol):
  - the declared budget FLYLOOP_CALL_BUDGET (default 200) counts
    proposer dispatch attempts at the transport layer: every 429
    backoff retry and every transport failure after the request left
    the runner consumes one unit (counting lives in budget.py, invoked
    inside llm_client.ask and propose_check.ask_effort immediately
    before urlopen);
  - the budget is PERSISTENT: state lives in
    runs/budget_state<OVERNIGHT_TAG>.json, so a resume restores the
    cumulative count instead of resetting it;
  - the loop runs until the budget is exhausted (or the wall-clock
    deadline passes). A round cap is only an optional emergency brake
    via FLYLOOP_ROUND_CAP; the declared protocol has none.

Resumable: already-logged rounds are never re-run; the log row records
budget.count() before/after so per-round spend is auditable.

Usage:
  python run_overnight.py run [rounds=0] [effort=low]
  python run_overnight.py report
  python run_overnight.py budget-reset   # NEW loop: zero the counter
"""
import json
import os
import random
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import budget  # noqa: E402
import propose_check as pc  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(ROOT, "runs")


def log_path():
    tag = os.environ.get("OVERNIGHT_TAG", "")
    d = os.path.join(RUNS, "overnight_" + time.strftime("%Y%m%d"))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"log{tag}.jsonl")


def budget_state_path():
    tag = os.environ.get("OVERNIGHT_TAG", "")
    return os.path.join(RUNS, f"budget_state{tag}.json")


def run(rounds=0, effort="low", deadline_h=9.0):
    call_budget = int(os.environ.get("FLYLOOP_CALL_BUDGET", "200"))
    round_cap = int(os.environ.get("FLYLOOP_ROUND_CAP", "0"))
    budget.init(budget_state_path(), call_budget)

    run_seed = random.randrange(2**32)
    random.seed(run_seed)  # flyloop RUNSEED: domain choices must reproduce
    ask = pc.load_llm()  # ask_effort is the ONLY dispatch path below;
    # every attempt it makes is counted inside budget.consume()

    con = sqlite3.connect(pc.DB)
    lp = log_path()
    done = 0
    if os.path.exists(lp):
        with open(lp, encoding="utf-8") as f:
            done = sum(1 for line in f if json.loads(line).get("rnd"))
    t0 = time.time()
    prev = None
    passed = failed = 0
    spent_at_start = budget.count()
    streak = 0
    fail_first = {}
    rnd = done
    print(f"run_seed={run_seed} resume_from={done} "
          f"budget={budget.count()}/{call_budget}", flush=True)
    with open(lp, "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(seed=run_seed, resumed=done,
                                budget=budget.count(),
                                t=time.strftime("%H:%M:%S"))) + "\n")
    # NO round cap in the declared protocol: the loop stops when the
    # proposer budget is exhausted (budget.remaining() == 0, enforced
    # inside budget.consume() by BudgetExhausted) or the deadline hits.
    while (time.time() - t0) < deadline_h * 3600:
        if budget.remaining() == 0:
            break
        if round_cap and rnd >= round_cap:
            break
        rnd += 1
        pre = budget.count()
        try:
            r = pc.one_round(con, ask, rnd, prev,
                             lambda p: pc.ask_effort(p, effort=effort))
        except budget.BudgetExhausted as e:
            r = dict(rnd=rnd, ok=False, why=f"BUDGET {e!r}"[:120],
                     budget=budget.count())
        except Exception as e:  # noqa: BLE001
            r = dict(rnd=rnd, ok=False, why=f"EXC {e!r}"[:300])
        r["calls_before"] = pre
        r["calls_after"] = budget.count()
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
        print(f"[{rnd}] budget={budget.count()}/{call_budget} "
              f"{r.get('file', '?')} "
              f"{'PASS ' + r.get('name', '') if r['ok'] else 'FAIL'}",
              flush=True)
    n = con.execute("SELECT COUNT(*) FROM thm").fetchone()[0]
    kb = con.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
    summary = dict(finished=time.strftime("%Y-%m-%d %H:%M"),
                   rounds=rnd, passed=passed, failed=failed,
                   thm_total=n, kb_total=kb,
                   llm_calls=budget.count(), call_budget=call_budget,
                   calls_spent=budget.count() - spent_at_start)
    with open(os.path.join(os.path.dirname(lp),
                           f"summary{os.environ.get('OVERNIGHT_TAG', '')}.json"),
              "w") as f:
        json.dump(summary, f, indent=1)
    print("OVERNIGHT DONE", summary, flush=True)


def report():
    lp = log_path()
    if not os.path.exists(lp):
        print("no log yet"); return
    recs = [json.loads(x) for x in open(lp, encoding="utf-8")]
    rounds = [r for r in recs if r.get("rnd")]
    passed = [r for r in rounds if r["ok"]]
    print(f"rounds={len(rounds)} pass={len(passed)} "
          f"({100*len(passed)/max(1,len(rounds)):.0f}%)")
    sp = budget_state_path()
    if os.path.exists(sp):
        st = json.load(open(sp, encoding="utf-8"))
        print(f"budget: {st['calls']}/{st['limit']} dispatch attempts")
    fails = {}
    for r in rounds:
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
        run(int(sys.argv[2]) if len(sys.argv) > 2 and int(sys.argv[2]) > 0 else 0,
            sys.argv[3] if len(sys.argv) > 3 else "low")
    elif sys.argv[1] == "report":
        report()
    elif sys.argv[1] == "budget-reset":
        p = budget_state_path()
        if os.path.exists(p):
            os.remove(p)
        print("budget state cleared:", p)
