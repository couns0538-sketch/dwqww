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
        "pat_p_isready": sum(1 for r in base["results"]
                             if r["cls"] == "position_fen" and r["pattern"] == "P_isready"),
        "pat_p_direct": sum(1 for r in base["results"]
                            if r["cls"] == "position_fen" and r["pattern"] == "P_direct"),
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

    # Any "P_isready=N" / "P_direct=N" stated in prose must match the corpus.
    for text, name in ((md, "FUZZ.md"), (status, "STATUS.md")):
        for m in re.finditer(r"P_isready=(\d+)", text):
            got = int(m.group(1))
            if got != facts["pat_p_isready"]:
                problems.append(f"{name}: P_isready={got} but corpus has "
                                f"{facts['pat_p_isready']}")
        for m in re.finditer(r"P_direct=(\d+)", text):
            got = int(m.group(1))
            if got != facts["pat_p_direct"]:
                problems.append(f"{name}: P_direct={got} but corpus has "
                                f"{facts['pat_p_direct']}")

    # The stated 0000 split must appear as base/integ, not as one number.
    for m in re.finditer(r"`bestmove 0000` \| (\d+) \| (\d+)", md):
        if int(m.group(1)) != facts["zero_base"] or int(m.group(2)) != facts["zero_integ"]:
            problems.append(f"0000 row {m.groups()} vs evidence "
                            f"({facts['zero_base']},{facts['zero_integ']})")

    # The corrections tally must agree between the report and the summary.
    tl = re.search(r"(\w+) items, enumerated", md)
    ts = re.search(r"(\w+) items, enumerated", status)
    word2num = {"six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                "eleven": 11, "twelve": 12}
    if tl and ts:
        a, b = tl.group(1).lower(), ts.group(1).lower()
        if a != b:
            problems.append(f"corrections tally disagrees: FUZZ.md='{a}', STATUS.md='{b}'")
        elif a in word2num:
            facts["corrections"] = word2num[a]
    elif tl or ts:
        problems.append("corrections tally present in one file and not the other")

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
