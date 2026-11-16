#!/usr/bin/env python3
"""At which depth does the colour-mirror symmetry of the SEARCH first break?

For each FEN, searches the position and its colour mirror (fresh process per search) at depths
1..DEPTHMAX over a fixed option set, and counts, per depth:
  - positions whose bestmove is the mirror of the original
  - positions whose (score kind, score value) is equal
  - positions whose node count is equal

usage: depth_curve.py EXE FENFILE DEPTHMAX OUTFILE
"""
import json
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


class E:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.w("uci")
        while self.r().strip() != "uciok":
            pass
        for n, v in [("Threads", "1"), ("Hash", "16")] + S14:
            self.w("setoption name %s value %s" % (n, v))
            self.w("isready")
            self.ready()

    def w(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def r(self):
        line = self.p.stdout.readline()
        if line == "":
            raise RuntimeError("died")
        return line

    def ready(self):
        while True:
            if self.r().strip() == "readyok":
                return

    def go(self, fen, d):
        self.w("ucinewgame")
        self.w("isready")
        self.ready()
        self.w("position fen " + fen)
        self.w("isready")
        self.ready()
        self.w("go depth %d" % d)
        pv = None
        while True:
            line = self.r().strip()
            if " pv " in line:
                pv = line
            if line.startswith("bestmove"):
                bm = line.split()[1]
                break
        t = pv.split()
        return {"bm": bm, "kind": t[t.index("score") + 1],
                "score": int(t[t.index("score") + 2]),
                "nodes": int(t[t.index("nodes") + 1])}


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    exe, fenfile, dmax, outfile = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    ea, eb = E(exe), E(exe)
    out = open(outfile, "w")
    counts = {d: {"n": 0, "bm": 0, "sc": 0, "nd": 0} for d in range(1, dmax + 1)}
    for i, fen in enumerate(fens):
        mfen = chess.Board(fen).mirror().fen()
        for d in range(1, dmax + 1):
            a = ea.go(fen, d)
            b = eb.go(mfen, d)
            rec = {"index": i, "depth": d, "fen": fen, "mfen": mfen, "self": a, "mirror": b,
                   "bm_mirrors": b["bm"] == mir(a["bm"]),
                   "score_equal": a["kind"] == b["kind"] and a["score"] == b["score"],
                   "nodes_equal": a["nodes"] == b["nodes"]}
            out.write(json.dumps(rec) + "\n")
            c = counts[d]
            c["n"] += 1
            c["bm"] += rec["bm_mirrors"]
            c["sc"] += rec["score_equal"]
            c["nd"] += rec["nodes_equal"]
        out.flush()
    ea.p.kill()
    eb.p.kill()
    out.close()
    print("| depth | positions | bestmove mirrors | score equal | node count equal |")
    print("|---|---|---|---|---|")
    for d in range(1, dmax + 1):
        c = counts[d]
        print("| %d | %d | %d | %d | %d |" % (d, c["n"], c["bm"], c["sc"], c["nd"]))


if __name__ == "__main__":
    main()
