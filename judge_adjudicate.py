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
    """Arms from the library itself: admit() stamped the arm into attrs
    (provenance=proposed / proposed-ungated). The original JSONL logs were
    lost in the runs/ cleanup -- the library IS the record."""
    con = sqlite3.connect(pc.DB)
    pat = "%provenance=proposed-ungated%" if tag == "_ungated"         else "%provenance=proposed%"
    rows = con.execute(
        "SELECT name, statement, proof FROM thm WHERE attrs LIKE ? "
        "ORDER BY id", (pat,)).fetchall()
    return [dict(name=n, statement=st, proof=pf) for n, st, pf in rows]


RUNS_DIR = os.path.join(ROOT, "runs", "overnight_" + time.strftime("%Y%m%d"))


def lean_reverify_batch(names, con):
    """One lake invocation for all lemmas (N cold starts were timing
    out under local load). Returns {name: (ok, log_tail)}."""
    blocks = []
    for name in names:
        row = con.execute(
            "SELECT statement, proof FROM thm WHERE name=?",
            (name,)).fetchone()
        if not row:
            blocks.append((name, None, None))
            continue
        stmt, proof = row
        nl = chr(10)
        proof_ind = nl.join(("  " + ln if ln.strip() else ln)
                            for ln in proof.split(nl))
        blocks.append((name, stmt, proof_ind))
    nl = chr(10)
    body = "import Mathlib.Tactic" + nl + nl
    for name, stmt, proof_ind in blocks:
        if stmt is None:
            continue
        body += (f"-- BEGIN {name}" + nl + stmt + nl + proof_ind
                 + nl + "-- END" + nl + nl)
    f = os.path.join(MATHLIB, "JudgeReverify.lean")
    with open(f, "w", encoding="utf-8", newline="") as fh:
        fh.write(body)
    try:
        p = subprocess.run(["lake", "env", "lean", "JudgeReverify.lean"],
                           cwd=MATHLIB, capture_output=True, text=True,
                           timeout=1200, encoding="utf-8", errors="replace")
        out = p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    res = {}
    for name, stmt, proof_ind in blocks:
        if stmt is None:
            res[name] = (False, "missing from library")
        elif out == "TIMEOUT":
            res[name] = (False, "TIMEOUT (skipped, inconclusive)")
        elif name in out:
            res[name] = (False, out[out.index(name):][:200])
        else:
            res[name] = (True, "")
    return res



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
        f"Closest existing theorems (hybrid retrieval):\n{lst}\n\n"
        "Step 1: name the mathematical content of the candidate in plain "
        "words (e.g. 'left additive identity for naturals', 'limit of a "
        "constant sequence').\n"
        "Step 2: is the candidate a restatement, renaming, or trivial "
        "special case of any listed theorem — or of any standard theorem "
        "its step-1 name corresponds to (think: does mathlib already have "
        "the theorem your step-1 name describes)? "
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
    all_names = [r["name"] for arm in arms.values() for r in arm]
    reverify = lean_reverify_batch(all_names, con)
    for arm, admitted in arms.items():
        verified = novel = trivial = restated = 0
        detail = []
        for r in admitted:
            name = r["name"]
            row = con.execute(
                "SELECT statement, proof, id FROM thm WHERE name=?",
                (name,)).fetchone()
            if not row:
                detail.append((name, "MISSING", "-", "-"))
                continue
            stmt_full, _proof, tid = row
            ok, log = reverify.get(name, (False, "no reverify"))
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
