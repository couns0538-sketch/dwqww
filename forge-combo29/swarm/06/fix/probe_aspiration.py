#!/usr/bin/env python3
"""Does the colour-mirror asymmetry disappear when the aspiration window is widened?

The suspicion in REPORT_next.md: the asymmetry is created by alpha-beta accumulation across the root
sequence, and at depth >= 4 the root narrows alpha/beta around the previous iteration's score, so which
root move first exceeds the window depends on the order the root walks them - which depends on the
previous iteration. If that is the mechanism, a full window at every depth should restore symmetry.

AspirationDelta max is 200, and `narrow` only starts at depth 4, so `AspirationDelta 200` is a wide but
not infinite window. This script also reports a run with the S14 defaults for comparison.

usage: probe_aspiration.py EXE FENFILE DEPTH
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

CONFIGS = [
    ("S14 (AspirationDelta 18)", []),
    ("AspirationDelta 200", [("AspirationDelta", "200")]),
    ("AspirationDelta 200 + AspCappedReopen off + AspArmLate off",
     [("AspirationDelta", "200"), ("AspCappedReopen", "false"), ("AspArmLate", "false")]),
]


class E:
    def __init__(self, exe, opts):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.w("uci")
        while self.r().strip() != "uciok":
            pass
        for n, v in [("Threads", "1"), ("Hash", "16")] + S14 + opts:
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
            line = self.r().strip()
            if any(m in line for m in ("unknown option", "invalid value")):
                raise RuntimeError(line)
            if line == "readyok":
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
                "score": int(t[t.index("score") + 2]), "nodes": int(t[t.index("nodes") + 1])}


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    exe, fenfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    print("exe: " + exe)
    print("depth %d, %d positions" % (depth, len(fens)))
    print("| config | bestmove mirrors | score equal | node count equal |")
    print("|---|---|---|---|")
    for name, opts in CONFIGS:
        bm = sc = nd = 0
        ea, eb = E(exe, opts), E(exe, opts)
        for fen in fens:
            mfen = chess.Board(fen).mirror().fen()
            a = ea.go(fen, depth)
            b = eb.go(mfen, depth)
            bm += b["bm"] == mir(a["bm"])
            sc += a["kind"] == b["kind"] and a["score"] == b["score"]
            nd += a["nodes"] == b["nodes"]
        ea.p.kill()
        eb.p.kill()
        print("| %s | %d/%d | %d/%d | %d/%d |" % (name, bm, len(fens), sc, len(fens), nd, len(fens)))


if __name__ == "__main__":
    main()
