#!/usr/bin/env python3
"""softnodes.py OUT — `go softnodes N` on the PC build under PC20 at Threads 1.

From FABLE_TO_swarm_6: "go softnodes 2000 (its self-play: the search stops at the end of the first depth after
2,000 nodes)". The suggested new area asks three questions:
  1. is it deterministic run to run (it must be),
  2. does it stop at a FINISHED depth (a complete iteration, not mid-iteration),
  3. how far past N does it go.

Method, per (N, position): 5 fresh processes. Record the bestmove, the score, the node count and the last depth, and
verify determinism across those 5. Then measure the OVERSHOOT = nodes_at_stop - N, and check the stop is at a
finished depth by confirming the final `info depth` line is a complete iteration (it has a pv) and that no later
depth was started.

ARGUMENT ORDER: OUT first.
"""
import json
import subprocess
import sys

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
RUNS = 5

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

POSITIONS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("G middlegame", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
]
NS = [500, 2000, 20000]


def probe(fen, n):
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
    send("go softnodes %d" % n)
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
    depths = []          # (depth, nodes, has_pv)
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                d = int(t[2])
                nn = int(t[t.index("nodes") + 1]) if "nodes" in t else None
                depths.append((d, nn, "pv" in t))
            except (IndexError, ValueError):
                pass
    return {"bm": lines[-1].split()[1], "depths": depths,
            "last_depth": depths[-1][0] if depths else None,
            "nodes_at_stop": depths[-1][1] if depths else None,
            "last_has_pv": depths[-1][2] if depths else None,
            "distinct_depths": len({d for d, _, _ in depths})}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## `go softnodes N` — PC r15, PC20, Threads 1, Hash 16, %d fresh processes per cell" % RUNS)
emit("")
emit("| position | N | run | bestmove | last depth | nodes at stop | overshoot | last info has pv |")
emit("|---|---|---|---|---|---|---|---|")

summary = {}
for label, fen in POSITIONS:
    for n in NS:
        runs = [probe(fen, n) for _ in range(RUNS)]
        for i, r in enumerate(runs, 1):
            emit("| %s | %d | %d | %s | %s | %s | %s | %s |" %
                 (label, n, i, r["bm"], r["last_depth"], f"{r['nodes_at_stop']:,}" if r["nodes_at_stop"] else "-",
                  f"{r['nodes_at_stop'] - n:+,}" if r["nodes_at_stop"] else "-", r["last_has_pv"]))
        summary[(label, n)] = runs
        emit("| | | | | | | | |")

emit("")
emit("## The three questions")
emit("")
emit("| position | N | deterministic? | bestmove(s) | last depth(s) | nodes at stop | overshoot past N | finished depth? |")
emit("|---|---|---|---|---|---|---|---|")
for (label, n), runs in summary.items():
    bms = {r["bm"] for r in runs}
    lds = {r["last_depth"] for r in runs}
    ns = {r["nodes_at_stop"] for r in runs}
    det = len(bms) == 1 and len(lds) == 1 and len(ns) == 1
    over = (list(ns)[0] - n) if len(ns) == 1 and list(ns)[0] is not None else None
    finished = all(r["last_has_pv"] for r in runs)
    emit("| %s | %d | **%s** | %s | %s | %s | %s | %s |" %
         (label, n, "YES" if det else "**NO**", ", ".join(sorted(bms)),
          ", ".join(str(x) for x in sorted(lds)),
          ", ".join(f"{x:,}" for x in sorted(ns) if x is not None),
          f"{over:+,}" if over is not None else "-",
          "YES (pv present)" if finished else "**NO pv on last line**"))

emit("")
nondet = [k for k, runs in summary.items()
          if len({r["bm"] for r in runs}) > 1 or len({r["nodes_at_stop"] for r in runs}) > 1]
emit("| quantity | value |")
emit("|---|---|")
emit("| cells measured | %d |" % len(summary))
emit("| cells NOT deterministic | **%d** %s |" % (len(nondet), nondet if nondet else ""))
worst = max((r["nodes_at_stop"] - k[1]) for k, runs in summary.items() for r in runs if r["nodes_at_stop"])
emit("| largest overshoot past N seen | **%s nodes** |" % f"{worst:,}")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
