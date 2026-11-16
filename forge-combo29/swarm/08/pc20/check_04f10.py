#!/usr/bin/env python3
"""check_04f10.py EXE OUT — my own check of seat 04's 04-F10, written from its sentence alone:

"On an ORDINARY middlegame position from set G (1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1),
 PC r15 under PC20, go depth 12, Threads 4, ten fresh processes: 9 distinct scores in 10 runs and two
 different bestmoves — g7g6 in 7 runs, e5e4 in 3. Threads 1 under the same settings: -293 in 5/5 runs,
 31,779 nodes every time."

THIS IS A THREADING CHECK, so Threads 4 is the subject and the swarm's Threads-1 rule does not apply to it; the
Threads-1 arm is the control.

My harness is my own. TEN fresh processes per arm. For each arm: the score, bestmove and node count per run, the
number of distinct scores, and the number of distinct bestmoves.

CONTROLS (enforced):
 - Threads 1 must be REPRODUCIBLE (else the machine or the harness is unstable and the Threads-4 spread cannot be
   attributed to threading): all 10 runs identical in score AND move, or the script aborts;
 - every process must actually reach depth 12 (else "at depth 12" is not what was measured);
 - the score must parse (no empty comparison — the vacuous-confirmation rule).
"""
import re
import subprocess
import sys
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
FENS = [
    ("04-F10 board (their ordinary middlegame)", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("second ordinary middlegame (mine, set G idx 1)", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
]
DEPTH = 12
RUNS = 10
BASE_OPTS = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
             ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
             ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
             ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
             ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
             ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run_once(threads, FEN):
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
    for n, v in BASE_OPTS:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("setoption name Threads value %d" % threads)
    sync()
    send("setoption name Hash value 16")
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
    depth_re = re.compile(r"^info depth (\d+) .*score (\S+) (\S+).*nodes (\d+)")
    last = None
    maxd = 0
    for l in lines:
        m = depth_re.match(l)
        if m:
            d = int(m.group(1))
            maxd = max(maxd, d)
            if d == DEPTH:
                last = (m.group(2), m.group(3), int(m.group(4)))
    bm = lines[-1].split()[1]
    return {"score": ("%s %s" % (last[0], last[1])) if last else None,
            "nodes": last[2] if last else None, "bm": bm, "maxd": maxd}


out = []


def emit(s):
    out.append(s)
    print(s)


results = {}
for label, fen in FENS:
    for threads in (1, 4):
        runs = [run_once(threads, fen) for _ in range(RUNS)]
        results[(label, threads)] = runs
        emit("## %s — Threads %d, %d fresh processes, depth %d" % (label, threads, RUNS, DEPTH))
        emit("")
        emit("| run | score | nodes | bestmove | reached depth |")
        emit("|---|---|---|---|---|")
        for i, r in enumerate(runs, 1):
            emit("| %d | %s | %s | %s | %d |" % (i, r["score"], r["nodes"], r["bm"], r["maxd"]))
        emit("")

# --- controls and verdict, per position
for label, fen in FENS:
    t1 = results[(label, 1)]
    t4 = results[(label, 4)]
    if any(r["maxd"] < DEPTH for r in t1 + t4):
        raise SystemExit("CONTROL FAILED: a run on %r did not reach depth %d" % (label, DEPTH))
    if any(r["score"] is None for r in t1 + t4):
        raise SystemExit("CONTROL FAILED: an unparsable depth-%d score on %r; comparison would be vacuous"
                         % (DEPTH, label))
    if len({r["score"] for r in t1}) != 1 or len({r["bm"] for r in t1}) != 1:
        raise SystemExit("CONTROL FAILED: Threads 1 is NOT reproducible on %r (%r) - a Threads-4 spread could "
                         "not be attributed to threading" % (label, ({r["score"] for r in t1},
                                                                    {r["bm"] for r in t1})))

emit("")
emit("## The spread — this is the question")
emit("| position | arm | distinct scores | distinct bestmoves | score range | nodes range |")
emit("|---|---|---|---|---|---|")
for label, fen in FENS:
    for threads in (1, 4):
        runs = results[(label, threads)]
        scores = {r["score"] for r in runs}
        bms = {r["bm"] for r in runs}
        ns = [r["nodes"] for r in runs]
        emit("| %s | Threads %d | **%d of %d** | **%d** (%s) | %s | %s..%s |" %
             (label[:34], threads, len(scores), len(runs), len(bms), ", ".join(sorted(bms)),
              ", ".join(sorted(scores)), min(ns), max(ns)))

emit("")
emit("### verdict per position")
for label, fen in FENS:
    t1b = {r["bm"] for r in results[(label, 1)]}
    t4b = {r["bm"] for r in results[(label, 4)]}
    t1s = {r["score"] for r in results[(label, 1)]}
    t4s = {r["score"] for r in results[(label, 4)]}
    emit("- **%s**: Threads 1 -> %d score / %d move; Threads 4 -> %d scores / %d moves. Move varies: **%s**. "
         "Score varies: **%s**." %
         (label[:40], len(t1s), len(t1b), len(t4s), len(t4b),
          "YES" if len(t4b) > 1 else "no", "YES" if len(t4s) > 1 else "no"))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
