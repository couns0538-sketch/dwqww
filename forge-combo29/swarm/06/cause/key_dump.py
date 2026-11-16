#!/usr/bin/env python3
"""Print the TT key and pawn key for every root move on both sides of a mirror pair.

The two outcomes this settles:
  keys DIFFER for corresponding moves -> the mirror does not preserve the key (hashing/zobrist defect).
  keys IDENTICAL but behaviour differs -> something stored is colour-dependent.

Note: keys differing for corresponding moves is EXPECTED for any absolute-square Zobrist scheme and is
not by itself a defect - what matters is whether the ENGINE'S BEHAVIOUR is a function of the position
alone. This script reports the keys, and the companion analysis says which of the two outcomes applies.

usage: key_dump.py EXE FEN DEPTH
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def dump(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def r():
        l = p.stdout.readline()
        if l == "":
            raise RuntimeError("died")
        return l

    def rd():
        while True:
            if r().strip() == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")] + S14:
        w("setoption name %s value %s" % (n, v)); w("isready"); rd()
    w("ucinewgame"); w("isready"); rd()
    w("position fen " + fen); w("isready"); rd()
    w("go depth %d" % depth)
    rows = []
    while True:
        l = r().strip()
        if l.startswith("info string rootkey"):
            t = l.split()
            rows.append({"move": t[3], "key": int(t[5]), "pawnkey": int(t[7]),
                         "nodes": int(t[9])})
        if l.startswith("bestmove"):
            break
    p.kill()
    return rows


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    exe, fen, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
    mfen = chess.Board(fen).mirror().fen()
    a = dump(exe, fen, depth)
    b = dump(exe, mfen, depth)
    print("FEN   : " + fen)
    print("MIRROR: " + mfen)
    print("")
    print("| move | key self | key mirror | key equal | pawnkey self | pawnkey mirror | pawn equal | nodes s/m |")
    print("|---|---|---|---|---|---|---|---|")
    bm = {mir(r["move"]): r for r in b}
    for r in a:
        q = bm.get(r["move"])
        if q is None:
            print("| %s | %d | (absent) | - | | | | |" % (r["move"], r["key"]))
            continue
        print("| %s | %d | %d | %s | %d | %d | %s | %d/%d |" % (
            r["move"], r["key"], q["key"], r["key"] == q["key"],
            r["pawnkey"], q["pawnkey"], r["pawnkey"] == q["pawnkey"],
            r["nodes"], q["nodes"]))
    print("")
    keq = sum(1 for r in a if bm.get(r["move"]) and r["key"] == bm[r["move"]]["key"])
    print("moves whose KEY is equal on both sides: %d of %d" % (keq, len(a)))
    print("(a key difference is EXPECTED for an absolute-square Zobrist scheme; the question is whether")
    print(" the search's behaviour is a function of the position alone - see the companion analysis.)")


if __name__ == "__main__":
    main()
