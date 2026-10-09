"""Feed miniF2F statements into the selflearner knowledge table.

Each miniF2F problem file becomes one knowledge card:
  text    = the full Lean source (imports stripped, sorry kept — the
            statement is the signal, not the proof)
  lang    = "lean4"
  source  = "minif2f/<category>/<file>"

Usage: python feed_minif2f.py <path-to-MiniF2F-dir>
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ingest import feed


def strip_imports(src):
    """Keep the theorem statement + proof skeleton; drop imports and
    set_option boilerplate (the statement is the retrieval signal)."""
    lines = []
    for ln in src.splitlines():
        if ln.startswith("import ") or ln.startswith("set_option "):
            continue
        lines.append(ln)
    return "\n".join(lines).strip()


def main(minif2f_dir):
    cards = []
    for cat in ("Test", "Valid"):
        pattern = os.path.join(minif2f_dir, "MiniF2F", cat, "*.lean")
        for path in sorted(glob.glob(pattern)):
            name = os.path.splitext(os.path.basename(path))[0]
            src = open(path, encoding="utf-8", errors="replace").read()
            body = strip_imports(src)
            if not body:
                continue
            cards.append({"text": f"[{name}]\n{body}",
                          "lang": "lean4",
                          "source": f"minif2f/{cat}/{name}"})
    print(f"feeding {len(cards)} miniF2F statements...")
    feed(cards, source="minif2f")
    print("done")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
