"""Hybrid cross-language search: lexical (FTS5) + semantic (multilingual
embeddings) fused with reciprocal-rank fusion. Queries in Chinese or
English retrieve both knowledge cards and Lean theorems.

Usage: python search_hybrid.py "无穷多个素数" [n]
"""
import os
import sqlite3
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "mathlib.db")
VEC = os.path.join(ROOT, "vectors.npz")


def rrf(rank_lists, k=60):
    scores = {}
    for ranks in rank_lists:
        for pos, rid in enumerate(ranks):
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (k + pos + 1)
    return sorted(scores, key=scores.get, reverse=True)


def main():
    query = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    con = sqlite3.connect(DB)

    # lexical legs
    lex = []
    for tbl, label in (("thm_fts", "thm"), ("knowledge_fts", "know")):
        try:
            rows = con.execute(
                f"SELECT rowid FROM {tbl} WHERE {tbl} MATCH ? LIMIT 50",
                (query,)).fetchall()
            lex.append(([f"{label}:{r[0]}" for r in rows], label))
        except sqlite3.OperationalError:
            pass

    # semantic leg
    z = np.load(VEC)
    kb_ids, kb_vecs = list(z["kb_ids"]), z["kb_vecs"]
    thm_ids, thm_vecs = list(z["thm_ids"]), z["thm_vecs"]
    from sentence_transformers import SentenceTransformer
    enc = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    qv = enc.encode([query], normalize_embeddings=True)[0]
    sem = []
    if len(kb_ids):
        for i in np.argsort(-(kb_vecs @ qv))[:15]:
            sem.append(f"know:{kb_ids[i]}")
    if len(thm_ids):
        for i in np.argsort(-(thm_vecs @ qv))[:35]:
            sem.append(f"thm:{thm_ids[i]}")

    fused = rrf([r for r, _l in lex] + [sem])[:n]

    for key in fused:
        label, rid = key.split(":", 1)
        rid = int(rid)
        if label == "know":
            r = con.execute("SELECT text, lang, source FROM knowledge "
                            "WHERE id=?", (rid,)).fetchone()
            if r:
                print(f"=== [knowledge/{r[1]}] ({r[2]})")
                print("   ", " ".join(r[0].split())[:260])
        else:
            r = con.execute("SELECT name, statement, file FROM thm "
                            "WHERE id=?", (rid,)).fetchone()
            if r:
                print(f"=== [thm] {r[0]}  {r[2]}")
                print("   ", " ".join(r[1].split())[:240])
        print()


if __name__ == "__main__":
    main()
