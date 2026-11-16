#!/usr/bin/env python3
"""Option sweep: which search feature, when switched off, restores colour-mirror symmetry?

For each configuration, searches startpos and its colour mirror at a fixed depth in FRESH processes
and reports whether bestmove is the mirror and whether the score is equal, plus both node counts.

usage: sweep.py EXE DEPTH
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

CONFIGS = {
    "S14 baseline": [],
    "ThreatHistory off": [("ThreatHistory", "false")],
    "ContHist4PlyRead off": [("ContHist4PlyRead", "false")],
    "ContHist4PlyRead 0-read": [("ContHist4PlyRead", "false")],
    "Threat+ContHist off": [("ThreatHistory", "false"), ("ContHist4PlyRead", "false")],
    "LmrSignedCorrection off": [("LmrSignedCorrection", "false")],
    "NonPawnCorrection off": [("NonPawnCorrection", "false")],
    "DrawJitter 0": [("DrawJitter", "0")],
    "DeadMaterial on": [("DeadMaterial", "true")],
    "HindsightDepth off": [("HindsightDepth", "false")],
}


def run(exe, fen, depth, opts):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def r():
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError("died")
        return line

    def ready():
        while True:
            if r().strip() == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in [("Threads", "1"), ("Hash", "16")] + S14 + opts:
        w("setoption name %s value %s" % (n, v))
        w("isready")
        ready()
    w("ucinewgame")
    w("isready")
    ready()
    w("position fen " + fen)
    w("isready")
    ready()
    w("go depth %d" % depth)
    pv = None
    while True:
        line = r().strip()
        if " pv " in line:
            pv = line
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
    p.kill()
    tok = pv.split()
    score = int(tok[tok.index("score") + 2])
    kind = tok[tok.index("score") + 1]
    nodes = int(tok[tok.index("nodes") + 1])
    return {"bm": bm, "score": score, "kind": kind, "nodes": nodes, "pv": tok[tok.index("pv") + 1:]}


def mir(u):
    frm = chess.parse_square(u[0:2])
    to = chess.parse_square(u[2:4])
    return chess.square_name(frm ^ 56) + chess.square_name(to ^ 56) + (u[4:] if len(u) > 4 else "")


def main():
    exe, depth = sys.argv[1], int(sys.argv[2])
    fen = chess.Board().fen()
    mfen = chess.Board().mirror().fen()
    print("depth %d, startpos vs its colour mirror, fresh process each side" % depth)
    print("| config | bestmove mirror? | score equal? | nodes W | nodes B | verdict |")
    print("|---|---|---|---|---|---|")
    for name, opts in CONFIGS.items():
        a = run(exe, fen, depth, opts)
        b = run(exe, mfen, depth, opts)
        bm_ok = b["bm"] == mir(a["bm"])
        sc_ok = a["score"] == b["score"] and a["kind"] == b["kind"]
        verdict = "SYMMETRIC" if (bm_ok and sc_ok) else ("bm differs" if not bm_ok else "score differs")
        print("| %s | %s | %s | %d | %d | %s |" % (name, bm_ok, sc_ok, a["nodes"], b["nodes"], verdict))


if __name__ == "__main__":
    main()
