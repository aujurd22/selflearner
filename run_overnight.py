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

A NEW loop is declared by a fresh ARK_BUDGET_STATE path (the runner
derives it from a NEW OVERNIGHT_TAG). There is no reset command: the
budget state of a running loop is a protocol component.
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


def _start_proxy():
    """Start the mandatory proposer proxy and point the client at it.

    Credential boundary (v12): the ARK key moves OUT of the runner
    environment into a root-only file the proxy reads at startup; the
    runner and the agent shell never hold the key. The proxy pins the
    declared model, counts every upstream dispatch attempt, and fails
    closed (startup aborts) when the budget state is unusable."""
    import subprocess
    import urllib.request as _u
    import tempfile as _tmp
    state = budget_state_path()
    key = os.environ.pop("ARK_API_KEY", "")  # scrub from the agent env
    env = {k: v for k, v in os.environ.items()
           if "KEY" not in k.upper() and "TOKEN" not in k.upper()
           and "SECRET" not in k.upper()}
    env.update(ARK_BUDGET_STATE=state,
               ARK_API_KEY=key,  # proxy-process env only
               FLYLOOP_CALL_BUDGET=os.environ.get("FLYLOOP_CALL_BUDGET", "200"),
               ARK_MODEL=os.environ.get("ARK_MODEL", "glm-5.3-flash"))
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "ark_proxy.py")],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            with _u.urlopen("http://127.0.0.1:8080/health", timeout=2) as r:
                if r.status == 200:
                    os.environ["ARK_BASE_URL"] = "http://127.0.0.1:8080"
                    os.environ["ARK_PROXY_REQUIRED"] = "1"
                    os.environ["ARK_PROXY_PID"] = str(proc.pid)
                    return state
        except Exception:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("proposer proxy failed to start — the loop cannot "
                       "dispatch: the proxy is the budget enforcement point")


def _proxy_calls():
    """Authoritative count: read the proxy's health endpoint (the proxy
    process owns the counter; this runner only reports it)."""
    import urllib.request as _u
    try:
        with _u.urlopen("http://127.0.0.1:8080/health", timeout=2) as r:
            return int(json.load(r)["calls"])
    except Exception:
        return budget.count()

def run(rounds=0, effort="low", deadline_h=9.0):
    call_budget = int(os.environ.get("FLYLOOP_CALL_BUDGET", "200"))
    round_cap = int(os.environ.get("FLYLOOP_ROUND_CAP", "0"))
    state = _start_proxy()
    budget.init(state, call_budget)  # counts come from the proxy's file
    # re-read after init: the proxy restored its own persisted count
    budget_count = budget.count

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
    spent_at_start = _proxy_calls()
    streak = 0
    fail_first = {}
    rnd = done
    print(f"run_seed={run_seed} resume_from={done} "
          f"budget={_proxy_calls()}/{call_budget}", flush=True)
    with open(lp, "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(seed=run_seed, resumed=done,
                                budget=_proxy_calls(),
                                t=time.strftime("%H:%M:%S"))) + "\n")
    # NO round cap in the declared protocol: the loop stops when the
    # proposer budget is exhausted (budget.remaining() == 0, enforced
    # inside budget.consume() by BudgetExhausted) or the deadline hits.
    while (time.time() - t0) < deadline_h * 3600:
        if _proxy_calls() >= call_budget:
            break
        if round_cap and rnd >= round_cap:
            break
        rnd += 1
        pre = _proxy_calls()
        try:
            r = pc.one_round(con, ask, rnd, prev,
                             lambda p: pc.ask_effort(p, effort=effort))
        except budget.BudgetExhausted as e:
            r = dict(rnd=rnd, ok=False, why=f"BUDGET {e!r}"[:120],
                     budget=_proxy_calls())
        except Exception as e:  # noqa: BLE001
            r = dict(rnd=rnd, ok=False, why=f"EXC {e!r}"[:300])
        r["calls_before"] = pre
        r["calls_after"] = _proxy_calls()
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
        print(f"[{rnd}] budget={_proxy_calls()}/{call_budget} "
              f"{r.get('file', '?')} "
              f"{'PASS ' + r.get('name', '') if r['ok'] else 'FAIL'}",
              flush=True)
    n = con.execute("SELECT COUNT(*) FROM thm").fetchone()[0]
    kb = con.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
    summary = dict(finished=time.strftime("%Y-%m-%d %H:%M"),
                   rounds=rnd, passed=passed, failed=failed,
                   thm_total=n, kb_total=kb,
                   llm_calls=_proxy_calls(), call_budget=call_budget,
                   calls_spent=_proxy_calls() - spent_at_start)
    with open(os.path.join(os.path.dirname(lp),
                           f"summary{os.environ.get('OVERNIGHT_TAG', '')}.json"),
              "w") as f:
        json.dump(summary, f, indent=1)
    # deliver the provider-side dispatch ledger with the snapshot:
    # the Judge cross-checks it against the log spend chain (v16)
    ledger_src = os.environ.get(
        "ARK_DISPATCH_LOG",
        os.path.join(RUNS, "dispatch.jsonl"))
    snap = os.environ.get("SELFLEARNER_SNAPSHOT", "/workspace/snapshot")
    try:
        if os.path.exists(ledger_src):
            os.makedirs(snap, exist_ok=True)
            import shutil
            shutil.copy(ledger_src, os.path.join(snap, "dispatch.jsonl"))
    except OSError as e:
        print(f"WARN: dispatch ledger not copied into snapshot: {e}",
              flush=True)
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
        # deadline override is a first-class CLI flag: formal launches
        # pass --deadline-h covering the full 200-dispatch budget
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        deadline = 9.0
        if "--deadline-h" in sys.argv:
            deadline = float(sys.argv[sys.argv.index("--deadline-h") + 1])
        run(int(args[0]) if args and int(args[0]) > 0 else 0,
            args[1] if len(args) > 1 else "low", deadline_h=deadline)
    elif sys.argv[1] == "report":
        report()
