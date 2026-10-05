"""Parse mathlib4 .lean sources into a structured theorem library.

Each record: name, kind, statement, proof (raw tactic block), docstring,
attrs, file, line. Streaming parse -> SQLite + FTS5. Text-level only
(no Lean toolchain): statement ends at the first `:= by` / `:= <term>`
at the declaration level; proof = the indented block that follows.
"""
import os
import re
import sqlite3
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mathlib4", "Mathlib")
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mathlib.db")

DECL_RE = re.compile(
    r"^(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(theorem|lemma)\s+([A-Za-z_\u0370-\u03ff'][A-Za-z0-9_\u0370-\u03ff'!.]*)"
)
DOC_RE = re.compile(r"/--(.*?)(-/|\Z)", re.S)
ATTR_LINE = re.compile(r"^@\[")
TOP_KINDS = ("theorem", "lemma", "def", "abbrev", "instance", "structure",
             "class", "inductive", "example", "notation", "syntax",
             "namespace", "section", "end", "open", "variable", "import",
             "macro", "elab", "deriving", "attribute", "local", "set_option",
             "alias", "#eval", "#check", "#print", "run_cmd", "library_note")

BATCH = 400


def top_decl_start(line):
    """True when `line` starts a new top-level Lean command."""
    s = line.strip()
    if not s or line[0] in " -" and not s.startswith("-"):
        pass
    if not s:
        return False
    if ATTR_LINE.match(s) or s.startswith("/--") or s.startswith("/-!"):
        return True  # docstring/attr block belongs to the NEXT declaration
    first = s.split(None, 1)[0].rstrip(":")
    if first in ("private", "protected", "noncomputable"):
        parts = s.split(None, 1)
        if len(parts) < 2:
            return False
        first = parts[1].split(None, 1)[0].rstrip(":")
    return first in TOP_KINDS or DECL_RE.match(s) is not None and first in ("theorem", "lemma")


def parse_file(path):
    """Yield theorem dicts from one .lean file."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    i = 0
    n = len(lines)
    while i < n:
        m = DECL_RE.match(lines[i])
        if not m:
            i += 1
            continue
        kind, name = m.group(1), m.group(2)
        start = i
        # pull adjacent docstring / attrs (walk back over blank lines)
        doc = ""
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j >= 0 and lines[j].strip().endswith("-/"):
            k = j
            while k >= 0 and not lines[k].lstrip().startswith("/--"):
                k -= 1
            if k >= 0:
                doc = DOC_RE.search("".join(lines[k:j + 1])).group(1).strip()
                j = k - 1
        attrs = []
        while j >= 0 and ATTR_LINE.match(lines[j].strip()):
            attrs.insert(0, lines[j].strip())
            j -= 1
        # scan forward for proof start (`:= by` or `:=` at decl level)
        buf = [lines[i]]
        proof = []
        k = i + 1
        split_at = None
        while k < n:
            cur = lines[k]
            if top_decl_start(cur) and cur.strip() and not ATTR_LINE.match(cur.strip()):
                break
            buf.append(cur)
            if split_at is None and re.search(r":=\s*by\b", cur):
                split_at = len(buf)  # proof starts after this line's `:= by`
            k += 1
            if split_at is not None:
                # keep consuming the indented tactic block until dedent/next decl
                pass
        text = "".join(buf)
        if split_at is None:
            # non-tactic (term-mode) proof or unterminated; keep whole body as proof-less
            statement = text
            proof_text = ""
        else:
            flat = "".join(buf[:split_at])
            pos = flat.rfind(":=")
            statement = flat[:pos].rstrip()
            proof_text = flat[pos + 2:].lstrip() + "".join(buf[split_at:])
        yield {
            "name": name, "kind": kind,
            "statement": statement.strip(),
            "proof": proof_text.strip(),
            "docstring": doc,
            "attrs": " ".join(attrs),
            "file": rel, "line": start + 1,
        }
        i = k


def main():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE thm(
      id INTEGER PRIMARY KEY, name TEXT, kind TEXT, statement TEXT,
      proof TEXT, docstring TEXT, attrs TEXT, file TEXT, line INTEGER);
    CREATE VIRTUAL TABLE thm_fts USING fts5(
      name, statement, proof, docstring, content='thm', content_rowid='id',
      tokenize="unicode61 separators '.' tokenchars '_'");
    """)
    t0 = time.time()
    files = []
    for dirpath, _dirs, names in os.walk(ROOT):
        for fn in names:
            if fn.endswith(".lean"):
                files.append(os.path.join(dirpath, fn))
    files.sort()
    total = 0
    buf = []
    ins = "INSERT INTO thm(name,kind,statement,proof,docstring,attrs,file,line) VALUES(?,?,?,?,?,?,?,?)"
    for fp in files:
        for rec in parse_file(fp):
            buf.append(rec)
            total += 1
            if len(buf) >= BATCH:
                con.executemany(ins, [tuple(r[k] for k in
                    ("name", "kind", "statement", "proof", "docstring", "attrs", "file", "line"))
                    for r in buf])
                ids = [r[0] for r in con.execute(
                    "SELECT id FROM thm ORDER BY id DESC LIMIT ?", (len(buf),))]
                con.executemany("INSERT INTO thm_fts(rowid,name,statement,proof,docstring) VALUES(?,?,?,?,?)",
                    [(rid, r["name"], r["statement"], r["proof"], r["docstring"])
                     for rid, r in zip(reversed(ids), buf)])
                buf = []
    if buf:
        con.executemany(ins, [tuple(r[k] for k in
            ("name", "kind", "statement", "proof", "docstring", "attrs", "file", "line")) for r in buf])
        con.execute("INSERT INTO thm_fts(rowid,name,statement,proof,docstring) SELECT id,name,statement,proof,docstring FROM thm WHERE id > (SELECT COALESCE(MAX(rowid),0) FROM thm_fts)")
    con.commit()
    cnt = con.execute("SELECT COUNT(*) FROM thm").fetchone()[0]
    withproof = con.execute("SELECT COUNT(*) FROM thm WHERE proof != ''").fetchone()[0]
    print(f"files={len(files)} theorems={cnt} with_proof={withproof} "
          f"elapsed={time.time()-t0:.0f}s db={os.path.getsize(DB)/1e6:.0f}MB")


if __name__ == "__main__":
    main()
