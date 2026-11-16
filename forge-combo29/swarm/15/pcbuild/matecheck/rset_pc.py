#!/usr/bin/env python3
"""rset_pc.py EXE --regime R : the 8 mate positions of job 1b (15-F6) on this build.

15-F6 was: 8 mate scores on 200 R positions at depth 12, all 8 correct on the base tree. This checks
the PC build does not REGRESS them, i.e. that MateAlphaGuard does not break mates that were already
right. For each: score must equal the previously-recorded one and the PV must still end in checkmate
with the plies the score claims. Threads 1.
"""
import argparse, re, sys
import chess
from pc_regimes import run, S14, PC20_EXTRA

# from job1b/mates_table.txt: (fen, expected score, expected PV plies)
CASES = [
 ("rn2r3/1b1p4/3q3k/p4P1P/2P5/P1K1pNP1/4Nn2/1B2R3 b - - 11 46", "mate 5", 9),
 ("r2k2r1/pbp2p2/5Np1/3pq2p/1Ppp2P1/P3n1QP/3N4/1RB1K2R b - - 1 32", "mate 2", 3),
 ("8/5k2/2b3pK/B4p2/8/8/7p/2n2b2 b - - 7 95", "mate 3", 5),
 ("r1k5/pb6/2npPp2/BP1N4/5pP1/2R2K2/3NP2R/5B2 w - - 0 43", "mate 1", 1),
 ("b7/3kP3/3p1p2/nP1N4/1p3pP1/2R2N2/r3PKBR/8 w - - 10 50", "mate 4", 7),
 ("8/1P2k1Nb/5R2/2n5/1p2p3/1B6/5p2/5K2 w - - 0 71", "mate 6", 11),
 ("1Q6/4kb2/5R2/7N/1p2p3/4K3/3nB3/8 w - - 3 78", "mate 2", 3),
 ("8/1bk5/4R3/7N/1p1Kp3/1B6/6Q1/5n2 w - - 17 85", "mate 5", 9),
]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("exe")
    ap.add_argument("--regime", default="PC20")
    a = ap.parse_args()
    opts = [] if a.regime == "none" else (S14 if a.regime == "S14" else S14 + PC20_EXTRA)
    print("exe: %s  regime: %s  Threads 1" % (a.exe, a.regime), flush=True)
    print("%-58s %-9s %-9s %-5s %-6s %s" % ("fen", "expected", "got", "plies", "mate?", "verdict"), flush=True)
    ok = bad = 0
    for fen, want, wantp in CASES:
        r = run(a.exe, opts, fen, 12)
        if r["score"] == "REFUSED_FEN":
            print("%-58s REFUSED_FEN — skipped, cannot judge" % fen[:58], flush=True)
            continue
        b = chess.Board(fen); legal = True
        for u in r["pv"]:
            mv = chess.Move.from_uci(u)
            if mv not in b.legal_moves:
                legal = False; break
            b.push(mv)
        good = (r["score"] == want and legal and b.is_checkmate() and len(r["pv"]) == wantp)
        ok += 1 if good else 0; bad += 0 if good else 1
        print("%-58s %-9s %-9s %-5d %-6s %s" % (fen[:58], want, r["score"], len(r["pv"]),
              b.is_checkmate() if legal else "ILLEGAL", "ok" if good else "CHANGED"), flush=True)
    print("\nunchanged %d, changed %d" % (ok, bad), flush=True)

main()
