#!/usr/bin/env python3
"""softnodes_probe.py EXE REGIME -- file 6's suggested area: `go softnodes N` on the PC build under PC20, Threads 1.

Three questions file 6 names:
  1. is it deterministic run to run (it must be)?
  2. does it stop at a FINISHED depth (i.e. the last info line is a completed depth, not a partial one)?
  3. how far past N does it go (reported nodes vs N)?

Method: for each (position, N) pair, run K fresh processes with identical input and compare the last pv line
byte for byte. Then report reported-nodes / N as the overshoot ratio.
"""
import hashlib
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
    ("G1", "rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4"),
    ("mid", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
]
NS = [2000, 20000, 50000, 250000]


def run_once(fen, n):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=300):
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
    s(f"go softnodes {n}")
    u("bestmove"); s("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    return L


def strip_timing(line):
    """Remove the wall-clock fields before comparing runs. `nps` and `time` are measured with the monotonic clock and
    differ by a microsecond between otherwise identical runs; comparing the raw line makes every run look different
    (my first version of this probe did exactly that and reported FALSE nondeterminism). The search-relevant fields
    are depth, seldepth, score, nodes, hashfull and pv."""
    if not line:
        return line
    return re.sub(r"\s*(nps \d+|time \d+)", "", line)


def last_pv(L):
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    return pv[-1] if pv else None


def parse(line):
    if not line:
        return None
    d = re.search(r"depth (\d+)", line)
    n = re.search(r"\bnodes (\d+)", line)
    s = re.search(r"score (mate|cp) (-?\d+)", line)
    return dict(depth=int(d.group(1)) if d else None,
                nodes=int(n.group(1)) if n else None,
                score=f"{s.group(1)} {s.group(2)}" if s else None)


print(f"exe: {EXE}   regime {REGIME}   Threads 1   {RUNS} fresh runs per cell   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| position | N | reported nodes | overshoot | depth | score | identical across runs? |")
print("|---|---|---|---|---|---|---|")
det_all = True
for label, fen in POSITIONS:
    for n in NS:
        outs = []
        for _ in range(RUNS):
            L = run_once(fen or "", n)
            outs.append(last_pv(L))
        parsed = [parse(o) for o in outs]
        same = len(set(strip_timing(o) for o in outs if o)) == 1
        det_all = det_all and same
        p0 = parsed[0] if parsed and parsed[0] else {}
        nodes = p0.get("nodes")
        over = f"{nodes/n:.2f}x" if nodes and n else "-"
        print(f"| {label} | {n} | {nodes} | {over} | {p0.get('depth')} | {p0.get('score')} | "
              f"{'YES' if same else '**NO**'} |")
print()
print(f"deterministic on every cell: {det_all}")
print("Note on 'finished depth': the engine prints one `info` line per completed depth; the LAST line's depth is")
print("by construction a completed depth, so the question is whether reported nodes exceed N (the overshoot column).")
