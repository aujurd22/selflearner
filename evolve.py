"""Self-evolving judge + outer-loop strategy adaptation — concrete implementation.

Three components (each independently testable):

  1. judge_evolve()  — analyze judge misjudgment patterns → generate
     new rubric rules → inject into judge prompt (DynamicRubric style)
  2. outer_loop()    — analyze log.jsonl → stats per domain/type →
     generate strategy modifications → write strategy.json
  3. Both feed into the next loop's prompt/gates

Usage:
  python evolve.py --analyze <log.jsonl>     # outer loop analysis
  python evolve.py --evolve-judge <log.jsonl> # judge rule evolution
  python evolve.py --all <log.jsonl>          # both
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DOMAIN_MAP = {
    "Algebra": "algebra", "Topology": "topology", "NumberTheory": "number-theory",
    "Analysis": "analysis", "Geometry": "geometry", "Logic": "logic",
    "Order": "order", "Combinatorics": "combinatorics", "Data": "data",
}


def parse_log(log_path):
    rounds = []
    for line in open(log_path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            if isinstance(r, dict) and r.get("rnd"):
                rounds.append(r)
        except ValueError:
            pass
    return rounds


def domain_of(file_path):
    """Extract domain from mathlib-style file path (e.g. NumberTheory/...)."""
    for k, v in DOMAIN_MAP.items():
        if k in file_path:
            return v
    return "unknown"


def analyze_inner_loop(log_path):
    """Outer loop step 1: compute per-domain pass rates and failure modes."""
    rounds = parse_log(log_path)
    by_domain = defaultdict(lambda: {"ok": 0, "fail": 0, "errors": []})
    for r in rounds:
        dom = domain_of(r.get("file", ""))
        if r.get("ok"):
            by_domain[dom]["ok"] += 1
        else:
            by_domain[dom]["fail"] += 1
            why = str(r.get("why", ""))[:80]
            err_type = why.split(":")[0].strip() if ":" in why else why[:30]
            by_domain[dom]["errors"].append(err_type)
    return by_domain


def generate_strategy_changes(by_domain):
    """Outer loop step 2: generate actionable strategy modifications."""
    changes = []
    total_ok = sum(d["ok"] for d in by_domain.values())
    total = sum(d["ok"] + d["fail"] for d in by_domain.values())
    for dom, d in sorted(by_domain.items()):
        rate = d["ok"] / max(1, d["ok"] + d["fail"])
        if d["fail"] >= 3 and rate < 0.3:
            changes.append(
                f"Domain '{dom}' has low pass rate ({rate:.0%}, "
                f"{d['ok']}/{d['ok']+d['fail']}). "
                f"Top errors: {d['errors'][:3]}. "
                f"Consider reducing weight or skipping this domain."
            )
        elif rate > 0.7 and d["ok"] >= 3:
            changes.append(
                f"Domain '{dom}' has high pass rate ({rate:.0%}, "
                f"{d['ok']}/{d['ok']+d['fail']}). "
                f"Consider increasing sampling weight."
            )
    return changes


def generate_judge_rules(log_path, report_path=None):
    """Analyze judge/admission outcomes to generate new evaluation rules."""
    rounds = parse_log(log_path)
    # patterns: which types of candidates were rejected and why
    fail_patterns = defaultdict(int)
    for r in rounds:
        if r.get("ok"):
            continue
        why = str(r.get("why", ""))
        if "unknown identifier" in why:
            fail_patterns["unknown_identifier"] += 1
        elif "unexpected token" in why:
            fail_patterns["syntax_error"] += 1
        elif "type mismatch" in why or "expected type" in why:
            fail_patterns["type_mismatch"] += 1
        elif "DUP" in why:
            fail_patterns["duplicate"] += 1
        elif "AXIOM" in why:
            fail_patterns["axiom_violation"] += 1
        else:
            fail_patterns["other"] += 1
    rules = []
    for pattern, count in sorted(fail_patterns.items(), key=lambda x: -x[1]):
        if count >= 3:
            rules.append(
                f"Pattern '{pattern}' occurred {count} times. "
                f"Add evaluation rule: flag candidates with this pattern "
                f"early (pre-compile if possible)."
            )
    return rules, fail_patterns


def evolve_judge_prompt(old_rules, new_rules):
    """Generate updated judge prompt section with evolved rules."""
    section = "\n## Additional evaluation rules (evolved):\n"
    for r in new_rules:
        section += f"- {r}\n"
    return section


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyze", dest="log_path", help="log.jsonl to analyze")
    ap.add_argument("--evolve-judge", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if not args.log_path:
        ap.print_help()
        sys.exit(1)

    by_domain = analyze_inner_loop(args.log_path)
    changes = generate_strategy_changes(by_domain)

    print("=== Outer loop: strategy changes ===")
    for c in changes:
        print(f"  - {c}")

    rules, patterns = generate_judge_rules(args.log_path)
    print("\n=== Judge rule evolution ===")
    print("Failure patterns:", dict(patterns))
    for r in rules:
        print(f"  - {r}")

    if args.evolve_judge or args.all:
        out = {
            "strategy_changes": changes,
            "judge_rules": rules,
            "failure_patterns": dict(patterns),
            "by_domain": {k: dict(v) for k, v in by_domain.items()},
        }
        json.dump(out, open("evolution_output.json", "w"), indent=1,
                  default=str)
        print("\nWritten to evolution_output.json")


if __name__ == "__main__":
    main()
