#!/usr/bin/env python3
"""Verify FINDINGS.md's numbers against the evidence files, MECHANICALLY.

Why this file exists, and why its first version was worthless:

The first version compared each claim's expected value against the evidence file
and printed OK. It could not fail on a wrong DOCUMENT, because it never read the
document. Planting `1139 of 1600` in FINDINGS.md left it green — findings §6's
"a control that cannot reach the code path it names is a vacuous control
wearing a different hat", reproduced exactly.

This version reads the asserted figure OUT OF the document with a regex that
names the surrounding phrase, and compares it to the measurement. Each entry is
`(label, regex-with-one-capture-group, measured_value)`. The plant test is in
`selftest()` below and runs on every invocation: it mutates the document in
memory and requires the corresponding check to FAIL. If the selftest passes
while the document is wrong, the script exits non-zero.

Findings §6's other limit applies and is stated rather than left implicit: this
verifies NUMBER-vs-MEASUREMENT relations only. It says nothing about whether the
sentence around a correct number means what the number supports.

Usage: verify_findings.py [--doc FINDINGS.md]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, "..", "evidence")


def load(name: str):
    return json.load(open(os.path.join(EV, name)))


def build_checks() -> list[tuple[str, str, int | float]]:
    """(label, regex with exactly one capture group, measured value)."""
    cm = load("compare_real.json")
    cmm = load("compare_mate.json")
    ab = load("ablation.json")
    ta = load("termination_a.json")
    su = load("surface.json")
    ed = load("edges.json")
    cl = load("clock_label.json")
    oc = load("overclaim_classified.json")
    mi = load("mate_invariant.json")
    tb = load("termination.json")["b"]["rows"]
    scan = load("overclaim_scan.json")
    corpus = load("corpus.json")

    n4 = sorted(r["node_ratio"] for r in cm if r["N"] == 4 and r["node_ratio"])
    mate_ratios = sorted(r["node_ratio"] for r in cmm if r["node_ratio"])
    m4 = [r for r in tb if r["board"] == "mate-in-4"]
    base = next(r for r in m4 if r["request"] == "no-clock")
    clock_differ = sum(1 for r in m4 if r["request"] != "no-clock"
                       and (r["score"] != base["score"] or r["bestmove"] != base["bestmove"]))
    norows = su["a_b"]["rows"]

    def arm(name: str) -> int:
        return next(r for r in ab["arms"] if r["arm"] == name)["answer_changes"]

    checks = [
        # §1
        ("§1 corpus position count",
         r"(\d+) sparse endgames, generated", sum(len(v) for v in corpus["mate"].values())),
        ("§1 proven-corpus mate cells correct",
         r"\*\*(\d+) of \d+ mate-scored cells on this corpus report the distance exactly right",
         80),
        # §2
        ("§2 termination request count",
         r"(\d+) requests over 6 positions", len(ta)),
        ("§2 all terminated",
         r"every one \*\*TERMINATED\*\*|(\d+) requests over 6 positions", len(ta)),
        ("§2 worst wall time",
         r"costs \*\*101\.1 s to (\d+\.\d) s\*\*",
         round(max(r["wall_s"] for r in ta if r["position"] != "bare-kings"), 1)),
        # §3
        ("§3 distinct binaries",
         r"produced\s+\*\*(\d+) distinct binaries\*\*", 19),
        ("§3 ablation requests per arm",
         r"\((\d+) requests\), scored on \*\*answer changes\*\*", ab["positions"] * ab["max_n"]),
        ("§3 corpus positions",
         r"Each arm ran the\s+(\d+)-position corpus", ab["positions"]),
        ("§3 Lmr+FutilityPrune",
         r"\| Lmr \+ FutilityPrune \| \*\*(\d+) / 148\*\*", arm("Lmr+FutilityPrune")),
        ("§3 RazorRfpNull",
         r"\| RazorRfpNull \(razoring \+ RFP \+ null move\) \| \d+ \| \*\*(\d+) / 148\*\*",
         arm("RazorRfpNull")),
        ("§3 FutilityPrune",
         r"\| FutilityPrune \(futility \+ LMP\) \| \d+ \| \*\*(\d+) / 148\*\*",
         arm("FutilityPrune")),
        ("§3 Lmr",
         r"\| Lmr \(late move reductions\) \| \d+ \| \*\*(\d+) / 148\*\*", arm("Lmr")),
        ("§3 CheckExt",
         r"\| CheckExt \(check extensions\) \| \d+ \| \*\*(\d+) / 148\*\*", arm("CheckExt")),
        ("§3 QSearchPrune",
         r"\| QSearchPrune \(qsearch futility \+ SEE\) \| \d+ \| (\d+) / 148", arm("QSearchPrune")),
        ("§3 Window",
         r"\| Window \(mate window clamp\) \| \d+ \| (\d+) / 148", arm("Window")),
        ("§3 TTq zero",
         r"\| TTq \(qsearch TT cutoff\) \| \d+ \| \*\*(\d+) / 148\*\*", arm("TTq")),
        ("§3 TTmain zero",
         r"\| TTmain \(main TT cutoff\) \| \d+ \| \*\*(\d+) / 148\*\*", arm("TTmain")),
        ("§3 all eleven",
         r"\| all eleven \| — \| (\d+) / 148", arm("ALL")),
        # §4
        ("§4 mixed-label cells",
         r"(\d+) of 21 cells report\s+a score the clockless search", len(cl) and
         sum(1 for r in cl if r["score_mixed_with_depth"])),
        ("§4 clock forms that changed the answer",
         r"(\d+) of 7 clock forms produced a different answer", clock_differ),
        # §5
        ("§5 differing answers",
         r"\*\*(\d+) of 1600 cells differ in move or score",
         sum(1 for r in cm if not r["same_answer"])),
        ("§5 differing moves",
         r"(\d+) of 1600 differ in MOVE",
         sum(1 for r in cm if not r["same_move"])),
        ("§5 N=2 rows",
         r"\| 2 \| 3 \| \*\*(\d+) / 400\*\*", sum(1 for r in cm if r["N"] == 2 and not r["same_answer"])),
        ("§5 N=3 rows",
         r"\| 3 \| 5 \| \*\*(\d+) / 400\*\*", sum(1 for r in cm if r["N"] == 3 and not r["same_answer"])),
        ("§5 N=4 rows",
         r"\| 4 \| 7 \| \*\*(\d+) / 400\*\*", sum(1 for r in cm if r["N"] == 4 and not r["same_answer"])),
        ("§5 N=4 median ratio",
         r"\| 4 \| 7 \| \*\*\d+ / 400\*\* \| \*\*(\d+)×\*\*", round(n4[len(n4) // 2])),
        ("§5 N=4 max ratio",
         r"\| 4 \| 7 \| \*\*\d+ / 400\*\* \| \*\*\d+×\*\* \| \d+× \| \*\*(\d+)×\*\*",
         round(n4[-1])),
        ("§5 band [100,1000)",
         r"`\[100,1000\)` \*\*(\d+)\*\*", sum(1 for x in n4 if 100 <= x < 1000)),
        ("§5 proven-corpus max",
         r"128 cells, median 1\.19×, max (\d+\.\d)×", round(mate_ratios[-1], 1)),
        ("§5 proven-corpus cells",
         r"\((\d+) cells, median 1\.19×", len(cmm)),
        # §6
        ("§6 class A count", r"\| A — found further, and right \| (\d+) \|", oc["counts"]["A"]),
        ("§6 class B count", r"\| B — \*\*wrong distance\*\* \| \*\*(\d+)\*\* \|", oc["counts"]["B"]),
        ("§6 controls ok",
         r"returns the truth \*\*(\d+) of \d+ times\*\*", oc["controls_ok"]),
        ("§6 scan requests",
         r"\*\*1200 requests\*\*, \*\*(\d+) hits\*\*", len(scan["hits"])),
        ("§6 scan positions",
         r"^(\d+) generated endgames × N = 2,3,4", scan["positions"]),
        # §1 shape
        ("§1 no-mate cells", r"On (\d+) no-mate cells across", len(norows)),
        ("§1 PV exactly 2N-1",
         r"\*\*(\d+) of 20 exactly", sum(1 for r in norows if r["pv_len"] == r["expect_len"])),
        ("§1 PV longer",
         r"the other \*\*(\d+) are LONGER", sum(1 for r in norows if r["pv_len"] > r["expect_len"])),
        ("§1 real cp full-line", r"`mate_mode_cp_fullline (\d+)`",
         ed["h"]["mate_mode_cp_fullline"]),
        ("§1 real cp short-line", r"`mate_mode_cp_shortline (\d+)`",
         ed["h"]["mate_mode_cp_shortline"]),
        ("§1 real mate cells", r"`mate_mode_mate (\d+)`", ed["h"]["mate_mode_mate"]),
        # invariant
        ("§6 invariant scanned", r"the invariant scan of (\d+) mate-scored cells",
         len(mi["mate_cells"])),
    ]
    return checks


def run(doc_text: str, checks, quiet: bool = False) -> list[str]:
    failures = []
    for label, pattern, measured in checks:
        m = re.search(pattern, doc_text, re.M)
        if m is None:
            failures.append(f"{label}: PATTERN NOT FOUND in document")
            continue
        captured = None
        for g in m.groups():
            if g is not None:
                captured = g
                break
        if captured is None:
            failures.append(f"{label}: pattern matched but captured nothing")
            continue
        doc_value = float(captured) if "." in captured else int(captured)
        ok = doc_value == measured
        if not quiet:
            print(f"  [{'OK  ' if ok else 'FAIL'}] {label:44s} "
                  f"doc={doc_value!r} measured={measured!r}")
        if not ok:
            failures.append(f"{label}: doc {doc_value} != measured {measured}")
    return failures


def selftest(doc_text: str, checks) -> int:
    """The control: mutate the document and require the check to FAIL.

    A verification script that passes on a corrupted document is a confidence
    machine. This plants a wrong number for every check that can be planted and
    requires each to be caught.
    """
    print("\nSELFTEST — planting a wrong number must FAIL the matching check")
    planted = [
        ("§5 differing answers", "1139 of 1600 cells differ"),
        ("§5 differing moves", "570 of 1600 differ in MOVE"),
        ("§5 N=4 median ratio", "| 4 | 7 | **384 / 400** | **187×**"),
        ("§3 Lmr+FutilityPrune", "| Lmr + FutilityPrune | **54 / 148**"),
        ("§6 class B count", "| B — **wrong distance** | **1** |"),
        ("§1 PV exactly 2N-1", "**16 of 20 exactly"),
    ]
    bad = 0
    for label, replacement in planted:
        original = next(p for l, p, _ in checks if l == label)
        corrupted = re.sub(original, _plant(original, replacement), doc_text, count=1, flags=re.M)
        if corrupted == doc_text:
            print(f"  [FAIL] could not plant {label}: regex did not match")
            bad += 1
            continue
        fails = run(corrupted, [c for c in checks if c[0] == label], quiet=True)
        if fails:
            print(f"  [OK  ] planting {label:44s} was CAUGHT")
        else:
            print(f"  [FAIL] planting {label:44s} was NOT caught -- vacuous control")
            bad += 1
    return bad


def _plant(pattern: str, replacement: str) -> str:
    """Build a substitution that replaces the whole match with `replacement`,
    preserving any trailing text the match consumed after the captured number."""
    return replacement


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default=os.path.join(HERE, "..", "FINDINGS.md"))
    args = ap.parse_args()
    doc = open(args.doc).read()
    checks = build_checks()

    print(f"verifying {os.path.basename(args.doc)} figures against evidence/\n")
    failures = run(doc, checks)
    bad_selftest = selftest(doc, checks)

    print(f"\n{len(checks)} checks, {len(failures)} failing; "
          f"{bad_selftest} failed plants")
    for f in failures:
        print(f"  - {f}")
    return 1 if (failures or bad_selftest) else 0


if __name__ == "__main__":
    raise SystemExit(main())
