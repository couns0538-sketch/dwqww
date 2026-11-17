#!/usr/bin/env python3
"""Self-test the mate oracle. Two halves, both required.

HALF 1 -- KNOWN ANSWERS. Fixtures whose exact distance was established by
pysolve.py, a python-chess negamax that shares no code with the C++ oracle.
Expectations are COMPUTED here, not recalled: an earlier draft of this file
carried a hand-remembered "Qxf7# scholar" at mate-in-1 that is actually only
check, and the oracle was right while the fixture was wrong. A remembered
expectation is a hypothesis, not a known answer.

HALF 2 -- PLANTED WRONG. A deliberately broken oracle must FAIL. Its fault is
the one that would fake a clean result: returning the requested depth as the
exact mate distance as soon as *any* mate exists, never proving the shorter one
impossible. Rule 3: prove the checker fires on a planted fault before you trust
its clean run.
"""
import json
import subprocess
import sys

sys.path.insert(0, "/tmp/fw/oracle")
import pysolve

GOOD = "/tmp/fw/oracle/oracle"
BROKEN = "/tmp/fw/oracle/oracle_broken"

# Candidate fixtures. The EXPECTED distance is computed by pysolve, not written.
FIXTURES = [
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", 5, "back-rank"),
    ("8/8/8/8/8/2k5/1q6/K7 b - - 0 1", 5, "queen+king"),
    ("7k/6pp/8/8/8/8/6PP/R5K1 w - - 0 1", 5, "back-rank-2"),
    ("2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", 5, "wAC-3"),
    ("r5rk/5p1p/5R2/4B3/8/8/7P/7K w - - 0 1", 5, "quiet-key-3"),
    ("r1bq2r1/b4pk1/p1pp1p2/1p2pP2/1P2P1PB/3P4/1PPQ2P1/R3K2R w - - 0 1", 5, "complex-3"),
    # Negative control: start position has no mate in any budget tested.
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 5, "startpos-no-mate"),
]


def query(binary, mode, plies, fen, deadline_ms=600000, extra=None):
    req = f"T\t{mode}\t{plies}\t{deadline_ms}\t"
    return req  # replaced below; kept for clarity of the wire format


def ask(binary, mode, plies, fen, deadline_ms=600000, extra=None):
    parts = ["T", mode, str(plies), str(deadline_ms)]
    if extra:
        parts.append(extra)
    parts.append(fen)
    req = " ".join(parts) + "\n"
    out = subprocess.run([binary], input=req, capture_output=True, text=True, timeout=1800)
    lines = [l for l in out.stdout.strip().split("\n") if l.startswith("{")]
    if len(lines) < 2:
        return {"error": "no reply", "raw": out.stdout + out.stderr}
    return json.loads(lines[-1])


def run_suite(binary, label, expectations):
    rows = []
    for fen, cap, name in FIXTURES:
        exp = expectations[name]
        if exp is None:
            r = ask(binary, "win", cap, fen)
            got = r.get("value")
            ok = got is False
            rows.append({"name": name, "expected": "no mate", "got": got,
                         "status": r.get("status"), "pass": ok})
        else:
            # Search 2 plies past the expected distance so an answer at the cap
            # cannot masquerade as the exact distance.
            r = ask(binary, "dist", exp + 2, fen)
            got = r.get("exact_plies")
            ok = got == exp
            rows.append({"name": name, "expected_plies": exp, "got_plies": got,
                         "status": r.get("status"), "pass": ok})
        row = rows[-1]
        print(f"  {label:7} {name:14} expect={str(row.get('expected_plies', row.get('expected'))):>8} "
              f"got={str(row.get('got_plies', row.get('got'))):>8}  {'PASS' if row['pass'] else 'FAIL'}")
    return rows


def main():
    # Build expectations with the independent solver.
    print("=== computing expectations with pysolve (independent, python-chess) ===")
    expectations = {}
    for fen, cap, name in FIXTURES:
        if name == "startpos-no-mate":
            expectations[name] = None
            print(f"  {name:14} -> no mate within {cap} plies (by construction)")
        else:
            d, n = pysolve.exact_plies(fen, cap)
            expectations[name] = d
            print(f"  {name:14} -> exact {d} plies (pysolve nodes {n})")

    print("\n=== GOOD oracle vs independently computed answers ===")
    good = run_suite(GOOD, "good", expectations)
    good_pass = all(r["pass"] for r in good)

    print("\n=== PLANTED-WRONG oracle must FAIL the same suite ===")
    bad = run_suite(BROKEN, "broken", expectations)
    detected = any(not r["pass"] for r in bad)

    ok = good_pass and detected
    print()
    print(f"good oracle: {'ALL PASS' if good_pass else 'FAILURES PRESENT'}")
    print(f"planted-wrong oracle: {'DETECTED (correctly fails)' if detected else 'NOT DETECTED — suite is blind'}")
    print("SUITE VALID" if ok else "SUITE INVALID")

    with open("/tmp/fw/oracle/selftest.json", "w") as f:
        json.dump({"expectations": expectations, "good": good, "broken": bad,
                   "good_all_pass": good_pass, "broken_detected": detected,
                   "suite_valid": ok}, f, indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
