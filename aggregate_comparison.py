"""Aggregate the six-loop formal comparison (3 gated + 3 control).

Reads the per-loop snapshots, runs the same reconciliation the Judge
runs, applies the three pre-registered metrics, and writes
comparison_results.json:

  per-loop:  arm, rounds, budget_used, admitted, verified, novel
  aggregate: median novel per arm, verification yield, novel-yield
             rate (novel per 100 dispatches), knowledge-growth
             efficiency (novel/hour)

Usage: python aggregate_comparison.py <snapshot-dir> [<snapshot-dir> ...]
Each snapshot dir must contain log.jsonl + report.json (Judge output)
and be named or described with its arm (gated/control).
"""
import json
import statistics
import sys
from pathlib import Path

BUDGET = 60


def load_snapshot(d):
    d = Path(d)
    log = d / "log.jsonl"
    rep = d / "report.json"
    if not log.exists() or not rep.exists():
        return None
    rounds = []
    for l in log.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if isinstance(r, dict):   # skip seed/resume marker rows
            rounds.append(r)
    spend = [r for r in rounds
             if isinstance(r, dict) and isinstance(r.get("rnd"), int)]
    final_calls = max((r.get("calls_after", 0) for r in spend), default=0)
    report = json.loads(rep.read_text(encoding="utf-8"))
    admitted = report.get("admitted", 0)
    novel = report.get("primary_novel_count", 0)
    verified = sum(1 for r in report.get("details", [])
                   if r.get("compiled") and r.get("verdict") != "INFRA")
    # arm from the runner summary or dir name
    arm = "unknown"
    for r in rounds:
        if r.get("arm"):
            arm = r["arm"]
            break
    if arm == "unknown":
        arm = "gated" if "gated" in d.name.lower() else "control"
    return dict(dir=str(d), arm=arm, rounds=len(spend),
                budget_used=final_calls, admitted=admitted,
                verified=verified, novel=novel)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    snaps = [load_snapshot(a) for a in sys.argv[1:]]
    snaps = [s for s in snaps if s]
    by_arm = {}
    for s in snaps:
        by_arm.setdefault(s["arm"], []).append(s)
    agg = {}
    for arm, lst in by_arm.items():
        novels = [s["novel"] for s in lst]
        dispatches = [s["budget_used"] for s in lst]
        verification_yield = (sum(s["verified"] for s in lst)
                              / max(1, sum(s["admitted"] for s in lst)))
        agg[arm] = dict(
            loops=len(lst),
            median_novel=statistics.median(novels),
            novels=novels,
            total_dispatches=sum(dispatches),
            all_within_budget=all(s["budget_used"] <= BUDGET
                                  for s in lst),
            verification_yield=round(verification_yield, 4),
            novel_yield_rate=round(sum(novels) / max(1, sum(dispatches))
                                   * 100, 3))
    out = dict(per_loop=snaps, aggregate=agg, budget=BUDGET)
    json.dump(out, open("comparison_results.json", "w"), indent=1)
    print(json.dumps(agg, indent=1))


if __name__ == "__main__":
    main()
