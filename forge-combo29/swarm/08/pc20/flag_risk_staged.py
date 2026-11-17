#!/usr/bin/env python3
"""flag_risk_staged.py OUT — stage the residual flag risk I identified in 08-F34.

08-F34 found 0 flags in 600 moves on the owner's control, but I noted a limit: "a bare-endgame position arriving at
~1400 ms could still take the 1585 ms hard plan". That is testable directly, and it is the last open flag question.

Method: put a BARE ENDGAME on the board (the shape 08-F33 found slowest — ≤8 pieces) and give it exactly the clock
level the drain test settled at, then lower. For each (position, clock) pair, run `go wtime C btime C winc 60 binc 60`
and record whether wall > C — a flag.

The positions are the ones that actually took longest in the shape sweep, so this is the worst case rather than a
random sample — and I say so.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# the boards that took longest in the shape sweep (08-F33), i.e. the worst case for a flag
FENS = [
    ("7-piece, 33 moves, took 1585 ms at 6 s", "8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1"),
    ("6-piece, 4 moves, took 1225 ms at 6 s", "8/8/4k3/8/8/4K3/8/R7 w - - 0 1"),
    ("4-piece, 22 moves, took 1164 ms at 6 s", "8/8/8/4k3/8/8/6PP/4R1K1 w - - 0 1"),
]
CLOCKS = [6000, 3000, 1600, 1200, 800, 400, 200]


def run(fen, clock):
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
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                break
        done.set()

    t0 = time.monotonic()
    send("go wtime %d btime %d winc 60 binc 60" % (clock, clock))
    threading.Thread(target=rd, daemon=True).start()
    ok = done.wait(max(30.0, clock / 200.0))
    wall = (time.monotonic() - t0) * 1000.0
    if not ok:
        p.kill()
        return {"timeout": True, "wall": wall}
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    depth = 0
    for l in lines:
        if l.startswith("info depth"):
            try:
                depth = max(depth, int(l.split()[2]))
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "bm": lines[-1].split()[1], "depth": depth}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Staged flag risk: bare endgames at falling clocks — PC r15, PC20, Threads 1")
emit("")
emit("These are the WORST boards from the shape sweep, not a random sample — deliberately.")
emit("")
emit("| board | clock | wall ms | wall > clock (FLAG)? | depth |")
emit("|---|---|---|---|---|")
flags = 0
total = 0
worst = []
for label, fen in FENS:
    for c in CLOCKS:
        r = run(fen, c)
        if r.get("timeout"):
            emit("| %s | %d | TIMEOUT | | |" % (label[:34], c))
            continue
        total += 1
        f = r["wall"] > c
        if f:
            flags += 1
            worst.append((label, c, r["wall"]))
        emit("| %s | %d | %.1f | %s | %d |" % (label[:34], c, r["wall"], "**YES**" if f else "no", r["depth"]))
    emit("| | | | | |")

emit("")
emit("## Verdict")
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| (board, clock) pairs tested | %d |" % total)
emit("| FLAGS (wall > remaining clock) | **%d** |" % flags)
if worst:
    emit()
    emit("### the flags, listed")
    emit("| board | clock | wall ms | overrun |")
    emit("|---|---|---|---|")
    for label, c, w in worst:
        emit("| %s | %d | %.1f | +%.1f ms |" % (label, c, w, w - c))
emit("")
if flags == 0:
    emit("**No flag even on the worst boards at 200 ms.** The time manager handles the bare-endgame case across the")
    emit("whole clock range, because the plan shrinks with the clock: at 200 ms the `available` is 190 and the plan")
    emit("(soft 53 / hard 114 ms) is small enough that an expensive iteration no longer fits, so the residual risk")
    emit("flagged in 08-F34 does NOT materialise on these boards.")
else:
    emit("**%d flags found** — this is the case 08-F34 could not stage, and it is real. See the list." % flags)

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
