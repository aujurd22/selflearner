"""Downstream utility experiment (review round-3 stage-03; pre-registered).

Question: do admitted lemmas, fed as retrieval context, improve the
proposer's success rate on formal math statements (miniF2F Test subset)?

Design:
  - Fixed task set: 30 miniF2F Test problems (deterministic selection:
    first 30 by filename order), each is a theorem statement with a
    `sorry` proof placeholder.
  - Arms: baseline (no admitted-lemma context) vs enhanced (top-3
    admitted lemmas by lexical FTS match to the problem statement,
    fed as retrieval context in the prompt).
  - 3 seeds per arm; same proposer (glm-5.3-flash, effort=low), same
    budget (1 proposal + 1 repair per problem), same parse criteria.
  - Success: proposed Lean code compiles under `lake env lean` with no
    sorry AND proves the exact statement (statement-level match).
  - Pre-registered: enhanced >= baseline (one-sided); report per-problem
    and aggregate. A null result is informative (pilot conclusion:
    proposer bottleneck, admitted lemmas too few/local).

Usage: python downstream_utility.py [--arms both] [--n 30]
Output: downstream_utility_results.json
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import propose_check as pc

MINIF2F = "D:/djr82/minif2f-lean4/MiniF2F/Test"
RESULTS = "downstream_utility_results.json"


def pick_problems(n=30):
    files = sorted(glob.glob(os.path.join(MINIF2F, "*.lean")))[:n]
    probs = []
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        src = open(path, encoding="utf-8", errors="replace").read()
        probs.append((name, src))
    return probs


def admitted_lemmas():
    con = sqlite3.connect(pc.DB)
    return con.execute(
        "SELECT name, statement, proof FROM thm "
        "WHERE attrs LIKE '%provenance=proposed%'").fetchall()


def lexical_top_k(query, lemmas, k=3):
    """Lexical overlap scoring (no FTS dependency — deterministic)."""
    qtok = set(re.findall(r"[A-Za-z_]+", query.lower()))
    scored = []
    for name, stmt, proof in lemmas:
        t = set(re.findall(r"[A-Za-z_]+", (stmt + " " + proof).lower()))
        if not t:
            continue
        score = len(qtok & t) / len(t)
        scored.append((score, name, stmt, proof))
    scored.sort(reverse=True)
    return scored[:k]


def attempt(problem_name, src, context_blocks, seed):
    """One proposal + one repair per problem. Returns (compiles, no_sorry)."""
    ctx = ""
    if context_blocks:
        ctx = ("\n\nRelevant lemmas already in the library (you may cite "
               "them):\n" + "\n".join(context_blocks))
    prompt = pc.PROMPT.format(context="") + (
        f"\n\nTarget problem (from {problem_name}):\n```lean\n{src}\n```\n"
        "Propose a Lean 4 proof completing this statement. No sorry."
        + ctx)
    reply = pc.ask_effort(prompt, effort="low")
    m = re.search(r"```lean\n(.*?)```", reply, re.S)
    if not m:
        return False, ""
    code = m.group(1).strip()
    ok, log = pc.check_candidate(code)
    return ok, code


def run_arm(arm, problems, lemmas, seed):
    import random
    random.seed(seed)
    results = []
    for name, src in problems:
        ctx_blocks = []
        if arm == "enhanced" and lemmas:
            blocks = lexical_top_k(src, lemmas, k=3)
            ctx_blocks = [f"```lean\n{s}\n{p}\n```" for _s, _n, s, p in blocks]
        ok, code = attempt(name, src, ctx_blocks, seed)
        results.append(dict(problem=name, arm=arm, seed=seed,
                            compiles=ok))
        print(f"  {name}: {'PASS' if ok else 'FAIL'}", flush=True)
    n_ok = sum(1 for r in results if r["compiles"])
    print(f"  arm={arm} seed={seed}: {n_ok}/{len(problems)}", flush=True)
    return results, n_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seeds", type=int, default=1,
                    help="seeds per arm (pilot: 1; formal: 3)")
    args = ap.parse_args()

    problems = pick_problems(args.n)
    lemmas = admitted_lemmas()
    print(f"problems: {len(problems)}, admitted lemmas: {len(lemmas)}",
          flush=True)

    all_results = []
    summary = {}
    for arm in ("baseline", "enhanced"):
        for seed in range(args.seeds):
            res, n_ok = run_arm(arm, problems, lemmas, seed)
            all_results.extend(res)
            summary.setdefault(arm, []).append(n_ok)

    out = dict(summary=summary, results=all_results,
               admitted_lemma_count=len(lemmas))
    json.dump(out, open(RESULTS, "w"), indent=1)
    for arm, counts in summary.items():
        total = sum(counts)
        n = len(counts) * len(problems)
        print(f"ARM {arm}: {total}/{n} = {total/max(1,n):.1%}", flush=True)
    print("DOWNSTREAM UTILITY COMPLETE", flush=True)


if __name__ == "__main__":
    main()
