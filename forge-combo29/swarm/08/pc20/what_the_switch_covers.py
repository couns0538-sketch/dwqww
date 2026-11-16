#!/usr/bin/env python3
"""what_the_switch_covers.py OUT — what FORGE_FIX_HARD_LIMIT_EMERGENCY actually does.

The switch's own comment (patch line 989-996) says: "when the hard time limit has already passed before the search
starts (a clock a millisecond or two above Move Overhead), play the hash move or search one ply with at most 2,000
nodes, AS FOR AN EMPTY RESERVE. r9 played the first legal move unsearched there, so `go wtime 11` could be answered
worse than `go wtime 10`."

So the switch's stated job is to make the NEAR-OVERHEAD case (wtime 11, where available time is positive but the
hard limit is already consumed) behave like the BELOW-OVERHEAD case (wtime 10, reserve empty) — both one ply with a
TT move preferred — instead of r9's unsearched first legal move.

Test on BOTH builds: for wtime 11 and wtime 10, the answer and whether it equals `go depth 1`:
 - base tree: `go wtime 11` should be the FIRST LEGAL MOVE unsearched (the defect the switch fixes)
 - PC r15 : `go wtime 11` should equal the `go depth 1` answer (one ply searched), i.e. no worse than wtime 10
"""
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
BUILDS = [("base tree 6b98f217", "/home/ubuntu/builds/release/forge"),
          ("PC r15", "/home/ubuntu/builds/pc/forge")]
FENS = [
    "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
    "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8",
    "8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1",
]


def ask(exe, fen, go, pc20):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    if pc20:
        opts = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
                ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
                ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
                ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
                ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
                ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
        for n, v in opts:
            send("setoption name %s value %s" % (n, v))
            sync()
    send("setoption name Threads value 1")
    sync()
    send("setoption name Hash value 16")
    sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    t0 = time.monotonic()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    depths = [l for l in lines if l.startswith("info depth")]
    return {"bm": lines[-1].split()[1], "wall": wall, "nd": len(depths),
            "maxd": max((int(l.split()[2]) for l in depths), default=None)}


out = []


def emit(s):
    out.append(s)
    print(s)


emit("## What FORGE_FIX_HARD_LIMIT_EMERGENCY covers: wtime 11 (near overhead) vs wtime 10 (reserve empty)")
emit("")
emit("| build | fen | wtime 11 | wtime 10 | depth-1 answer | first legal (python-chess) | 11 == depth1? | 10 == depth1? |")
emit("|---|---|---|---|---|---|---|---|")
n11_eq = {}
for label, exe in BUILDS:
    pc20 = (label == "PC r15")
    eq11 = eq10 = 0
    for fen in FENS:
        b = chess.Board(fen)
        first = b.uci(list(b.legal_moves)[0])
        r11 = ask(exe, fen, "go wtime 11 btime 11", pc20)
        r10 = ask(exe, fen, "go wtime 10 btime 10", pc20)
        d1 = ask(exe, fen, "go depth 1", pc20)
        a11 = (r11["bm"] == d1["bm"])
        a10 = (r10["bm"] == d1["bm"])
        eq11 += a11
        eq10 += a10
        emit("| %s | %s | %s (d=%s, %.2f ms) | %s (d=%s, %.2f ms) | %s | %s | %s | %s |" %
             (label, fen[:22], r11["bm"], r11["maxd"], r11["wall"], r10["bm"], r10["maxd"], r10["wall"],
              d1["bm"], first, a11, a10))
    n11_eq[label] = (eq11, eq10)

emit("")
emit("| build | wtime 11 answered like depth 1 | wtime 10 answered like depth 1 |")
emit("|---|---|---|")
for label, (a, b) in n11_eq.items():
    emit("| %s | %d of %d | %d of %d |" % (label, a, len(FENS), b, len(FENS)))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
