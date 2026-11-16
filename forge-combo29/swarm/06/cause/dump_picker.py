#!/usr/bin/env python3
"""Dump the MovePicker's ROOT score vector for a position and its colour mirror, and compare.

Question: do the picker's scores already differ at the root between a position and its mirror
(which would implicate the history/threat/continuation tables), or are they identical there and the
divergence starts deeper?

Only the FIRST root iteration is reported, because that is the one taken before any subtree of this
search has been searched; later iterations legitimately differ since the search has filled the tables.

usage: dump_picker.py INSTRUMENTED_EXE FEN DEPTH
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def run(exe, fen, depth, first_only=True):
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
    vectors = []
    while True:
        l = r().strip()
        if l.startswith("info string rootpicker"):
            t = l.split()[3:]
            v = {}
            for item in t:
                if ":" in item:
                    mv, sc = item.split(":")
                    v[mv] = int(sc)
            vectors.append(v)
            if first_only:
                # stop right after the first root picker dump: kill the search
                p.kill()
                return vectors
        if l.startswith("bestmove"):
            break
    p.kill()
    return vectors


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    exe, fen, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
    mfen = chess.Board(fen).mirror().fen()
    a = run(exe, fen, depth)[0]
    b = run(exe, mfen, depth)[0]
    bm = {mir(k): v for k, v in b.items()}
    print("FEN   : " + fen)
    print("MIRROR: " + mfen)
    print("FIRST ROOT ITERATION ONLY (no subtree of this search has been searched yet)")
    print("")
    print("| move | picker score self | picker score mirror (mapped back) | equal |")
    print("|---|---|---|---|")
    keys = sorted(set(a) | set(bm))
    diffs = 0
    for k in keys:
        sa, sb = a.get(k), bm.get(k)
        same = sa == sb
        if not same:
            diffs += 1
        print("| %s | %s | %s | %s |" % (k, sa, sb, same))
    print("")
    print("root moves whose PICKER SCORE differs: %d of %d" % (diffs, len(keys)))
    if diffs == 0:
        print("")
        print("VERDICT: the picker's root score vectors are IDENTICAL, so the history/threat/continuation")
        print("         tables do not differ at the root on the first iteration. The divergence must appear")
        print("         below the root (as the tables fill during the search), not in the initial picker scores.")
    else:
        print("")
        print("VERDICT: the picker's root score vectors ALREADY DIFFER before any subtree is searched, so the")
        print("         accumulating tables (history/threat/continuation) are implicated at the root.")


if __name__ == "__main__":
    main()
