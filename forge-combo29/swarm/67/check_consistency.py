#!/usr/bin/env python3
"""Consistency check: every count stated in the prose must match the evidence.

This exists because a stale literal ('49 refusals' after the corpus grew to 56)
survived two regenerations of FUZZ.md undetected. A report whose tables are
computed and whose prose is typed has a silent failure mode; this closes it.
"""
import json
import re
import sys

BASE = "evidence-asan-base.json"
INTEG = "evidence-asan-integrate.json"


def main() -> int:
    base = json.load(open(BASE))
    integ = json.load(open(INTEG))
    md = open("FUZZ.md", encoding="utf-8").read()
    status = open("STATUS.md", encoding="utf-8").read()

    facts = {
        "cases": len(base["results"]),
        "cases_integ": len(integ["results"]),
        "crashes": sum(1 for r in base["results"] if r["sanitizer"] or r["exit"] not in (0, None)),
        "hangs": sum(1 for r in base["results"] if r["hang"]),
        "sanitizer": sum(1 for r in base["results"] if r["sanitizer"]),
        "bad_exit": sum(1 for r in base["results"] if r["exit"] not in (0, None)),
        "unbounded": sum(1 for r in base["results"] if r.get("unbounded")),
        "zero_base": sum(1 for r in base["results"] if r["illegal_0000"]),
        "zero_integ": sum(1 for r in integ["results"] if r["illegal_0000"]),
        "refusals": sum(len(r["refusal"]) for r in base["results"]),
    }

    print("evidence facts:")
    for k, v in facts.items():
        print(f"  {k} = {v}")

    problems = []

    # Every number that appears next to a claim word must equal its fact.
    checks = [
        (md,    r"\*\*Crashes[^*]*: (\d+)\*\* across (\d+) cases", ("crashes", "cases")),
        (md,    r"\*\*Hangs[^*]*: (\d+)\*\* across (\d+) cases",    ("hangs", "cases")),
        (md,    r"Across the whole corpus, \*\*(\d+)\*\* refusal",  ("refusals",)),
        (status, r"\| cases \| (\d+) \| (\d+) \|",                  ("cases", "cases_integ")),
    ]
    for text, pattern, keys in checks:
        m = re.search(pattern, text)
        if not m:
            problems.append(f"pattern not found: {pattern}")
            continue
        for got, key in zip(m.groups(), keys):
            if int(got) != facts[key]:
                problems.append(f"{pattern}: stated {got}, evidence {facts[key]} ({key})")

    # Any bare "N refusals" or "N cases" in prose must match.
    for text, name in ((md, "FUZZ.md"), (status, "STATUS.md")):
        for m in re.finditer(r"(\d+) refusals", text):
            if int(m.group(1)) != facts["refusals"]:
                problems.append(f"{name}: '{m.group(0)}' but evidence has {facts['refusals']}")
        for m in re.finditer(r"(\d+)-case corpus", text):
            if int(m.group(1)) != facts["cases"]:
                problems.append(f"{name}: '{m.group(0)}' but evidence has {facts['cases']}")

    # The 0000 split must appear as base/integ, not as one number.
    for m in re.finditer(r"`bestmove 0000` \| (\d+) \| (\d+)", md):
        if int(m.group(1)) != facts["zero_base"] or int(m.group(2)) != facts["zero_integ"]:
            problems.append(f"0000 row {m.groups()} vs evidence "
                            f"({facts['zero_base']},{facts['zero_integ']})")

    if problems:
        print("\nINCONSISTENCIES:")
        for p in problems:
            print("  -", p)
        print("\nRESULT: FAIL")
        return 1
    print("\nRESULT: PASS — no stated count disagrees with the evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
