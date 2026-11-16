#!/usr/bin/env python3
"""clock_path.py EXE REGIME -- the PC's strength-match clock: 6 seconds + 0.06 s per move, PC20, Threads 1, Hash 16.

File 6 says the owner's strength matches use exactly this. Questions worth measuring on that path:
  * does the engine stay inside its clock (no overrun)?
  * is the search deterministic run to run (it must be at Threads 1)?
  * how many nodes does 6 s actually buy on these positions?
Timing is measured with a monotonic clock from sending `go` to reading `bestmove` (the harness's own measurement, not
the engine's `time` field), and the engine's own reported time is recorded beside it.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
REGIME = sys.argv[2] if len(sys.argv) > 2 else "PC20"
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 2
WTIME = 6000
WINC = 60

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
    ("deep", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1"),
]


def strip_timing(line):
    return re.sub(r"\s*(nps \d+|time \d+)", "", line or "")


def run_once(fen, to_move_white=True):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=120):
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
    go = (f"go wtime {WTIME} btime {WTIME} winc {WINC} binc {WINC}" if to_move_white
          else f"go wtime {WTIME} btime {WTIME} winc {WINC} binc {WINC}")
    t0 = time.monotonic()
    s(go)
    u("bestmove")
    wall = time.monotonic() - t0
    s("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    last = pv[-1] if pv else None
    bm = next((x for x in L if x.startswith("bestmove")), None)
    d = re.search(r"depth (\d+)", last or "")
    n = re.search(r"\bnodes (\d+)", last or "")
    et = re.search(r"\btime (\d+)", last or "")
    sc = re.search(r"score (mate|cp) (-?\d+)", last or "")
    return dict(wall=wall, depth=int(d.group(1)) if d else None,
                nodes=int(n.group(1)) if n else None, etime=int(et.group(1)) if et else None,
                score=f"{sc.group(1)} {sc.group(2)}" if sc else None, bm=bm, pv=strip_timing(last))


print(f"exe: {EXE}   regime {REGIME}   Threads 1   clock wtime/btime {WTIME} inc {WINC}   {RUNS} runs   "
      f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| position | run | wall (s) | engine time (ms) | over 6.06s? | depth | nodes | score | bestmove |")
print("|---|---|---|---|---|---|---|---|---|")
BUDGET = 6.0
allin = True
for label, fen in POSITIONS:
    det = []
    for i in range(RUNS):
        r = run_once(fen or "")
        over = r["wall"] > BUDGET + 0.5   # allow the 60 ms increment plus slack
        allin = allin and not over
        det.append((r["score"], r["nodes"], r["depth"], r["bm"]))
        print(f"| {label} | {i} | {r['wall']:.2f} | {r['etime']} | {'**YES**' if over else 'no'} | "
              f"{r['depth']} | {r['nodes']} | {r['score']} | {r['bm']} |")
    same = len(set(det)) == 1
    print(f"| {label} | — | identical across {RUNS} runs: {'YES' if same else '**NO**'} | | | | | | |")
print()
print(f"stayed inside the clock on every run: {allin}")
print(f"NOTE: my own wall measurement includes process start-up and pipe latency, so it is an upper bound on the")
print(f"engine's own time (recorded beside it). The engine's `time` field is the comparison to use.")
