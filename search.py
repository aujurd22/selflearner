"""Search demo over the mathlib theorem library (FTS5, bm25-ranked).

Usage: python search.py "infinitely many primes" [n_results]
"""
import json
import sqlite3
import sys

DB = "mathlib.db"


def search(query, k=5):
    con = sqlite3.connect(DB)
    rows = con.execute(
        """SELECT thm.name, thm.kind, thm.statement, thm.proof, thm.docstring,
                  thm.file, thm.line, bm25(thm_fts) AS rank
           FROM thm_fts JOIN thm ON thm.id = thm_fts.rowid
           WHERE thm_fts MATCH ?
           ORDER BY rank LIMIT ?""",
        (query, k),
    ).fetchall()
    return rows


def show(rows, max_proof=400):
    for name, kind, stmt, proof, doc, file, line, rank in rows:
        print(f"=== {name}  [{kind}]  {file}:{line}  (bm25 {rank:.1f})")
        if doc:
            print("doc:", " ".join(doc.split())[:200])
        print("stmt:", " ".join(stmt.split())[:300])
        if proof:
            print("proof:", " ".join(proof.split())[:max_proof])
        print()


if __name__ == "__main__":
    q = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    show(search(q, k))
