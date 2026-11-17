#!/usr/bin/env python3
"""drain_to_flag.py OUT — run the owner's clock all the way DOWN to the flag.

My earlier countdown sweep (08-F24 / job5) stopped at ~3000 ms after 40 moves. The question a match manager actually
asks is: when the clock drains to zero over a long game, does the engine ever exceed the remaining time (i.e. flag)?

Method: the owner's control, `wtime/btime 6000 6000 winc 60 binc 60`; after each move subtract the wall time and add
60 ms, exactly as a GUI does, and keep going until the clock would be at or below Move Overhead. Record every move:
clock before, wall, clock after, and whether wall > clock (a flag).

Because the engine also SHORTENS its thinking as the clock drains, a well-behaved time manager should converge rather
than flag. This measures that.

ARGUMENT ORDER: OUT first.
"""
import json
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
INC = 60
START_CLOCK = 6000
MAX_MOVES = 200
FENS = [
    ("G mid 1", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G mid 2", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
]
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]


def one_move(fen, clock):
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
    send("go wtime %d btime %d winc %d binc %d" % (max(clock, 0), max(clock, 0), INC, INC))
    threading.Thread(target=rd, daemon=True).start()
    ok = done.wait(max(30.0, clock / 500.0))
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

emit("## Draining the owner's clock to the flag — PC r15, PC20, Threads 1, 6 s + 0.06")
emit("")
emit("Clock walked forward exactly as a GUI does: clock -= wall, then += 60 ms.")
emit("")
for label, fen in FENS:
    emit("### %s" % label)
    emit("")
    emit("| move | clock before | wall ms | clock after | wall > clock? | depth |")
    emit("|---|---|---|---|---|---|")
    clock = START_CLOCK
    flags = 0
    moves = 0
    lo = clock
    for i in range(1, MAX_MOVES + 1):
        if clock <= 10:
            emit("| — | %d | reserve-empty boundary reached; drain ends | | | |" % clock)
            break
        r = one_move(fen, clock)
        if r.get("timeout"):
            emit("| %d | %d | TIMEOUT | | | |" % (i, clock))
            break
        after = clock - int(r["wall"]) + INC
        flagged = r["wall"] > clock
        if flagged:
            flags += 1
        moves += 1
        lo = min(lo, clock)
        if i <= 8 or i % 20 == 0 or flagged or clock < 500:
            emit("| %d | %d | %.1f | %d | %s | %d |" %
                 (i, clock, r["wall"], max(after, 0), "**YES**" if flagged else "no", r["depth"]))
        clock = max(after, 0)
    emit("")
    emit("| quantity | value |")
    emit("|---|---|")
    emit("| moves played | %d |" % moves)
    emit("| lowest clock reached | %d ms |" % lo)
    emit("| moves where wall > remaining clock (a FLAG) | **%d** |" % flags)
    emit("")
    with open(OUT + ".jsonl", "a") as fh:
        fh.write(json.dumps({"start": label, "moves": moves, "lowest": lo, "flags": flags}) + "\n")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
