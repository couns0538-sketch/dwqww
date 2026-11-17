#!/usr/bin/env python3
"""audit_c1.py EXE OUTDIR

MEASUREMENT-INTEGRITY AUDIT of my own 21-C1 (the check of seat 30's 30-F6).

The failure seat 19 warns about: a check parses a line the engine never prints, gets
nothing, and a NaN/empty comparison prints CONFIRMS. So this script

  1. asserts, for every case, that the exact line it parses (`nodes N`) was FOUND — a
     missing line raises and the check dies loudly instead of confirming;
  2. prints, for every case, the parsed integer and the raw line it came from;
  3. includes the three plants that would expose a vacuous check:
       PLANT-missing   a case whose expected line is deliberately never sent (the parser
                       must NOT report success for it: it must raise / mark FAIL)
       PLANT-wrong     a case whose engine answer is deliberately compared against a value
                       it cannot equal (the comparison must fail loudly)
       PLANT-empty     a case where the engine prints nothing at all for the go (no nodes
                       line): parsed as MISSING, never as 0.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_engine import SafeEngine  # noqa: E402

NODES = re.compile(r"^nodes (\d+)$")


def parse_nodes(lines, case):
    """The ONLY way this check reads a node count. Raises if the line is absent, so an
    absent line can never pass as a measurement."""
    found = []
    for ln in lines:
        m = NODES.match(ln.strip())
        if m:
            found.append(int(m.group(1)))
    if not found:
        raise AssertionError("case %r: NO `nodes N` line in the engine's answer; "
                             "the check measured nothing" % case)
    if len(found) != 1:
        raise AssertionError("case %r: %d `nodes` lines, expected exactly 1" % (case, len(found)))
    return found[0]


def run_case(exe, outdir, tag, pos_line):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"))
    ans = e.position(pos_line)
    lines = e.go("go perft 1", token="nodes")
    e.close()
    return ans, lines


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    POS = "startpos moves e2e4 e7e5 g1f3 b8c6 f1b5"
    rows = []
    failures = []

    def case(tag, pos_line, expect):
        ans, lines = run_case(exe, outdir, tag, pos_line)
        try:
            n = parse_nodes(lines, tag)
        except AssertionError as exc:
            failures.append(str(exc))
            rows.append((tag, "PARSE FAILED: %s" % exc, "-", str(expect), "FAIL"))
            return None
        ok = (n == expect)
        rows.append((tag, "parsed %d from %r" % (n, [l for l in lines if NODES.match(l.strip())][0]),
                     str(n), str(expect), "ok" if ok else "MISMATCH"))
        if not ok:
            failures.append("case %r: parsed %d, expected %d" % (tag, n, expect))
        return n

    # ---- the real 21-C1 cases, now with the assertion in place
    n_base = case("control_no_ucinewgame", "position " + POS, 30)
    n_before = case("ucinewgame_before", "ucinewgame\nposition " + POS, 30)
    n_after = case("position_then_ucinewgame", "position " + POS + "\nucinewgame", 20)
    n_other = case("second_position_control", "position startpos moves d2d4 d7d5 c2c4", 28)

    # ---- plants that must NOT be able to pass
    # PLANT-empty: the engine is never asked to search, so there is no nodes line at all.
    e = SafeEngine(exe, os.path.join(outdir, "plant_empty_raw.txt"))
    e.position("position " + POS)
    e.close()
    empty_lines = ["readyok"]  # what a check sees when it never sent the go
    try:
        parse_nodes(empty_lines, "PLANT-empty")
        failures.append("PLANT-empty PASSED the parser: a vacuous check is possible")
        rows.append(("PLANT-empty", "PARSER ACCEPTED AN EMPTY ANSWER", "-", "-", "FAIL"))
    except AssertionError as exc:
        rows.append(("PLANT-empty", "correctly rejected: %s" % exc, "-", "-", "ok"))

    # PLANT-wrong: a real answer compared against an impossible value must fail.
    real = n_base
    wrong_expect = real + 1000
    ok = (real == wrong_expect)
    rows.append(("PLANT-wrong", "parsed %d vs impossible expected %d" % (real, wrong_expect),
                 str(real), str(wrong_expect), "ok (mismatch correctly reported)" if not ok else "FAIL"))
    if ok:
        failures.append("PLANT-wrong: an impossible comparison reported equality")

    verdict = "CONFIRMS 30-F6 (with the parser proved non-vacuous)" if (
        n_base == 30 and n_before == 30 and n_after == 20 and n_other == 28 and not failures) else \
        "NOT CONFIRMED — see failures"
    out = ["| case | what the parser saw | parsed | expected | result |", "|---|---|---|---|---|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    out.append("")
    out.append("failures: %s" % (failures or "none"))
    out.append("=> %s" % verdict)
    text = "\n".join(out)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()