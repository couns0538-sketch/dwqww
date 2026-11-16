#!/usr/bin/env python3
"""ownbook_effect_on_OG.py EXE OUT — does the book change ANY number in my job1/job2/job3 datasets?

Those three datasets ran on clock_latency.py, which does NOT send OwnBook false. 08-F12 proves the book answers
startpos and short opening lines. This closes the gap by MEASUREMENT rather than by argument: run the same
200-position searches with OwnBook at its default (true) and with it false, and compare per position.

If the book never fires on O/G, the two runs agree within noise and job1/job2/job3 are unaffected.
If the book does fire, the difference will be visible as a position answering in ~0.2 ms with 2 stdout lines.
"""
import json
import subprocess
import sys
import time

exe, outpath = sys.argv[1:3]
FENS = [l.strip() for l in open("../job1/OG200.fens") if l.strip()]

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def run(ownbook):
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
    for n, v in S14:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("setoption name Threads value 1")
    sync()
    send("setoption name Hash value 16")
    sync()
    send("setoption name OwnBook value %s" % ("true" if ownbook else "false"))
    sync()

    recs = []
    for i, fen in enumerate(FENS):
        send("ucinewgame")
        sync()
        send("position fen " + fen)
        sync()
        t0 = time.monotonic()
        send("go movetime 50")
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
        recs.append({"i": i, "fen": fen, "wall_ms": wall, "bestmove": lines[-1].split()[1],
                     "book": any("book move" in l for l in lines), "nlines": len(lines)})
    send("quit")
    p.wait(timeout=10)
    return recs


on = run(True)
off = run(False)

out = []
def emit(s):
    out.append(s)
    print(s)

booked_on = [r for r in on if r["book"]]
booked_off = [r for r in off if r["book"]]
emit("## the same 200 positions, OwnBook default (true) vs false")
emit("| quantity | OwnBook true | OwnBook false |")
emit("|---|---|---|")
emit("| records | %d | %d |" % (len(on), len(off)))
emit("| answered from the book | %d | %d |" % (len(booked_on), len(booked_off)))
emit("| median wall ms | %.2f | %.2f |" % (
    sorted(r["wall_ms"] for r in on)[len(on) // 2], sorted(r["wall_ms"] for r in off)[len(off) // 2]))
emit("| differing bestmoves | %d | |" % sum(1 for a, b in zip(on, off) if a["bestmove"] != b["bestmove"]))
emit("")
if booked_on:
    emit("### positions the book answered with OwnBook true")
    emit("| i | wall ms | bestmove | nlines | fen |")
    emit("|---|---|---|---|---|")
    for r in booked_on:
        emit("| %d | %.2f | %s | %d | %s |" % (r["i"], r["wall_ms"], r["bestmove"], r["nlines"], r["fen"]))
else:
    emit("RESULT: the book answered 0 of the 200 O/G positions even with OwnBook true, so its default value")
    emit("cannot have changed any job1/job2/job3 number.")

with open(outpath, "w") as fh:
    fh.write("\n".join(out) + "\n")
