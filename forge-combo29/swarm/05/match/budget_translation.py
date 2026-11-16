#!/usr/bin/env python3
"""budget_translation.py EXE -- compares what each of the owner's real controls actually buys, in DEPTH.

The owner's PC uses, per file 6: `go softnodes 2000` (self-play), `go nodes` 20000/50000/250000 (matches), and the
clock 6 s + 0.06 (strength matches). This measures all of them on the same boards so the effective strengths are
comparable, and answers: is the 6-second clock WORSE than a small node budget?

Threads 1, Hash 16, OwnBook false, PC20.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"

OPTS = ["setoption name Threads value 1", "setoption name Hash value 16",
        "setoption name OwnBook value false",
        "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
        "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
        "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
        "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
        "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
        "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
        "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
        "setoption name CuckooRep value true", "setoption name HistRework value 2",
        "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
        "setoption name MateAlphaGuard value true"]

CONTROLS = [
    ("softnodes 2000 (self-play)", "go softnodes 2000"),
    ("nodes 20000 (match)", "go nodes 20000"),
    ("nodes 50000 (match)", "go nodes 50000"),
    ("nodes 250000 (match)", "go nodes 250000"),
    ("clock 6s+0.06 (strength match)", "go wtime 6000 btime 6000 winc 60 binc 60"),
    ("movetime 6000", "go movetime 6000"),
]

POSITIONS = [
    ("startpos", None),
    ("G0 mid", "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"),
    ("deep mid", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1"),
]


def run(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=200):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                return False
            l = l.rstrip()
            L.append(l)
            if l.startswith(t):
                return True
        return False

    s("uci"); u("uciok")
    for o in OPTS:
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s("position fen " + fen if fen else "position startpos")
    s("isready"); u("readyok")
    t0 = time.monotonic()
    s(go)
    ok = u("bestmove")
    wall = time.monotonic() - t0
    s("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    last = pv[-1] if pv else ""
    d = re.search(r"depth (\d+)", last)
    n = re.search(r"\bnodes (\d+)", last)
    sc = re.search(r"score (mate|cp) (-?\d+)", last)
    bm = next((x for x in L if x.startswith("bestmove")), "")
    return dict(depth=int(d.group(1)) if d else None, nodes=int(n.group(1)) if n else None,
                score=f"{sc.group(1)} {sc.group(2)}" if sc else None,
                move=(bm.split()[1] if len(bm.split()) > 1 else None), wall=wall)


print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("What each of the owner's real controls buys, on the same boards:")
print()
print("| control | " + " | ".join(p[0] for p in POSITIONS) + " |")
print("|---|---|---|---|")
for label, go in CONTROLS:
    cells = []
    for _pname, fen in POSITIONS:
        r = run(fen or "", go)
        if r is None:
            cells.append("REFUSED")
        else:
            cells.append(f"d{r['depth']} {r['nodes']}n {r['score']}")
    print(f"| {label} | " + " | ".join(cells) + " |")
print()
print("Reading: compare the DEPTH column-wise. If the 6-second clock's depth is below `nodes 20000`, then a clock")
print("game is weaker than a 20,000-node game on those positions, which is the operational consequence of S-F37-S-F44.")
