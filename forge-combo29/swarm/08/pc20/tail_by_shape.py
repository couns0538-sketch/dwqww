#!/usr/bin/env python3
"""tail_by_shape.py OUT — WHICH KINDS OF POSITION blow the tail at 6 s + 0.06?

The reconciliation with seat 28 showed their outliers reproduce on my harness (one at 1585.4 ms against their
1585.3), so my original 3-position sample was too narrow. This isolates the SHAPE that makes a search spend a
quarter of the clock.

Hypothesis from the observed data: the slow boards are FEW-PIECE positions with FEW LEGAL MOVES (5, 6, 13 legal
moves) where the search goes very deep and each extra depth costs a large multiple; the fast boards are full
material with many legal moves where depth grows slowly and evenly.

Method: four shape classes, 5 positions each, at the owner's control. For each board record the wall time, the
last completed depth, and the cost of the last iteration. Then a per-class median.

ARGUMENT ORDER: OUT first.
"""
import json
import statistics
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

CLASSES = [
    ("few pieces, few moves", [
        "8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1",
        "8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1",
        "8/8/4k3/8/8/4K3/8/4R3 w - - 0 1",
        "8/6k1/8/8/8/8/6PK/7R w - - 0 1",
        "8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b - - 0 1",
    ]),
    ("few pieces, many moves", [
        "8/8/8/8/8/5k2/p6P/6K1 w - - 0 1",
        "7k/8/8/8/8/8/5PPP/3R2K1 w - - 0 1",
        "8/8/4k3/8/8/4K3/8/R7 w - - 0 1",
        "6k1/8/8/8/8/8/8/R5K1 w - - 0 1",
        "8/8/8/4k3/8/8/6PP/4R1K1 w - - 0 1",
    ]),
    ("full material, few moves", [
        "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1",
        "1r2k2r/pppppppp/8/8/8/8/PPPPPPPP/1R2K2R w Kk - 0 1",
        "4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1",
        "r1bqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    ]),
    ("full material, many moves", [
        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
        "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
        "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
        "r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2/PBPPBPPP/R2Q1RK1 w - - 0 10",
        "2r2rk1/1p1nbppp/pq1pb3/3Np3/1P2P3/P1N1B3/1BPP1PPP/R2Q1RK1 w - - 0 14",
    ]),
]


def probe(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        got = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            got.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return got

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return {"err": "refused"}
    t0 = time.monotonic()
    send(CLOCK)
    marks = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        ms = (time.monotonic() - t0) * 1000.0
        if l.startswith("info depth"):
            try:
                marks.append((int(l.split()[2]), ms))
            except (IndexError, ValueError):
                pass
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    lastd = marks[-1][0] if marks else 0
    lastms = marks[-1][1] if marks else None
    itercost = None
    if len(marks) >= 2:
        itercost = marks[-1][1] - marks[-2][1]
    elif marks:
        itercost = marks[-1][1]
    return {"wall": wall, "depth": lastd, "itercost": itercost, "lastdepth_ms": lastms}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Which shapes blow the tail at 6 s + 0.06? PC r15, PC20, Threads 1, Hash 16")
emit("")
emit("| class | board | legal moves | wall ms | depth | last iteration cost ms |")
emit("|---|---|---|---|---|---|")
per = {}
for cname, fens in CLASSES:
    per[cname] = []
    for fen in fens:
        r = probe(fen)
        if "err" in r:
            # a refused synthetic FEN: skip it and SAY so rather than silently dropping
            emit("| %s | %s | REFUSED by the engine — excluded | | | |" % (cname, fen))
            continue
        b = chess.Board(fen)
        per[cname].append(r)
        emit("| %s | %s | %d | %.1f | %d | %s |" %
             (cname, fen[:34], b.legal_moves.count(), r["wall"], r["depth"],
              "%.1f" % r["itercost"] if r["itercost"] is not None else "-"))

emit("")
emit("## Per class")
emit("")
emit("| class | n | median wall ms | worst ms | median depth | median last-iteration cost ms |")
emit("|---|---|---|---|---|---|")
for cname, rows in per.items():
    if not rows:
        continue
    w = [r["wall"] for r in rows]
    d = [r["depth"] for r in rows]
    ic = [r["itercost"] for r in rows if r["itercost"] is not None]
    emit("| %s | %d | **%.1f** | %.1f | %.0f | %s |" %
         (cname, len(rows), statistics.median(w), max(w), statistics.median(d),
          "%.1f" % statistics.median(ic) if ic else "-"))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
