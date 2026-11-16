#!/usr/bin/env python3
"""Ablation: switch one search feature off at a time and ask whether colour-mirror symmetry
comes back (bestmove mirrors AND score equal) at a fixed depth, on a fixed set of FENs.

Pruning is turned off by pushing its depth/margin parameters to values that disable the test,
because the engine has no explicit on/off switch for most of them. A feature is "the cause"
only if disabling it restores symmetry on ALL tested positions.

usage: ablation.py EXE DEPTH FENFILE
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
    ("S14 baseline", []),
    ("null move off (NullMoveMinDepth 10, NullMoveBase 0)",
     [("NullMoveMinDepth", "10")]),
    ("RFP off (RfpMargin 0, RfpDepth 0)", [("RfpMargin", "10"), ("RfpDepth", "0")]),
    ("razoring off (RazorDepth 0)", [("RazorDepth", "0")]),
    ("futility off (FutilityDepth 0)", [("FutilityDepth", "0")]),
    ("LMP off (LmpBase 0, HistoryPruneMultiplier 0)",
     [("LmpBase", "0"), ("HistoryPruneMultiplier", "0")]),
    ("probcut off (ProbcutMargin 1000)", [("ProbcutMargin", "1000")]),
    ("singular off (SingularDepth 20)", [("SingularDepth", "20")]),
    ("IIR off (IirDepth 0)", [("IirDepth", "1")]),
    ("LMR off (LmrQuietBase 0, LmrNoisyBase 0)", [("LmrQuietBase", "0"), ("LmrNoisyBase", "0")]),
    ("LMR history divisor max (30000)", [("LmrHistoryDivisor", "30000")]),
    ("SEE pruning off (SeeQuiet 0, SeeNoisy 0)",
     [("SeeQuietMultiplier", "0"), ("SeeNoisyMultiplier", "0")]),
    ("aspiration wide (AspirationDelta 200)", [("AspirationDelta", "200")]),
    ("LmrSignedCorrection off", [("LmrSignedCorrection", "false")]),
    ("HindsightDepth off", [("HindsightDepth", "false")]),
    ("NullThreatVerify off", [("NullThreatVerify", "false")]),
    ("NullSeeVeto off", [("NullSeeVeto", "false")]),
    ("QuietExtinction off", [("QuietExtinction", "false")]),
    ("SoundMatePruning off", [("SoundMatePruning", "false")]),
    ("everything above off at once",
     [("NullMoveMinDepth", "10"), ("RfpMargin", "10"), ("RfpDepth", "0"),
      ("RazorDepth", "0"), ("FutilityDepth", "0"), ("LmpBase", "0"),
      ("HistoryPruneMultiplier", "0"), ("ProbcutMargin", "1000"), ("SingularDepth", "20"),
      ("IirDepth", "1"), ("LmrQuietBase", "0"), ("LmrNoisyBase", "0"),
      ("SeeQuietMultiplier", "0"), ("SeeNoisyMultiplier", "0"),
      ("LmrSignedCorrection", "false"), ("HindsightDepth", "false"),
      ("NullThreatVerify", "false"), ("NullSeeVeto", "false"),
      ("QuietExtinction", "false"), ("SoundMatePruning", "false")]),
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
        return (bm, t[t.index("score") + 1], int(t[t.index("score") + 2]),
                int(t[t.index("nodes") + 1]))


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    exe, depth, fenfile = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    print("depth %d, %d positions, S14 + the listed option changes" % (depth, len(fens)))
    print("| config | bestmoves mirroring | scores equal |")
    print("|---|---|---|")
    for name, opts in CONFIGS:
        bm_ok = sc_ok = 0
        ea, eb = E(exe, opts), E(exe, opts)
        for fen in fens:
            mfen = chess.Board(fen).mirror().fen()
            a = ea.go(fen, depth)
            b = eb.go(mfen, depth)
            if b[0] == mir(a[0]):
                bm_ok += 1
            if a[1] == b[1] and a[2] == b[2]:
                sc_ok += 1
        ea.p.kill()
        eb.p.kill()
        print("| %s | %d/%d | %d/%d |" % (name, bm_ok, len(fens), sc_ok, len(fens)))


if __name__ == "__main__":
    main()
