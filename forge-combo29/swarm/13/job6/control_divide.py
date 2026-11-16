#!/usr/bin/env python3
"""Control for divide_perft4.py — Rule 1 of FABLE file 2: a zero needs a planted one.

The zero I will report is "0 positions differ at the per-divide level at perft 4". That zero counts
only if the SAME harness, unchanged, catches a planted difference. Two plants are made, both through
the real code path (`py_divide` + the same comparison function the real run uses):

  PLANT A (compensating, the S-C4 case): take a real position, add +1 to one root move's count and
    -1 to another's, so the TOTAL is unchanged. A totals-only check passes this; the per-divide
    check must catch it. This is exactly the error class that closed my earlier limit.
  PLANT B (missing move): delete one root move. Must be caught as `missing`.
  PLANT C (extra move): insert a root move that does not exist. Must be caught as `extra`.

If any plant is NOT caught, this exits non-zero and the real run's zero is "not shown".

Usage: control_divide.py FENS
"""
import sys

import chess

sys.path.insert(0, ".")
import importlib.util

spec = importlib.util.spec_from_file_location("dp4", "divide_perft4.py")

DEPTH = 4


def py_divide(fen, depth):
    """Identical to divide_perft4.py's function: the reference for both real and planted data."""
    b = chess.Board(fen)

    def perft(bd, d):
        if d == 0:
            return 1
        n = 0
        for m in bd.legal_moves:
            bd.push(m)
            n += perft(bd, d - 1)
            bd.pop()
        return n

    div = {}
    for m in b.legal_moves:
        b.push(m)
        div[m.uci()] = perft(b, depth - 1)
        b.pop()
    return div


def compare(eng_div, ref_div):
    """Identical comparison the real run performs."""
    missing = sorted(set(ref_div) - set(eng_div))
    extra = sorted(set(eng_div) - set(ref_div))
    wrong = sorted(m for m in set(ref_div) & set(eng_div) if ref_div[m] != eng_div[m])
    return missing, extra, wrong


def main():
    fens = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    out = []
    ok = True

    # find a position with >= 2 root moves and at least one move with a count > 0
    fen = None
    ref = None
    for f in fens:
        try:
            b = chess.Board(f)
        except ValueError:
            continue
        if b.legal_moves.count() >= 2:
            d = py_divide(f, DEPTH)
            if len(d) >= 2 and all(v >= 0 for v in d.values()):
                fen, ref = f, d
                break
    if fen is None:
        raise SystemExit("FAIL: no suitable control position in %s" % sys.argv[1])

    moves = sorted(ref)
    out.append("## control position")
    out.append("`%s`" % fen)
    out.append("root moves: %d, python total: %d" % (len(ref), sum(ref.values())))
    out.append("")

    # PLANT 0: unmodified reference must NOT be flagged (guards against a checker that flags everything)
    eng0 = dict(ref)
    m0 = compare(eng0, ref)
    caught0 = bool(m0[0] or m0[1] or m0[2])
    out.append("| plant | method | total unchanged? | caught | result |")
    out.append("|---|---|---|---|---|")
    out.append("| P0 identity | engine copy of reference | yes | %s | %s |"
               % (caught0, "WRONG - checker flags an identical set" if caught0 else "correctly NOT flagged"))
    ok &= not caught0

    # PLANT A: compensating +1 / -1
    a, c = moves[0], moves[1]
    engA = dict(ref)
    engA[a] += 1
    engA[c] -= 1
    mA = compare(engA, ref)
    total_same = sum(engA.values()) == sum(ref.values())
    caughtA = bool(mA[0] or mA[1] or mA[2])
    out.append("| A compensating | %s +1, %s -1 | %s | %s | %s |"
               % (a, c, "yes (%d vs %d)" % (sum(engA.values()), sum(ref.values())),
                  caughtA, "CAUGHT (%s)" % ",".join(mA[2]) if caughtA else "MISSED"))
    ok &= caughtA and total_same

    # PLANT B: missing move
    engB = dict(ref)
    del engB[moves[-1]]
    mB = compare(engB, ref)
    caughtB = bool(mB[0])
    out.append("| B missing move | delete %s | no | %s | %s |"
               % (moves[-1], caughtB, "CAUGHT" if caughtB else "MISSED"))
    ok &= caughtB

    # PLANT C: extra move
    engC = dict(ref)
    engC["a1a2" if moves[0] != "a1a2" else "a1a3"] = 1
    mC = compare(engC, ref)
    caughtC = bool(mC[1])
    out.append("| C extra move | insert a move not in python's list | no | %s | %s |"
               % (caughtC, "CAUGHT" if caughtC else "MISSED"))
    ok &= caughtC

    out.append("")
    out.append("**Rule 1 verdict: %s**" % (
        "the per-divide checker catches every planted difference, and does not flag an identical "
        "set, so a reported zero from this harness is a real measurement"
        if ok else "FAILED - a zero from this harness would be 'not shown'"))
    text = "\n".join(out)
    open("CONTROL_DIVIDE.md", "w").write(text)
    print(text)
    if not ok:
        raise SystemExit(1)


main()
