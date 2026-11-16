#!/usr/bin/env python3
"""gonodes_probe.py EXE REGIME -- file 6's match path: `go nodes` 20000, 50000 and 250000 on the PC build under PC20,
Threads 1, Hash 16. Is it deterministic run to run, does it stop at a finished depth, and how close are the reported
nodes to N?

`go nodes` is a HARD limit (unlike softnodes), so the expectation is reported nodes == N exactly and the last info
line possibly at a depth in progress. The comparison excludes `nps` and `time` (wall clock).
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
REGIME = sys.argv[2] if len(sys.argv) > 2 else "PC20"
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3

S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16"]
SIX = ["setoption name CuckooRep value true", "setoption name HistRework value 2",
       "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
       "setoption name MateAlphaGuard value true", "setoption name OwnBook value false"]
OPTS = {"S14": S14, "PC20": S14 + SIX}[REGIME]

POSITIONS = [
    ("startpos", None),
    ("G0", "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"),
    ("mid", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
]
NS = [20000, 50000, 250000]


def strip_timing(line):
    if not line:
        return line
    return re.sub(r"\s*(nps \d+|time \d+)", "", line)


def run_once(fen, n):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=400):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                L.append("###EOF")
                return
            l = l.rstrip()
            L.append(l)
            if l.startswith(t):
                return
        L.append("###TIMEOUT")

    s("uci"); u("uciok")
    for o in OPTS:
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s("position fen " + fen if fen else "position startpos")
    s("isready"); u("readyok")
    s(f"go nodes {n}")
    u("bestmove"); s("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    last = pv[-1] if pv else None
    bm = next((x for x in L if x.startswith("bestmove")), None)
    return last, bm


def parse(line):
    if not line:
        return {}
    d = re.search(r"depth (\d+)", line)
    n = re.search(r"\bnodes (\d+)", line)
    s = re.search(r"score (mate|cp) (-?\d+)", line)
    pvlen = len(line.split(" pv ", 1)[1].split()) if " pv " in line else 0
    return dict(depth=int(d.group(1)) if d else None, nodes=int(n.group(1)) if n else None,
                score=f"{s.group(1)} {s.group(2)}" if s else None, pvlen=pvlen)


print(f"exe: {EXE}   regime {REGIME}   Threads 1   {RUNS} fresh runs per cell   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| position | N | reported nodes | nodes/N | depth | score | pv | identical across runs? | bestmove same? |")
print("|---|---|---|---|---|---|---|---|---|")
all_det = True
for label, fen in POSITIONS:
    for n in NS:
        outs = [run_once(fen or "", n) for _ in range(RUNS)]
        pvs = [strip_timing(o[0]) for o in outs]
        bms = [o[1] for o in outs]
        same = len(set(p for p in pvs if p)) == 1
        samebm = len(set(b for b in bms if b)) == 1
        all_det = all_det and same and samebm
        p0 = parse(outs[0][0])
        nodes = p0.get("nodes")
        ratio = f"{nodes/n:.3f}" if nodes else "-"
        print(f"| {label} | {n} | {nodes} | {ratio} | {p0.get('depth')} | {p0.get('score')} | "
              f"{p0.get('pvlen')} | {'YES' if same else '**NO**'} | {'yes' if samebm else '**NO**'} |")
print()
print(f"deterministic on every cell (pv and bestmove): {all_det}")
print("`go nodes` is a hard limit, so nodes/N near 1.000 means the limit is honoured exactly.")
