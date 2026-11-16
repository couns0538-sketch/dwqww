#!/usr/bin/env python3
"""Independent reproduction of the reported wrong-move defect.

Position under test: 1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183
Claim: the engine plays c6c7 (its own depth-20 score mate -11) while c6d6 scores cp -1142, and the base
build ranks them the other way.

This harness is written from the report's sentence only; it does not use anyone else's script.
Each move is scored SEPARATELY with `go depth D searchmoves <move>` so the two scores are independent
(the root is restricted, which is the only way to force the engine to report a specific move's score).

Fresh process for every single number. Threads 1, Hash 16 always (owner's rule).
Every setoption is followed by isready and every line up to readyok is read.
Stops on `unknown option`, `invalid value`, `ERROR`.

usage: repro_wrongmove.py EXE LABEL FEN "MOVE1 MOVE2" DEPTHS OUTFILE
"""
import hashlib
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "ERROR")


def one(exe, fen, depth, searchmove=None, mode="PC20"):
    opts = PC20 if mode == "PC20" else S14
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def r():
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError("engine died")
        return line

    def ready():
        while True:
            line = r().strip()
            if any(m in line for m in BAD):
                raise RuntimeError(line)
            if line == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in [("Threads", "1"), ("Hash", "16")] + opts:
        w("setoption name %s value %s" % (n, v))
        w("isready")
        ready()
    w("ucinewgame")
    w("isready")
    ready()
    w("position fen " + fen)
    w("isready")
    ready()
    go = "go depth %d" % depth
    if searchmove:
        go += " searchmoves " + searchmove
    w(go)
    last = None
    bm = None
    depth_reached = 0
    while True:
        line = r().strip()
        if any(m in line for m in BAD):
            raise RuntimeError(line)
        if line.startswith("info") and " pv " in line:
            t = line.split()
            if "depth" in t:
                depth_reached = max(depth_reached, int(t[t.index("depth") + 1]))
            last = t
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
    p.kill()
    if last is None:
        return {"score_kind": None, "score": None, "nodes": None, "bestmove": bm, "depth": depth_reached}
    return {"score_kind": last[last.index("score") + 1],
            "score": int(last[last.index("score") + 2]),
            "nodes": int(last[last.index("nodes") + 1]),
            "bestmove": bm, "depth": depth_reached}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    exe, label, fen, movestr, depths, outfile = sys.argv[1:7]
    moves = movestr.split()
    depths = [int(x) for x in depths.split(",")]
    b = chess.Board(fen)
    legal = {m.uci() for m in b.legal_moves}
    lines = []
    lines.append("BUILD LABEL : " + label)
    lines.append("EXE         : " + exe)
    lines.append("EXE SHA256  : " + sha256(exe))
    lines.append("FEN         : " + fen)
    lines.append("SIDE TO MOVE: " + ("white" if b.turn else "black") + "  pieces " + str(len(b.piece_map())))
    lines.append("LEGAL       : " + " ".join(sorted(legal)))
    lines.append("MOVES TESTED: " + " ".join(moves) + ("   (all legal)" if all(m in legal for m in moves)
                                                         else "   *** SOME ARE ILLEGAL ***"))
    lines.append("SETTINGS    : PC20 (Threads 1, Hash 16, 14 S14 settings, CuckooRep true, HistRework 2,")
    lines.append("              TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false)")
    lines.append("Every number from a FRESH process. Threads 1 (owner's rule).")
    lines.append("")
    lines.append("| move | depth | depth reached | score | nodes | bestmove answered |")
    lines.append("|---|---|---|---|---|---|")
    for mv in moves:
        for d in depths:
            r = one(exe, fen, d, mv)
            lines.append("| %s | %d | %d | %s %s | %s | %s |" %
                         (mv, d, r["depth"], r["score_kind"], r["score"], r["nodes"], r["bestmove"]))
    lines.append("")
    lines.append("=== the engine's OWN free choice (no searchmoves), for comparison ===")
    lines.append("| depth | bestmove | score | nodes |")
    lines.append("|---|---|---|---|")
    for d in depths:
        r = one(exe, fen, d)
        lines.append("| %d | %s | %s %s | %s |" % (d, r["bestmove"], r["score_kind"], r["score"], r["nodes"]))
    text = "\n".join(lines) + "\n"
    open(outfile, "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
