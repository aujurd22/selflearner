"""Ingest arbitrary text knowledge (zh/en) into the selflearner library.

Feed: knowledge cards (declarative statements, M5T form) as a JSON list
or inline strings. Each card gets an embedding; the vector index lives
alongside the Lean theorem index so one hybrid search sees both.

Usage:
  python ingest.py feed knowledge_cards.json     # ingest cards
  python ingest.py embed-thm                     # embed all thm statements (background job)
"""
import json
import os
import sqlite3
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "mathlib.db")
VEC = os.path.join(ROOT, "vectors.npz")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_model = None


def model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts, batch=256):
    return model().encode(texts, batch_size=batch, show_progress_bar=False,
                          normalize_embeddings=True)


def load_vec():
    """Return separate id/vec lists per source: (kb_ids, kb_vecs, thm_ids, thm_vecs)."""
    if os.path.exists(VEC):
        z = np.load(VEC)
        return (list(z["kb_ids"]), z["kb_vecs"],
                list(z["thm_ids"]), z["thm_vecs"])
    e = np.zeros((0, 384), dtype=np.float32)
    return [], e, [], e.copy()


def save_vec(kb_ids, kb_vecs, thm_ids, thm_vecs):
    np.savez(VEC, kb_ids=np.array(kb_ids), kb_vecs=kb_vecs,
             thm_ids=np.array(thm_ids), thm_vecs=thm_vecs)


def feed(cards, source="manual"):
    """cards: list of dicts {text, lang} or plain strings."""
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS knowledge(
        id INTEGER PRIMARY KEY, text TEXT, lang TEXT, source TEXT,
        created TEXT DEFAULT (datetime('now')))""")
    rows = []
    for c in cards:
        text = c["text"] if isinstance(c, dict) else c
        lang = c.get("lang", "") if isinstance(c, dict) else ""
        rows.append((text.strip(), lang, source))
    vecs = embed([r[0] for r in rows])
    cur = con.executemany(
        "INSERT INTO knowledge(text,lang,source) VALUES(?,?,?)", rows)
    con.commit()
    new_ids = [r[0] for r in con.execute(
        "SELECT id FROM knowledge ORDER BY id DESC LIMIT ?", (len(rows),))]
    con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5("
                "text, content='knowledge', content_rowid='id')")
    con.executemany("INSERT INTO knowledge_fts(rowid,text) VALUES(?,?)",
                    list(zip(new_ids, [r[0] for r in rows])))
    con.commit()
    kb_ids, kb_vecs, thm_ids, thm_vecs = load_vec()
    kb_ids = new_ids[::-1] + kb_ids
    kb_vecs = np.vstack([vecs, kb_vecs])
    save_vec(kb_ids, kb_vecs, thm_ids, thm_vecs)
    return len(rows)


def embed_thm(limit=None):
    """Embed theorem statements into the same vector index."""
    con = sqlite3.connect(DB)
    q = "SELECT id, statement FROM thm ORDER BY id"
    if limit:
        q += f" LIMIT {limit}"
    ids_all, texts_all = [], []
    for tid, stmt in con.execute(q):
        ids_all.append(tid)
        texts_all.append(" ".join(stmt.split())[:512])
    kb_ids, kb_vecs, thm_ids, thm_vecs = load_vec()
    have = set(thm_ids)
    todo = [(i, t) for i, t in zip(ids_all, texts_all) if i not in have]
    print(f"to embed: {len(todo)} / {len(ids_all)}")
    t0 = time.time()
    chunk_ids, chunks = [], []
    for k in range(0, len(todo), 4096):
        part = todo[k:k + 4096]
        v = embed([t for _i, t in part])
        chunk_ids += [i for i, _t in part]
        chunks.append(v)
        print(f"  {k + len(part)}/{len(todo)}  {time.time()-t0:.0f}s", flush=True)
    if chunks:
        thm_ids = thm_ids + chunk_ids
        thm_vecs = np.vstack([thm_vecs] + chunks)
        save_vec(kb_ids, kb_vecs, thm_ids, thm_vecs)
    print(f"index size: kb={len(kb_ids)} thm={len(thm_ids)} vectors")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "feed":
        src = sys.argv[3] if len(sys.argv) > 3 else "manual"
        if sys.argv[2].endswith(".json"):
            cards = json.load(open(sys.argv[2], encoding="utf-8"))
        else:
            cards = sys.argv[2:]
        n = feed(cards, src)
        print(f"fed {n} cards; index={len(load_vec()[0])} vectors")
    elif cmd == "embed-thm":
        embed_thm(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    else:
        print(__doc__)
