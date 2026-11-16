#!/usr/bin/env python3
"""cold_vs_warm.py EXE -- is my depth figure cold or warm? The coordinator reported that, at the SAME wall time,
a fresh process per position gives median depth 18 while ONE warm process gives 20, and inferred my depth-22 came
from a warm process.

This tests that on MY harness and MY board, with three disciplines side by side at the same clock/increment:
  COLD  : one fresh process per run (what my increment_scaling.py does — a new Popen each time)
  WARM  : ONE process, the same position searched RUNS times in a row with no ucinewgame between
  UCINEW: ONE process, but `ucinewgame` + `isready` before each search (the protocol my harness uses per position)

Reports, for each discipline: median wall, median depth, max depth, and whether the depth differs at matched wall.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
CLOCK = 6000
INC = 60000        # a big increment so the search is time-limited and depth is meaningful to compare
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 5

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
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

FEN = "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"


def _open():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    return p


def _send(p, x):
    p.stdin.write(x + "\n")
    p.stdin.flush()


def _until(p, tok, lim=400):
    L = []
    t0 = time.time()
    while time.time() - t0 < lim:
        l = p.stdout.readline()
        if l == "":
            return L, False
        l = l.rstrip()
        L.append(l)
        if any(b in l for b in BAD):
            return L, False
        if l.startswith(tok):
            return L, True
    return L, False


def _setup(p):
    _send(p, "uci"); _until(p, "uciok")
    for o in OPTS:
        _send(p, o); _send(p, "isready"); _until(p, "readyok")


def _search(p, want_ucinew):
    if want_ucinew:
        _send(p, "ucinewgame"); _send(p, "isready"); _until(p, "readyok")
    _send(p, f"position fen {FEN}"); _send(p, "isready"); _until(p, "readyok")
    t0 = time.monotonic()
    _send(p, f"go wtime {CLOCK} btime {CLOCK} winc {INC} binc {INC}")
    L, ok = _until(p, "bestmove")
    wall = time.monotonic() - t0
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    d = re.search(r"depth (\d+)", pv[-1])
    et = re.search(r"\btime (\d+)", pv[-1])
    return dict(wall=wall, depth=int(d.group(1)) if d else None,
                etime=int(et.group(1)) if et else None)


def cold():
    out = []
    for _ in range(RUNS):
        p = _open()
        _setup(p)
        r = _search(p, want_ucinew=False)   # fresh process, no ucinewgame needed
        _send(p, "quit")
        try:
            p.wait(timeout=20)
        except Exception:
            p.kill()
        if r:
            out.append(r)
    return out


def warm(ucinew):
    p = _open()
    _setup(p)
    out = []
    for _ in range(RUNS):
        r = _search(p, want_ucinew=ucinew)
        if r:
            out.append(r)
    _send(p, "quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    return out


def med(v):
    v = sorted(x for x in v if x is not None)
    return v[len(v) // 2] if v else None


print(f"exe: {EXE}   clock {CLOCK} inc {INC}   Threads 1, Hash 16, OwnBook false")
print(f"board: {FEN}")
print(f"{RUNS} runs per discipline, SEQUENTIAL   date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| discipline | n | median wall (ms) | median depth | depths seen |")
print("|---|---|---|---|---|")
for label, res in (("COLD (fresh process per run)", cold()),
                   ("WARM (one process, no ucinewgame)", warm(False)),
                   ("UCINEW (one process, ucinewgame each)", warm(True))):
    if not res:
        print(f"| {label} | 0 | NO MEASUREMENT | - | - |")
        continue
    print(f"| {label} | {len(res)} | {med([r['wall']*1000 for r in res]):.0f} | "
          f"{med([r['depth'] for r in res])} | {sorted(set(r['depth'] for r in res))} |")
print()
print("This is the direct test: my increment_scaling.py calls subprocess.Popen inside run(), so it is the COLD row.")
