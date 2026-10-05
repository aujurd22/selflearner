"""Judge adjudication for the gated-vs-ungated A/B comparison.

For each admitted lemma in both arms' logs:
  1. Lean re-verification (batch: one file per arm, lake env lean).
  2. Triviality check (True/False statements).
  3. Semantic top-3 neighbors + LLM novelty adjudication ("is this a
     restatement of one of these?").

Output: side-by-side table (compiled / verified / novel counts) written
to stdout and runs/overnight_<date>/judge_report.md.
"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import propose_check as pc  # noqa: E402
from ingest import embed  # noqa: E402

ROOT = pc.ROOT
MATHLIB = pc.MATHLIB


def load_arm(tag):
    lp = os.path.join(RUNS_DIR, f"log{tag}.jsonl")
    recs = [json.loads(x) for x in open(lp, encoding="utf-8")
            if x.strip().startswith('{"rnd')]
    return [r for r in recs if r.get("ok")]


RUNS_DIR = os.path.join(ROOT, "runs", "overnight_" + time.strftime("%Y%m%d"))


def lean_reverify(name, con):
    row = con.execute(
        "SELECT statement, proof FROM thm WHERE name=?", (name,)).fetchone()
    if not row:
        return False, "missing from library"
    stmt, proof = row
    code = "import Mathlib.Tactic\n\n" + stmt + "\n" + proof + "\n"
    f = os.path.join(MATHLIB, "JudgeReverify.lean")
    with open(f, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(code)
    p = subprocess.run(["lake", "env", "lean", "JudgeReverify.lean"],
                       cwd=MATHLIB, capture_output=True, text=True,
                       timeout=600, encoding="utf-8", errors="replace")
    return p.returncode == 0, (p.stdout + p.stderr)[-200:]


def neighbors(con, stmt, k=3, exclude=None):
    z = np.load(os.path.join(ROOT, "vectors.npz"))
    tv, tids = z["thm_vecs"], list(z["thm_ids"])
    m = re.search(r"^(?:lemma|theorem)\s+\S+\s+([^:]*)\s*:\s*(.+)",
                  stmt, re.M | re.S)
    core = " ".join((m.group(1) + m.group(2)).split())[:512] if m else stmt[:512]
    v = embed(core)
    order = np.argsort(-(tv @ v))
    out = []
    for i in order:
        nid = int(tids[int(i)])
        if exclude and nid == exclude:
            continue
        r = con.execute("SELECT name, statement FROM thm WHERE id=?",
                        (nid,)).fetchone()
        if r:
            out.append((r[0], " ".join(r[1].split())[:220]))
        if len(out) >= k:
            break
    return out


def llm_adjudicate(ask_fn, stmt, neigh):
    lst = "\n".join(f"- `{n}`: {s}" for n, s in neigh)
    prompt = (
        "You are a novelty judge for a Lean mathlib library.\n\n"
        f"Candidate lemma:\n{stmt}\n\n"
        f"Closest existing theorems:\n{lst}\n\n"
        "Is the candidate a restatement, trivial special case, or "
        "notation-level variant of any existing theorem above? "
        "Answer IMMEDIATELY with exactly one word RESTATEMENT or NOVEL, "
        "then one short sentence of reason.")
    reply = ask_fn(prompt)
    word = reply.strip().split()[0].upper() if reply.strip() else "NOVEL"
    return ("RESTATEMENT" in word, reply.strip()[:200])


def main():
    arms = {"gated": load_arm(""), "ungated": load_arm("_ungated")}
    con = sqlite3.connect(pc.DB)
    ask = pc.load_llm()
    ask_fn = lambda p: pc.ask_effort(p, effort="low")  # noqa: E731
    report = ["# Judge report — gated vs ungated", ""]
    rows = []
    for arm, admitted in arms.items():
        verified = novel = trivial = restated = 0
        detail = []
        for r in admitted:
            name = r.get("name", "")
            row = con.execute(
                "SELECT statement, proof, id FROM thm WHERE name=?",
                (name,)).fetchone()
            if not row:
                detail.append((name, "MISSING", "-", "-"))
                continue
            stmt_full, _proof, tid = row
            ok, log = lean_reverify(name, con)
            verified += ok
            if re.search(r":\s*(True|False)\b\s*:?=", stmt_full):
                trivial += 1
                detail.append((name, "compiled" if ok else "FAIL",
                               "TRIVIAL", "-"))
                continue
            neigh = neighbors(con, stmt_full, 3, exclude=tid)
            is_rest, why = llm_adjudicate(ask_fn, stmt_full[:600], neigh)
            restated += is_rest
            novel += ok and not is_rest
            detail.append((name, "compiled" if ok else "FAIL",
                           "RESTATEMENT" if is_rest else "NOVEL",
                           why.split("\n")[-1][:80]))
        rows.append((arm, len(admitted), verified, novel, restated, trivial,
                     detail))
    report.append("| arm | admitted | compiled | novel(final) | restated | trivial |")
    report.append("|---|---|---|---|---|---|")
    for arm, n, v, nv, rs, tr, _d in rows:
        report.append(f"| {arm} | {n} | {v} | {nv} | {rs} | {tr} |")
    report.append("")
    for arm, _n, _v, _nv, _rs, _tr, detail in rows:
        report.append(f"## {arm} — per-lemma")
        for name, comp, verdict, why in detail:
            report.append(f"- {name}: {comp} / {verdict} / {why}")
        report.append("")
    out = "\n".join(report)
    print(out)
    with open(os.path.join(RUNS_DIR, "judge_report.md"), "w",
              encoding="utf-8") as f:
        f.write(out)


if __name__ == "__main__":
    main()
