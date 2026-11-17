#!/usr/bin/env python3
"""f2_harness_can_fail.py <exe> <outdir>

Seat 19's integrity rule: a check that greps engine output must assert the line it parses was found,
and a zero/empty/NaN must never pass as a confirmation. So before any "X of X equal" claim from
f1_board_checks.py counts, the SAME perft comparison must be shown able to report a DIFFERENCE.

Three planted cases, all through the same p4 comparison path:
  (a) expected-difference: compare the engine's perft of position A against python-chess's perft of
      position B (one legal move apart) -> must report a difference.
  (b) missing-line: ask the engine for `go perft 5` on a position where the answer will not arrive in
      time (timeout 0.01 s) -> the harness must raise Missing, not return None/0.
  (c) self-check of the reference generator: python-chess startpos perft 4 must be 197281 and the
      planted 401 must fail (see pyperft.py __main__; here repeated for one place).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f1_board_checks as H
import pyperft

class Missing(Exception):
    """A value the harness needed was not found. Never let this pass as a result."""


A = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"
B = "rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4"


def main():
    exe = os.path.realpath(sys.argv[1])
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    res = {}

    e = H.Engine(exe)
    e.boot()

    # (a) the comparison must SEE a difference when one exists
    eng_a, _ = e.perft("position fen " + A, 2)
    py_a = pyperft.perft_fen(A, 2)
    py_b = pyperft.perft_fen(B, 2)
    res["a_engine_perft2_A"] = eng_a
    res["a_python_perft2_A"] = py_a
    res["a_python_perft2_B"] = py_b
    res["a_same_case_A_vs_A"] = (eng_a == py_a)
    res["a_planted_difference_A_vs_B_detected"] = (eng_a != py_b)
    if not res["a_planted_difference_A_vs_B_detected"]:
        print("FAIL: the comparison cannot see a difference it must see")
        json.dump(res, open(os.path.join(outdir, "result.json"), "w"), indent=2)
        return 1
    if not res["a_same_case_A_vs_A"]:
        print("FAIL: the engine and python-chess disagree on position A itself")
        json.dump(res, open(os.path.join(outdir, "result.json"), "w"), indent=2)
        return 1

    # (b) a missing line must raise, never return a silent zero
    raised = None
    try:
        e.perft("position fen " + A, 5, timeout=0.01)
        raised = "NOTHING (BAD: a silent success)"
    except H.Missing as ex:
        raised = "Missing: %s" % ex
    res["b_missing_line_raises"] = raised
    if not str(raised).startswith("Missing"):
        print("FAIL: a missing node line did not raise")
        json.dump(res, open(os.path.join(outdir, "result.json"), "w"), indent=2)
        return 1
    e.quit()

    # (c) the reference generator itself
    ok = pyperft.perft_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 4) == 197281
    caught = False
    try:
        assert pyperft.perft_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 2) == 401
    except AssertionError:
        caught = True
    res["c_reference_startpos_perft4_197281"] = ok
    res["c_planted_wrong_expectation_caught"] = caught
    res["date_utc"] = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                     capture_output=True, text=True).stdout.strip()
    res["exe"] = exe
    res["exe_sha256"] = subprocess.run(["sha256sum", exe], capture_output=True,
                                       text=True).stdout.split()[0]
    res["verdict"] = ("HARNESS CAN FAIL (a and b and c all held)"
                      if ok and caught else "HARNESS IS BLIND - DO NOT TRUST f1")
    with open(os.path.join(outdir, "result.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))
    return 0 if (ok and caught) else 1


if __name__ == "__main__":
    sys.exit(main())
