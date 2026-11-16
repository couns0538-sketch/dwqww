#!/usr/bin/env python3
"""softnodes.py EXE OUTDIR : `go nodes N` on the PC build under PC20, Threads 1.

File 6's suggested new area, and the PC's actual self-play path. Three questions:
  1. is it DETERMINISTIC run to run (it must be at Threads 1)?
  2. does it stop at a FINISHED depth (i.e. the last `info depth` reported a complete iteration)?
  3. how far PAST N does the node budget go?

Per position and per N: several fresh processes. For each run record the full `info depth` line list, the
bestmove, the total nodes at the end, and the last completed depth. Determinism = every run identical in
(move, last depth, node count).
"""
import os
import subprocess
import sys

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
limit = int(sys.argv[4]) if len(sys.argv) > 4 else 6
ns = [int(x) for x in (sys.argv[5].split(",") if len(sys.argv) > 5 else ["2000"])]
reps = int(sys.argv[6]) if len(sys.argv) > 6 else 4
depth_cap = 60
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16")]

positions = []
for line in open(fens):
    line = line.strip()
    if line and not line.startswith("#"):
        positions.append(line.split(";")[0].strip())
positions = positions[:limit]


def one(fen, n):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def readto(pred, limit=500000):
        got = []
        for _ in range(limit):
            l = p.stdout.readline()
            if not l:
                return got
            l = l.rstrip("\n")
            got.append(l)
            if pred(l):
                return got
        return got

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
        send("isready")
        readto(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("position fen " + fen)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("go nodes %d" % n)
    block = readto(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill()
    depths = []
    best = None
    for l in block:
        if l.startswith("info depth") and " pv " in l:
            try:
                d = int(l.split("info depth ")[1].split()[0])
                nodes = int(l.split("nodes ")[1].split()[0])
                depths.append((d, nodes))
            except (IndexError, ValueError):
                pass
        if l.startswith("bestmove"):
            best = l.split()[1] if len(l.split()) > 1 else None
    last_depth = depths[-1][0] if depths else 0
    last_nodes = depths[-1][1] if depths else 0
    return best, last_depth, last_nodes, depths, block


rows = []
for i, fen in enumerate(positions):
    for n in ns:
        runs = [one(fen, n) for _ in range(reps)]
        keys = {(r[0], r[1], r[2]) for r in runs}
        det = len(keys) == 1
        best, last_depth, last_nodes, depths, _ = runs[0]
        over = (last_nodes - n) / n * 100 if n else 0
        rows.append((i, fen, n, det, best, last_depth, last_nodes, over, len(depths)))
        print("pos %d softnodes %d: deterministic=%s  bestmove=%s  last depth %d at %d nodes  (%+.0f %% over N)  %d iterations"
              % (i, n, det, best, last_depth, last_nodes, over, len(depths)), flush=True)

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("go nodes on PC r15, PC20, Threads 1, Hash 16, cold (ucinewgame before each)\n")
    fh.write("%d positions x %s, %d runs each\n\n" % (len(positions), ns, reps))
    fh.write("| pos | softnodes N | deterministic | bestmove | last finished depth | nodes at that depth | over N |\n")
    fh.write("|---|---|---|---|---|---|---|\n")
    for i, fen, n, det, best, ld, ln, over, it in rows:
        fh.write("| %d | %d | **%s** | %s | %d | %d | %+.1f %% |\n"
                 % (i, n, "yes" if det else "NO", best, ld, ln, over))
    alldet = all(r[3] for r in rows)
    fh.write("\nall rows deterministic: **%s**\n" % alldet)
    if rows:
        overs = [r[7] for r in rows]
        fh.write("overshoot past N: min %+.1f %%, median %+.1f %%, max %+.1f %%\n"
                 % (min(overs), sorted(overs)[len(overs) // 2], max(overs)))
print("\n" + open(os.path.join(outdir, "RESULT.txt")).read()[-900:])
