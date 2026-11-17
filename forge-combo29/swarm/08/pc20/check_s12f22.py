#!/usr/bin/env python3
"""check_s12f22.py OUT — my own check of seat 12's S-F22:

"The safe Hash x MultiPV boundary is a CURVE, not a single cell, and the 'MultiPV 3 at Hash 256 is ruined /
 MultiPV 2 at 64 is marginal' premise is wrong."

Their claim is about a PERFORMANCE boundary: certain (Hash, MultiPV) combinations are much slower per move, and the
slow region is a curve rather than one bad cell.

What I can measure cheaply and independently: for a grid of (Hash, MultiPV), run the same fixed search and record
elapsed time. The claim to test is SHAPE: is there a slow region, and is it a curve (i.e. a boundary that moves with
Hash) rather than a single cell?

This is a clock-seat question — I have the timing harnesses — so it is a good fit.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
FEN = "r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2/PBPPBPPP/R2Q1RK1 w - - 0 10"
HASHES = [16, 64, 256]
MULTIPVS = [1, 2, 3, 4]
GO = "go nodes 200000"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run(hash_mb, multipv):
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
    for k, v in PC20 + [("Threads", "1")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("setoption name Hash value %d" % hash_mb)
    sync()
    send("setoption name MultiPV value %d" % multipv)
    sync()
    send("ucinewgame")
    sync()
    send("position fen " + FEN)
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
    send(GO)
    threading.Thread(target=rd, daemon=True).start()
    ok = done.wait(180.0)
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
    nodes = None
    for l in lines:
        if l.startswith("info depth") and "nodes" in l.split():
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "nodes": nodes}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 12 S-F22 — Hash x MultiPV: a curve, or a single bad cell?")
emit("")
emit("`%s`, PC r15 PC20, Threads 1, fixed node budget so the WORK is constant and the time is the variable." % GO)
emit("")
emit("| Hash | MultiPV 1 | 2 | 3 | 4 |")
emit("|---|---|---|---|---|")
grid = {}
for h in HASHES:
    row = []
    for m in MULTIPVS:
        r = run(h, m)
        if r.get("timeout"):
            grid[(h, m)] = None
            row.append("TIMEOUT")
        else:
            grid[(h, m)] = r["wall"]
            row.append("%.0f" % r["wall"])
    emit("| %d | %s |" % (h, " | ".join(row)))

emit("")
emit("## The claim, tested")
emit("")
emit("| question | answer |")
emit("|---|---|")
vals = [v for v in grid.values() if v is not None]
if vals:
    lo, hi = min(vals), max(vals)
    emit("| fastest cell | %.0f ms |" % lo)
    emit("| slowest cell | %.0f ms |" % hi)
    emit("| spread | **%.1fx** |" % (hi / lo if lo else 0))
    # is the slow region a single cell or a band?
    slow_thresh = lo * 1.5
    slow_cells = [(h, m) for (h, m), v in grid.items() if v and v > slow_thresh]
    emit("| cells slower than 1.5x the fastest | **%d** %s |" % (len(slow_cells), slow_cells[:8]))
    multi = len({h for h, m in slow_cells}) > 1 or len({m for h, m in slow_cells}) > 1
    emit("| spread across more than one Hash or MultiPV value (a curve, not a cell) | **%s** |" %
         ("YES" if multi and len(slow_cells) > 1 else "NO"))
    emit("")
    if len(slow_cells) > 1 and multi:
        emit("**SUPPORTS the curve claim**: the slow region is more than one cell and spans more than one Hash or")
        emit("MultiPV value, so it is a boundary rather than a single bad combination.")
    elif len(slow_cells) <= 1:
        emit("**DOES NOT support the curve claim on this grid**: at most one cell is slow, which is the single-cell")
        emit("picture their finding argues against. Note my grid is coarser than theirs (3 Hash x 4 MultiPV).")
    else:
        emit("**PARTIAL**: %d slow cells but all on one axis, so the boundary is a line rather than a curve on my grid."
             % len(slow_cells))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
