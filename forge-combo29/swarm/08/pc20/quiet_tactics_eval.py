#!/usr/bin/env python3
"""quiet_tactics_eval.py OUT — for the three positions where the 10 ms one-ply answer differed from the deep
answer, how bad is the difference really? The deep score alone does not say whether the one-ply move LOSES or is
merely a different good move. Measure the position after each candidate at a fixed depth, from the same side.

For each of the three: play the 10 ms move, then ask a deep search for the score of the RESULTING position; play the
deep move, do the same. The difference between those two scores is the cost of the one-ply choice, in centipawns
from the mover's point of view (negated, because after the move it is the opponent to move).
"""
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

CASES = [
    ("pin_the_queen", "r2q1rk1/ppp2ppp/8/8/3n4/2N5/PPP2PPP/R2Q1RK1 w - - 0 1", "f1e1", "d1d3"),
    ("discovered_attack", "r1bq1rk1/ppp2ppp/2n5/3n4/8/2N2N2/PPP2PPP/R1BQ1RK1 w - - 0 1", "c3d5", "d1d5"),
    ("knight_retreat", "r1b1k2r/pppp1ppp/8/8/1b1n4/2N5/PPPP1PPP/R1BQK2R w KQkq - 0 1", "c3d5", "d1g4"),
]


def score_of(fen, depth=16):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for n, v in PC20:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    send("go depth %d" % depth)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    sc = ""
    for l in lines:
        if l.startswith("info depth") and " score " in l:
            sc = l.split(" score ")[1].split(" nodes")[0]
    return sc


def parse_cp(score):
    """'cp 123' or 'mate 3' -> centipawns (mate mapped to +-30000)."""
    t = score.split()
    if len(t) < 2:
        return None
    try:
        v = int(t[1])
    except ValueError:
        return None
    if t[0] == "cp":
        return v
    if t[0] == "mate":
        return (30000 - abs(v)) * (1 if v > 0 else -1)
    return None


out = []


def emit(s):
    out.append(s)
    print(s)


emit("## The cost of the 1-ply choice in the three disagreeing positions (PC r15, PC20, Threads 1)")
emit("")
emit("Both candidate moves played out of the same position, then the RESULTING position scored at depth 16.")
emit("A positive cost means the 1-ply move left the mover worse off than the deep move.")
emit("")
emit("| position | 1-ply move | score after it | deep move | score after it | cost of the 1-ply choice |")
emit("|---|---|---|---|---|---|")
costs = []
for label, fen, m10, mdeep in CASES:
    b = chess.Board(fen)
    b.push(chess.Move.from_uci(m10))
    s10 = score_of(b.fen())
    b = chess.Board(fen)
    b.push(chess.Move.from_uci(mdeep))
    sdeep = score_of(b.fen())
    v10, vdeep = parse_cp(s10), parse_cp(sdeep)
    if v10 is None or vdeep is None:
        raise SystemExit("CONTROL FAILED: could not parse a score for %r (%r / %r)" % (label, s10, sdeep))
    # after the move the opponent is to move, so negate to get the mover's view
    cost = (-vdeep) - (-v10)
    costs.append((label, cost))
    emit("| %s | %s | %s | %s | %s | **%+d cp** |" % (label, m10, s10, mdeep, sdeep, cost))

emit("")
emit("| position | cost of the one-ply choice |")
emit("|---|---|")
for label, c in costs:
    verdict = "loses material" if c >= 150 else ("worse, but small" if c >= 50 else "negligible")
    emit("| %s | %+d cp — %s |" % (label, c, verdict))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
