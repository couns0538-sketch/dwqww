#!/usr/bin/env python3
"""move_distribution.py OUT RUNS — twenty runs of seat 04's own board at Threads 4, to settle whether the MOVE
ever varies there.

Seat 04's 04-F10 reported `g7g6` in 7 of 10 Threads-4 runs and `e5e4` in 3. My first check (08-C7) got g7g6 in 10
of 10. Twenty more runs decides: if it is g7g6 in all twenty, then either their e5e4 came from a different build
state/board, or it is rarer than 3-in-10, and the wording is theirs to correct. If e5e4 appears, their claim
reproduces and my first ten were simply lucky.

ARGUMENT ORDER: OUT first, then RUNS (the lesson from the overwritten binary).
"""
import collections
import subprocess
import sys

OUT = sys.argv[1]
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 20
EXE = "/home/ubuntu/builds/pc/forge"
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
DEPTH = 12
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "4"), ("Hash", "16")]


def run_once():
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
    send("position fen " + FEN)
    sync()
    send("go depth %d" % DEPTH)
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
        p.wait(timeout=10)
    except Exception:
        p.kill()
    score = nodes = None
    maxd = 0
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                d = int(t[2])
                maxd = max(maxd, d)
                if d == DEPTH and "score" in t and "nodes" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
                    nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return lines[-1].split()[1], score, nodes, maxd, lines[-1]


rows = []
for i in range(RUNS):
    rows.append(run_once())
    print("run %2d: %s  %s  nodes %s" % (i + 1, rows[-1][0], rows[-1][1], rows[-1][2]))

# controls
if any(r[3] < DEPTH for r in rows):
    raise SystemExit("CONTROL FAILED: a run did not reach depth %d" % DEPTH)
if any(r[1] is None for r in rows):
    raise SystemExit("CONTROL FAILED: an unparsable score; the comparison would be vacuous")

moves = collections.Counter(r[0] for r in rows)
scores = collections.Counter(r[1] for r in rows)
nodes = sorted(r[2] for r in rows)

out = []
def emit(s):
    out.append(s)
    print(s)

emit("")
emit("## seat 04's board, Threads 4, depth 12, %d fresh processes — the MOVE distribution" % RUNS)
emit("")
emit("| bestmove | count | share |")
emit("|---|---|---|")
for m, c in moves.most_common():
    emit("| %s | %d | %.0f %% |" % (m, c, 100.0 * c / RUNS))
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| distinct bestmoves | **%d** |" % len(moves))
emit("| distinct scores | %d of %d |" % (len(scores), RUNS))
emit("| node range | %s .. %s |" % (f"{nodes[0]:,}", f"{nodes[-1]:,}"))
emit("")
if len(moves) == 1:
    emit("**The move NEVER varied in %d runs.** Seat 04 reported `e5e4` in 3 of 10; combined with my earlier ten")
    emit("runs that is **%d of %d** Threads-4 runs on this board giving a single bestmove. Their e5e4 therefore came" %
         (RUNS + 10, RUNS + 10))
    emit("from a different build state, a different board, or an arm that was not what it appeared to be — and the")
    emit("wording of 04-F10's move claim is theirs to correct.")
else:
    emit("**The move DID vary** (%s) — seat 04's claim reproduces and my first ten runs were simply lucky."
         % ", ".join(sorted(moves)))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
