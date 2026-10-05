"""Judge-only scorer for rsi/verified-lemma-growth (Harbor tests/).

Scores a candidate snapshot (/workspace/snapshot):
  1. Lean re-verification of every admitted lemma (fresh lake env).
  2. Triviality gate (True/False statements).
  3. Novelty adjudication: retrieval = RRF(semantic top-k, lexical FTS)
     over the library, then a cross-model-family LLM judge answers
     "is this a restatement of one of these?" — the lexical leg exists
     because semantic-only retrieval misses textbook restatements
     (2026-10-05 A/B: 8 'n + 0 = n' restatements passed a semantic-only
     gate in both arms; Nat.add_zero was unfindable by embedding).

Primary score: count of lemmas passing 1+2+3. Secondary: restatement
rate, triviality rate. Emits report.json — never trusts candidate logs.
"""
import json
import os
import re
import sqlite3
import subprocess
import sys

import numpy as np

LIB = "/workspace/library/mathlib.db"
MATHLIB = "/workspace/mathlib4"
SNAP = "/workspace/snapshot"
RRF_K = 60


def rrf(rank_lists):
    scores = {}
    for ranks in rank_lists:
        for pos, rid in enumerate(ranks):
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (RRF_K + pos + 1)
    return [rid for rid, _ in sorted(scores.items(),
                                     key=lambda kv: -kv[1])]


def neighbors(con, stmt, k=5):
    """Hybrid semantic + lexical legs (the v2.5 fix)."""
    # semantic
    from sentence_transformers import SentenceTransformer
    enc = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    z = np.load("/workspace/library/vectors_release.npz")
    tv, tids = z["thm_vecs"], list(z["thm_ids"])
    v = enc.encode([" ".join(stmt.split())[:512]],
                   normalize_embeddings=True)[0]
    sem = [tids[i] for i in np.argsort(-(tv @ v))[:20]]
    # lexical: token keys from the candidate statement
    toks = [t for t in re.findall(r"[A-Za-z_]{3,}|\d+", stmt)][:6]
    lex = []
    if toks:
        q = " OR ".join(toks)
        try:
            lex = [r[0] for r in con.execute(
                "SELECT rowid FROM thm_fts WHERE thm_fts MATCH ? LIMIT 20",
                (q,))]
        except sqlite3.OperationalError:
            pass
    fused = rrf([sem, lex])[:k]
    out = []
    for rid in fused:
        r = con.execute("SELECT name, statement FROM thm WHERE id=?",
                        (rid,)).fetchone()
        if r:
            out.append((r[0], " ".join(r[1].split())[:220]))
    return out


def lean_ok(stmt, proof, workdir="/tmp/judge"):
    os.makedirs(workdir, exist_ok=True)
    proof_ind = "\n".join(("  " + ln if ln.strip() else ln)
                          for ln in proof.split("\n"))
    with open(f"{workdir}/Cand.lean", "w", encoding="utf-8",
              newline="\n") as f:
        f.write("import Mathlib.Tactic\n\n" + stmt + "\n" + proof_ind + "\n")
    p = subprocess.run(["lake", "env", "lean", "Cand.lean"], cwd=MATHLIB,
                       capture_output=True, text=True, timeout=600,
                       encoding="utf-8", errors="replace")
    return p.returncode == 0, (p.stdout + p.stderr)[-300:]


def adjudicate(ask_fn, stmt, neigh):
    lst = "\n".join(f"- `{n}`: {s}" for n, s in neigh)
    prompt = (
        "You are a novelty judge for a Lean mathlib library.\n\n"
        f"Candidate lemma:\n{stmt[:600]}\n\n"
        f"Closest existing theorems (hybrid retrieval):\n{lst}\n\n"
        "Step 1: name the mathematical content of the candidate in words "
        "(e.g. 'left additive identity for naturals').\n"
        "Step 2: is the candidate a restatement, renaming, or trivial "
        "special case of any listed theorem — or of any standard theorem "
        "its step-1 name corresponds to? Answer IMMEDIATELY with exactly "
        "one word RESTATEMENT or NOVEL, then one short reason.")
    reply = ask_fn(prompt)
    first = reply.strip().split()[0].upper() if reply.strip() else "NOVEL"
    return "RESTATEMENT" in first, reply.strip()[:200]


def main():
    con = sqlite3.connect(LIB)
    sys.path.insert(0, "/workspace/loop")
    from judge_client import make_ask  # endpoint/key injected by harness
    ask_fn = make_ask()
    admitted = sorted(os.listdir(f"{SNAP}/admitted"))
    results = []
    for fn in admitted:
        code = open(f"{SNAP}/admitted/{fn}", encoding="utf-8").read()
        m = re.search(r":=\s*by\b", code)
        stmt, proof = (code[:m.start()], code[m.end():]) if m else (code, "")
        ok, log = lean_ok(stmt.strip(), proof.strip())
        trivial = bool(re.search(r":\s*(True|False)\b\s*:?=", stmt))
        verdict, why = ("RESTATEMENT", "trivial") if trivial \
            else adjudicate(ask_fn, stmt, neighbors(con, stmt)) if ok \
            else ("FAIL", log[-120:])
        results.append(dict(file=fn, compiled=ok, verdict=verdict, why=why))
        print(f"{fn}: compiled={ok} {verdict}", flush=True)
    novel = sum(1 for r in results
                if r["compiled"] and r["verdict"] == "NOVEL")
    report = dict(primary_novel_count=novel,
                  admitted=len(results),
                  restatement_rate=round(sum(1 for r in results
                                             if r["verdict"] == "RESTATEMENT")
                                         / max(1, len(results)), 3),
                  trivial_rate=round(sum(1 for r in results
                                         if r["verdict"] == "trivial")
                                     / max(1, len(results)), 3),
                  details=results)
    json.dump(report, open(f"{SNAP}/report.json", "w"), indent=1)
    print("SCORE", novel, flush=True)


if __name__ == "__main__":
    main()
