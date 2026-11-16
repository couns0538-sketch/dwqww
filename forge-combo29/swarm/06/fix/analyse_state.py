#!/usr/bin/env python3
"""Compare the three state-probe modes for the colour-mirror search asymmetry.

For each mode it reports, over the same pairs:
  - bestmoves that are the mirror of each other
  - scores that are equal
  - node counts that are equal

Then prints the three-outcome verdict:
  A fresh symmetric, same-process not  -> cross-search state in per-colour tables (a real defect)
  B both fail identically              -> state carried WITHIN the search
  C both symmetric                     -> the earlier pairing harness was the problem

usage: analyse_state.py FRESH.jsonl SAME.jsonl REVERSE.jsonl
"""
import json
import sys

import chess


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def load(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def score_of(rec, side):
    return rec[side]["kind"], rec[side]["score"]


def stats(rows):
    n = len(rows)
    bm = sc = nd = 0
    for r in rows:
        a, b = r["self"], r["mirror"]
        if b["bm"] == mir(a["bm"]):
            bm += 1
        if score_of(r, "self") == score_of(r, "mirror"):
            sc += 1
        if a["nodes"] == b["nodes"]:
            nd += 1
    return n, bm, sc, nd


def main():
    fresh, same, rev = (load(p) for p in sys.argv[1:4])
    print("| mode | pairs | bestmoves mirroring | scores equal | node counts equal |")
    print("|---|---|---|---|---|")
    results = {}
    for name, rows in (("fresh process per search", fresh),
                       ("same process, original first", same),
                       ("same process, mirror first", rev)):
        n, bm, sc, nd = stats(rows)
        results[name] = (n, bm, sc, nd)
        print("| %s | %d | %d | %d | %d |" % (name, n, bm, sc, nd))

    nf, bmf, scf, ndf = results["fresh process per search"]
    ns, bms, scs, nds = results["same process, original first"]
    nr, bmr, scr, ndr = results["same process, mirror first"]
    print("")
    print("per-pair agreement between modes (same bestmove? same score?):")
    agree_bm = agree_sc = 0
    for f, s, r in zip(fresh, same, rev):
        if f["self"]["bm"] == s["self"]["bm"] == r["self"]["bm"]:
            agree_bm += 1
        if score_of(f, "self") == score_of(s, "self") == score_of(r, "self"):
            agree_sc += 1
    print("  original-position result identical in all three modes: bestmove %d/%d, score %d/%d"
          % (agree_bm, nf, agree_sc, nf))
    print("")

    fresh_ok = bmf == nf and scf == nf
    same_ok = bms == ns and scs == ns
    print("VERDICT")
    if fresh_ok and not same_ok:
        print("  A: FRESH IS SYMMETRIC, SAME-PROCESS IS NOT.")
        print("     -> the asymmetry is cross-search state carried in per-colour/accumulating tables.")
        print("        This is a REAL DEFECT, not an inherent property of alpha-beta.")
    elif (not fresh_ok) and (not same_ok):
        print("  B: BOTH FAIL. State carried WITHIN a single search.")
        print("     -> look at the tables that accumulate inside one search and whose index is colour-dependent.")
        print("     fresh: %d/%d mirror, %d/%d score equal; same: %d/%d mirror, %d/%d score equal"
              % (bmf, nf, scf, nf, bms, ns, scs, ns))
    elif fresh_ok and same_ok:
        print("  C: BOTH SYMMETRIC -> my earlier pairing harness carried state; the headline was an artefact.")
    else:
        print("  MIXED/UNEXPECTED: fresh fails but same-process succeeds. Report and investigate.")
    print("")
    print("node counts: fresh %d/%d equal, same %d/%d, reverse %d/%d"
          % (ndf, nf, nds, ns, ndr, nr))


if __name__ == "__main__":
    main()
