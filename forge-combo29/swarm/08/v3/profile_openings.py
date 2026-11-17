#!/usr/bin/env python3
"""profile_openings.py OUT — FABLE file 7 Step 1, second half: 200 openings at go depth 12 under PC20 + test net.

Also records the per-position node rows, which file 7 needs for Step 2's identity check, so this doubles as the
baseline that any patch must reproduce exactly.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
EXE = sys.argv[2] if len(sys.argv) > 2 else "/home/ubuntu/builds/v3/forge"
NET = "/agent/repos/dwqww/forge-combo29/swarm/08/v3/test_v3.fnn3"
FENS = "/tmp/o100.fens"
OPT = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]

fens = [l.strip() for l in open(FENS) if l.strip()]
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
# file 7's load order: NNUEArchFile FIRST, then NNUEArch
send("setoption name NNUEArchFile value " + NET)
sync()
send("setoption name NNUEArch value true")
sync()
for k, v in OPT:
    send("setoption name %s value %s" % (k, v))
    sync()
send("setoption name Threads value 1")
sync()
send("setoption name Hash value 16")
sync()

rows = []
t_all = time.monotonic()
for i, fen in enumerate(fens, 1):
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

    send("go depth 12")
    threading.Thread(target=rd, daemon=True).start()
    if not done.wait(120.0):
        p.kill()
        raise SystemExit("HANG at position %d" % i)
    sync()
    nodes = None
    for l in lines:
        if l.startswith("info depth") and "nodes" in l.split():
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    rows.append((i, fen, nodes, [l for l in lines if l.startswith("bestmove")][-1].split()[1]))
    if i % 50 == 0:
        print("  %d/200 done (%ds)" % (i, int(time.monotonic() - t_all)), flush=True)

send("quit")
try:
    p.wait(timeout=20)
except Exception:
    p.kill()

out = []
def emit(s):
    out.append(s)
    print(s)

emit("## FABLE file 7 Step 1b — 200 openings at depth 12, PC20 + test net, Threads 1")
emit("")
emit("This table is also the IDENTITY BASELINE for Step 2: any patch must reproduce every node row exactly.")
emit("")
emit("| # | fen | nodes | bestmove |")
emit("|---|---|---|---|")
for i, fen, n, bm in rows:
    emit("| %d | %s | %s | %s |" % (i, fen[:52], f"{n:,}" if n is not None else "-", bm))
total = sum(n for _, _, n, _ in rows if n)
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| positions | %d |" % len(rows))
emit("| **node sum** | **%s** |" % f"{total:,}")
emit("| positions with no node count | %d |" % sum(1 for _, _, n, _ in rows if n is None))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
