"""Propose-check loop at the library edge (Phase 2).

Round structure:
  1. SEED: sample related theorem groups from the library (same file,
     coherent topic).
  2. PROPOSE: LLM sees the statements + proof styles, proposes one new
     candidate lemma (Lean 4, mathlib import) with a proof.
  3. CHECK: `lake env lean` the candidate in the mathlib environment.
     PASS = exit 0, no sorry/admit.
  4. ADMIT: passing candidates are written back to mathlib.db with
     provenance='proposed'. Failures logged with the compiler error.

Usage: python propose_check.py [n_rounds]
"""
import os
import re
import sqlite3
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "mathlib.db")
MATHLIB = os.path.join(ROOT, "mathlib4")
CAND = os.path.join(MATHLIB, "Selflearner.lean")
KEY_FILE = os.path.expanduser("~/.intuition/ark_key")

sys.path.insert(0, r"D:\djr82\intuition-mechanism")


def load_llm():
    """Import the shared intuition llm_client, supplying its key."""
    key = open(KEY_FILE, encoding="utf-8").read().strip()
    os.environ.setdefault("ARK_API_KEY", key)
    import llm_client  # noqa: PLC0415
    return llm_client.ask


def ask_effort(prompt, effort="low", temperature=0.4, max_tokens=8192):
    """Same Volcano Responses API but with configurable reasoning effort.

    The shared client hardcodes minimal; proposal quality is the
    bottleneck, so spend reasoning tokens here. 429s back off 60s/attempt."""
    import json as _json
    import time as _time
    import urllib.error as _uerr
    import urllib.request as _urllib  # noqa: PLC0415
    from llm_client import BASE, KEY, MODEL  # noqa: PLC0415
    body = _json.dumps({
        "model": MODEL,
        "input": prompt,
        "temperature": temperature,
        "max_output_tokens": max_tokens,
        "reasoning": {"effort": effort},
    }).encode()
    for attempt in range(3):
        req = _urllib.Request(
            BASE + "/responses", data=body,
            headers={"Authorization": f"Bearer {KEY}",
                     "Content-Type": "application/json"})
        try:
            with _urllib.urlopen(req, timeout=900) as r:
                data = _json.loads(r.read())
            parts = []
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            parts.append(c["text"])
            return "\n".join(parts)
        except _uerr.HTTPError as ex:
            if ex.code == 429:
                _time.sleep(60 * (attempt + 1))
                continue
            raise
    return ""


PROMPT = """You are extending a Lean 4 (mathlib) theorem library.

Here are related existing theorems (statements and proof excerpts):

{context}

Propose ONE new lemma that is (a) not already in mathlib, (b) a small
step adjacent to these (a corollary, a specialized variant, a converse
that actually holds), and (c) provable with mathlib tactics in under
~15 lines.

Answer with ONLY a fenced ```lean block containing the full lemma,
including its `import Mathlib.Tactic` line. No sorry, no admit."""


def sample_seeds(con, k=4):
    """Pick k theorems from one file (coherent topic) that have proofs."""
    file_, = con.execute(
        """SELECT file FROM thm WHERE proof != '' AND kind='theorem'
           GROUP BY file HAVING COUNT(*) >= 20 ORDER BY RANDOM() LIMIT 1"""
    ).fetchone()
    rows = con.execute(
        """SELECT name, statement, SUBSTR(proof, 1, 300) FROM thm
           WHERE file = ? AND proof != '' ORDER BY RANDOM() LIMIT ?""",
        (file_, k),
    ).fetchall()
    return file_, rows


def check_candidate(code):
    """Write candidate, run lean. Returns (ok, log)."""
    with open(CAND, "w", encoding="utf-8", newline="\n") as f:
        f.write(code + "\n")
    p = subprocess.run(
        ["lake", "env", "lean", "Selflearner.lean"],
        cwd=MATHLIB, capture_output=True, text=True, timeout=600,
        encoding="utf-8", errors="replace",
    )
    log = (p.stdout + p.stderr)[-3000:]
    ok = p.returncode == 0
    if ok and re.search(r"\b(sorry|admit)\b", code):
        ok = False
        log = "SORRY/ADMIT in accepted text\n" + log
    return ok, log


def novelty_check(con, code):
    """Lean guarantees TRUE; this gate approximates NEW.

    Rejects (a) name collisions, (b) one-line `exact <existing>` restatements
    (the dominant failure seen in round 3: it re-declared an existing
    mathlib theorem verbatim)."""
    m = re.search(r"^(?:private\s+|protected\s+)*"
                  r"(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'!]*)", code, re.M)
    if not m:
        return False, "no top-level name"
    name = m.group(1)
    if con.execute("SELECT 1 FROM thm WHERE name = ? LIMIT 1", (name,)).fetchone():
        return False, f"name collision: {name}"
    proof = code.split(":=", 1)[-1].strip() if ":=" in code else ""
    if re.fullmatch(r"exact\s+[A-Za-z_.][\w.'\s]*", proof) and len(proof) < 120:
        return False, "one-line exact restatement"
    if re.search(r":\s*(True|False)\b\s*:?=", code):
        return False, "trivial True/False statement"  # round-2 lesson: `fixed`
    return True, "ok"


def admit(con, code, file_, log):
    m = re.search(r"^(?:private\s+|protected\s+)*"
                  r"(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'!]*)", code, re.M)
    name = m.group(1) if m else f"anon_{int(time.time())}"
    body = code.split("\n")
    stmt_lines, proof_lines, seen_by = [], [], False
    for ln in body:
        if not seen_by:
            stmt_lines.append(ln)
            if re.search(r":=\s*by\b", ln):
                seen_by = True
        else:
            proof_lines.append(ln)
    con.execute(
        """INSERT INTO thm(name,kind,statement,proof,docstring,attrs,file,line)
           VALUES(?,'lemma',?,?,?,'provenance=proposed',?,0)""",
        (name, "\n".join(stmt_lines).strip(), "\n".join(proof_lines).strip(),
         f"Selflearner-proposed (verified {time.strftime('%Y-%m-%d')})", file_),
    )
    rowid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute("INSERT INTO thm_fts(rowid,name,statement,proof,docstring) "
                "SELECT id,name,statement,proof,docstring FROM thm WHERE id=?",
                (rowid,))
    con.commit()
    return name


def one_round(con, ask, rnd, prev=None, ask_fn=None, retries=2):
    """One propose->check cycle, with compile-error feedback retries.

    ask_fn(prompt) -> reply; defaults to `ask` (minimal effort). Passing
    ask_effort upgrades proposal quality; retries feed the Lean errors
    back to the proposer."""
    propose = ask_fn or (lambda p: ask(p, temperature=0.4, max_tokens=4096))
    file_, seeds = sample_seeds(con)
    ctx = "\n\n".join(
        f"-- {n}\n{s}\nproof sketch: {p}" for n, s, p in seeds)
    if prev:
        ctx += ("\n\nA lemma this session grew earlier (already verified, "
                "you may cite it):\n" + prev)
    reply = propose(PROMPT.format(context=ctx))
    m = re.search(r"```lean\n(.*?)```", reply, re.S)
    if not m:
        return dict(rnd=rnd, file=file_, ok=False, why="no lean block")
    code = m.group(1).strip()
    for attempt in range(retries + 1):
        ok, log = check_candidate(code)
        if ok:
            break
        if attempt < retries:
            fix_prompt = (
                "Your Lean 4 lemma failed to compile with:\n\n" + log[-1500:] +
                "\n\nFix it. Answer with ONLY a fixed ```lean block "
                "(full lemma, same goal). No sorry, no admit.")
            reply = propose(fix_prompt)
            m = re.search(r"```lean\n(.*?)```", reply, re.S)
            if not m:
                break
            code = m.group(1).strip()
    if ok:
        new, why = novelty_check(con, code)
        if not new:
            return dict(rnd=rnd, file=file_, ok=False, why=f"DUP {why}")
        name = admit(con, code, file_, log)
        return dict(rnd=rnd, file=file_, ok=True, name=name, code=code,
                    tries=attempt + 1)
    return dict(rnd=rnd, file=file_, ok=False, why=log[-500:])


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    effort = sys.argv[2] if len(sys.argv) > 2 else "minimal"
    ask = load_llm()
    ask_fn = (lambda p: ask_effort(p, effort=effort)) if effort != "minimal" \
        else None
    con = sqlite3.connect(DB)
    n0 = con.execute("SELECT COUNT(*) FROM thm").fetchone()[0]
    passed = failed = 0
    prev = None
    for rnd in range(1, rounds + 1):
        try:
            r = one_round(con, ask, rnd, prev, ask_fn)
        except Exception as e:  # noqa: BLE001
            r = dict(rnd=rnd, ok=False, why=f"EXC {e!r}"[:300])
        passed += r["ok"]
        failed += not r["ok"]
        if r["ok"]:
            prev = r.get("code", "")[:1500]
        tag = f"PASS {r.get('name')} (tries={r.get('tries', 1)})" if r["ok"] \
            else f"FAIL {r.get('why', '')[:120]}"
        print(f"[{rnd}/{rounds}] {r.get('file','?')} {tag}", flush=True)
    n1 = con.execute("SELECT COUNT(*) FROM thm").fetchone()[0]
    print(f"library: {n0} -> {n1} (+{n1-n0}), pass {passed} / fail {failed}")


if __name__ == "__main__":
    main()
