#!/usr/bin/env python3
"""Re-derive every count stated in FINDINGS.md and STATUS.md from the evidence files.

A prose count beside a computed table is a stale claim waiting for its next
regeneration. This is the guard: it reads the counts out of the documents and
compares them with the JSON evidence, failing on any mismatch.

Usage: check_consistency.py [evidence dir] [docs dir]
"""
import json
import os
import re
import sys


def derive(evidence):
    results_rel = json.load(open(os.path.join(evidence, "results_rel.json")))["results"]
    results_asan = json.load(open(os.path.join(evidence, "results_asan.json")))["results"]
    manifest = json.load(open(os.path.join(evidence, "mut.json")))
    loud = json.load(open(os.path.join(evidence, "loud_rel.json")))

    by_class = {}
    for case in manifest["cases"]:
        rel = next(r for r in results_rel if r["name"] == case["name"])
        cls = case["class"]
        by_class.setdefault(cls, {"refuse": 0, "accept": 0})
        by_class[cls][rel["probe_rel"]["verdict"]] += 1

    facts = {
        "total": len(manifest["cases"]),
        "refused": sum(c["refuse"] for c in by_class.values()),
        "loaded": sum(c["accept"] for c in by_class.values()),
        "sanitizer_lines": sum(len(r["probe_asan"]["sanitizer_lines"]) for r in results_asan),
        "verdict_disagreements": sum(
            1 for rel, asan in zip(results_rel, results_asan)
            if rel["probe_rel"]["verdict"] != asan["probe_asan"]["verdict"]),
    }
    for cls in ("header", "truncation", "bomb", "checksum", "control", "adversarial"):
        c = by_class.get(cls, {"refuse": 0, "accept": 0})
        facts[cls + "_refused"] = c["refuse"]
        facts[cls + "_total"] = c["refuse"] + c["accept"]

    loud_ok = 0
    for rec in loud:
        accepted = any("loaded v3" in x for x in rec.get("load_reply", []))
        if accepted:
            good = rec.get("readyok_after_load") and len(rec.get("bestmove", [])) == 1
        else:
            good = (rec.get("readyok_after_load") and not rec.get("bestmove")
                    and not rec.get("stderr"))
        loud_ok += 1 if good else 0
    facts["loud_cases_ok"] = loud_ok
    facts["loud_total"] = len(loud)
    return facts


CHECKS = [
    # (label, regex with ONE capture group, fact key)
    ("refused count", r"rejects (\d+) of 60 mutants", "refused"),
    ("header refused", r"Header mutants — (\d+) of 30 refused", "header_refused"),
    ("truncation refused", r"Truncation at every boundary — (\d+) of 14 refused", "truncation_refused"),
    ("bomb refused", r"Oversized dimension claims — (\d+) of 4 refused", "bomb_refused"),
]


def check_doc(path, facts):
    if not os.path.exists(path):
        return []
    text = open(path).read()
    problems = []
    for label, pattern, key in CHECKS:
        found = re.findall(pattern, text)
        for value in found:
            if int(value) != facts[key]:
                problems.append("%s: %s stated %s, evidence %d"
                                % (os.path.basename(path), label, value, facts[key]))
    return problems


def main():
    evidence = sys.argv[1] if len(sys.argv) > 1 else "evidence"
    docs = sys.argv[2] if len(sys.argv) > 2 else "."
    facts = derive(evidence)

    print("derived from evidence:")
    for key in sorted(facts):
        print("  %-24s %s" % (key, facts[key]))

    problems = []
    for name in ("FINDINGS.md", "STATUS.md"):
        problems += check_doc(os.path.join(docs, name), facts)

    if facts["sanitizer_lines"] != 0:
        problems.append("sanitizer lines is %d, not 0 — the clean bill does not hold"
                        % facts["sanitizer_lines"])
    if facts["verdict_disagreements"] != 0:
        problems.append("%d release/sanitizer verdict disagreements" % facts["verdict_disagreements"])

    if problems:
        print("\nMISMATCHES:")
        for problem in problems:
            print("  " + problem)
        return 1
    print("\nconsistent: every checked count agrees with the evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
