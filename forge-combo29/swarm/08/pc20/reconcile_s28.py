#!/usr/bin/env python3
"""reconcile_s28.py OUT — run seat 28's OUTLIER positions on MY harness at the owner's control.

The disagreement: on 6 s + 0.06, PC20, Threads 1, Hash 16, seat 28 finds 5 of 120 searches spending 1.2-1.59 s
(worst 1585.3 ms = exactly the 1585 ms hard plan), while my 240 moves across 3 positions never exceeded 482 ms.

Their method and mine agree on the plan arithmetic (soft 317 / hard 1585) and on the control string, so the
difference must be the POSITION SET. This runs their exact outlier FENs, plus a few of their ordinary ones as a
control, through MY harness at the same control, 3 fresh processes each.

ARGUMENT ORDER: OUT first.
"""
import json
import subprocess
import sys
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"
RUNS = 3

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# seat 28's outliers, taken verbatim from their realclock_PC20.tsv, with their measured time
CASES = [
    ("28 outlier #1 (1585.3 ms)", "8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1", 1585.349),
    ("28 outlier #2 (1439.5 ms)", "7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b - - 0 1", 1439.493),
    ("28 outlier #3 (834.7 ms)", "8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1", 834.707),
    ("28 outlier #4 (804.9 ms)", "8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b - - 0 1", 804.865),
    ("28 ordinary (160.7 ms)", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1", 160.659),
    ("28 fastest-ish (204.2 ms)", "8/3k1p2/1R4pp/4P3/5KP1/5P2/8/r7 w - - 0 1", 204.193),
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
        return None
    t0 = time.monotonic()
    send(CLOCK)
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
        p.wait(timeout=30)
    except Exception:
        p.kill()
    maxd = 0
    nodes = None
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                maxd = max(maxd, int(t[2]))
                if "nodes" in t:
                    nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "depth": maxd, "nodes": nodes, "bm": lines[-1].split()[1]}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Reconciling with seat 28: THEIR outlier positions, MY harness, same control")
emit("")
emit("`go wtime 6000 btime 6000 winc 60 binc 60`, PC r15, PC20, Threads 1, Hash 16, %d fresh processes per board." % RUNS)
emit("Plan: soft 317 ms / hard 1585 ms.")
emit("")
emit("| board | seat 28 measured | my run 1 | my run 2 | my run 3 | my median | reproduces 1.2-1.59 s? |")
emit("|---|---|---|---|---|---|---|")
allrows = []
for label, fen, theirs in CASES:
    runs = [probe(fen) for _ in range(RUNS)]
    if any(r is None for r in runs):
        emit("| %s | %s | REFUSED | | | | |" % (label, fen))
        continue
    walls = sorted(r["wall"] for r in runs)
    med = walls[len(walls) // 2]
    repro = "**YES**" if med > 1200 else ("partly" if max(walls) > 1000 else "no")
    allrows.append((label, theirs, walls, runs[0]["depth"], runs[0]["bm"]))
    emit("| %s | %.1f ms | %.1f | %.1f | %.1f | **%.1f ms** | %s |" %
         (label, theirs, walls[0], walls[len(walls) // 2], walls[-1], med, repro))

emit("")
emit("| board | my median | seat 28's value | ratio | my depth | bestmove |")
emit("|---|---|---|---|---|---|")
for label, theirs, walls, d, bm in allrows:
    med = walls[len(walls) // 2]
    emit("| %s | %.1f ms | %.1f ms | %.2fx | %d | %s |" % (label, med, theirs, med / theirs if theirs else 0, d, bm))

emit("")
emit("| question | answer |")
emit("|---|---|")
mine = [w[len(w) // 2] for _, _, w, _, _ in allrows]
emit("| my median across their 4 outliers | %.1f ms |" % (sum(mine[:4]) / 4))
emit("| how many of their 4 outliers I reproduce above 1200 ms | **%d of 4** |"
     % sum(1 for w in mine[:4] if w > 1200))
emit("| my worst on their boards | **%.1f ms** |" % max(max(w) for _, _, w, _, _ in allrows))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
