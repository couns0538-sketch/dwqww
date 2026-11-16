#!/usr/bin/env python3
"""check_s05f3.py EXE — seat 11's check of seat 05's S-F3 (fifty-move threshold).

S-F3: "The fifty-move draw is applied about 9 plies early: `1K6/8/8/3R4/8/8/8/k7 w - - H 1` at
`go depth 10` scores `cp 472` for H=0..75, `cp 314` at H=90, then exactly `cp 0` from H=91."

MEASUREMENT INTEGRITY (two warnings applied):
  * 19-F12: a piped `quit` mid-search fabricates a bestmove with no info lines. This script
    uses ucio.Engine, which sends one command and reads to bestmove before the next.
  * seat 19's NaN warning: EVERY score must be positively parsed. A run that produces no
    `info depth ... score` line is a HARD FAILURE of the measurement, never "drawish" and never
    a confirmation. `assert_scored()` raises if the parse is empty.
The verdict can only be CONFIRMS/REFUTES when every sweep point parsed; otherwise it prints
"MEASUREMENT FAILED" and exits non-zero.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine

EXE = sys.argv[1]
KRK = "1K6/8/8/3R4/8/8/8/k7 w - - {h} 1"
BARE = "1K6/8/8/8/8/8/8/k7 w - - {h} 1"


class MeasurementError(Exception):
    pass


def probe(fen, depth=10):
    """Run one search. Returns (score_tuple, n_info, bestmove). Raises if nothing parsed."""
    e = Engine(EXE, options=["OwnBook false"], timeout=600)
    e.start()
    try:
        answer, refused = e.position(fen=fen)
        if refused:
            raise MeasurementError(f"position refused: {refused} (fen={fen})")
        infos, bm, lines = e.go(f"go depth {depth}")
        if not infos:
            raise MeasurementError(f"NO info lines at all (fen={fen}) — 19-F12 or no search")
        last = None
        for l in infos:
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                last = (m.group(1), int(m.group(2)))
        if last is None:
            raise MeasurementError(
                f"info lines present but NO 'score cp|mate N' parsed (fen={fen}); "
                f"first line was {infos[0]!r}")
        san = e.drain_stderr()
        if san:
            raise MeasurementError(f"sanitizer output: {san[:3]}")
        return last, len(infos), bm
    finally:
        e.quit()


def main():
    sweep = [0, 50, 75, 85, 88, 90, 91, 92, 95, 99, 100]
    print("=== the curve (KRvK, go depth 10, waiting driver) ===")
    print(f"{'H':>4} {'score':>14} {'n_info':>7}  bestmove")
    res = {}
    try:
        for h in sweep:
            score, n, bm = probe(KRK.format(h=h))
            res[h] = score
            print(f"{h:>4} {str(score):>14} {n:>7}  {bm}")
    except MeasurementError as exc:
        print(f"\nMEASUREMENT FAILED: {exc}")
        print("No verdict is given. A missing/unparsed score is never a result.")
        return 2

    print("\n=== controls (also must parse) ===")
    try:
        bare_score, _, _ = probe(BARE.format(h=0))
        print(f"  bare kings H=0 -> {bare_score} (a draw; the position is insufficient material)")
    except MeasurementError as exc:
        print(f"  control MEASUREMENT FAILED: {exc}")
        return 2

    print("\n=== verdict on S-F3 ===")
    failures = []
    def chk(name, cond, detail=""):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
        if not cond:
            failures.append(name)

    chk("KRvK at H=0 is a win, not cp 0 (S-F3 says cp 472)",
        res[0] != ("cp", 0), f"got {res[0]}")
    chk("bare kings at H=0 is exactly cp 0 (control)", bare_score == ("cp", 0), f"got {bare_score}")
    zeros = sorted(h for h in sweep if res[h] == ("cp", 0))
    chk("H=90 is still a win (S-F3 says cp 314)", res[90] != ("cp", 0), f"got {res[90]}")
    chk("the first cp 0 is at H=91 (S-F3's claim)",
        (zeros[0] if zeros else None) == 91, f"H values with cp 0: {zeros}")

    print()
    if not failures:
        print("RESULT: CONFIRMS S-F3 — the fifty-move draw takes effect at H=91, nine plies early.")
        print(f"        Scores seen: H=0 {res[0]}, H=90 {res[90]}, H=91 {res[91]}, H=100 {res[100]}.")
        return 0
    print("RESULT: does NOT reproduce S-F3 as stated; the printed curve is the evidence.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
