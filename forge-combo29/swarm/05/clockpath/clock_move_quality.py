#!/usr/bin/env python3
"""clock_move_quality.py EXE -- does the wtime shortfall cost MOVE QUALITY?

File 6 says what counts most is "a wrong move, a wrong score, a crash, a slow path" on the PC's real path. S-F37-S-F40
show a 6-second clock buys only ~0.2-0.7 s of search. This measures whether that changes the MOVE, by comparing:
  A) `go wtime 6000 btime 6000 winc 60 binc 60`   (what the owner's matches send)
  B) `go depth <depth A reached>`                  (the same search, reached explicitly)
  C) `go movetime 6000`                            (a full 6 seconds)
On many positions: does A pick the same move as C? Where they differ, C is the stronger search, so A's move is the
one at risk. Also reports A-vs-B (should match if A is really just "depth N"), which tests S-F37's claim.

Threads 1, Hash 16, OwnBook false throughout.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
REGIME = sys.argv[2] if len(sys.argv) > 2 else "PC20"

S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16",
       "setoption name OwnBook value false"]
SIX = ["setoption name CuckooRep value true", "setoption name HistRework value 2",
       "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
       "setoption name MateAlphaGuard value true"]
OPTS = {"S14": S14, "PC20": S14 + SIX}[REGIME]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


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
            if any(b in l for b in BAD):
                return False
            if l.startswith(t):
                return True
        return False

    s("uci"); u("uciok")
    for o in OPTS:
        s(o); s("isready")
        if not u("readyok"):
            p.kill()
            return None
    s("ucinewgame"); s("isready"); u("readyok")
    s("position fen " + fen)
    s("isready"); u("readyok")
    t0 = time.monotonic()
    s(go)
    ok = u("bestmove")
    wall = time.monotonic() - t0
    s("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    last = pv[-1] if pv else ""
    d = re.search(r"depth (\d+)", last)
    sc = re.search(r"score (mate|cp) (-?\d+)", last)
    bm = next((x for x in L if x.startswith("bestmove")), None)
    return dict(wall=wall, depth=int(d.group(1)) if d else None,
                score=f"{sc.group(1)} {sc.group(2)}" if sc else None,
                move=(bm.split()[1] if bm and len(bm.split()) > 1 else None))


fens = []
for line in open("../job1/data/G.epd"):
    fens.append(line.split(";")[0].strip())
fens = [f for f in fens if f][:12]

print(f"exe: {EXE}   regime {REGIME}   Threads 1, Hash 16, OwnBook false   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| # | wtime 6000: move / depth / %used | depth-N replay: move | movetime 6000: move / depth | A==C? | A==B? |")
print("|---|---|---|---|---|---|")
same_ac = same_ab = n = 0
for i, fen in enumerate(fens):
    A = run(fen, "go wtime 6000 btime 6000 winc 60 binc 60")
    if not A:
        print(f"| {i} | REFUSED | - | - | - | - |")
        continue
    B = run(fen, f"go depth {A['depth']}")
    C = run(fen, "go movetime 6000")
    if not B or not C:
        print(f"| {i} | {A['move']} / d{A['depth']} / {100*A['wall']/6:.1f}% | REFUSED | REFUSED | - | - |")
        continue
    n += 1
    ac = (A["move"] == C["move"])
    ab = (A["move"] == B["move"])
    same_ac += ac
    same_ab += ab
    print(f"| {i} | {A['move']} / d{A['depth']} / {100*A['wall']/6:.1f}% | {B['move']} | "
          f"{C['move']} / d{C['depth']} | {'yes' if ac else '**NO**'} | {'yes' if ab else 'NO'} |")
print()
print(f"positions compared: {n}")
print(f"wtime move == movetime move: {same_ac}/{n}  (where they differ, the wtime move came from a much shallower search)")
print(f"wtime move == `go depth {{{{A depth}}}}` move: {same_ab}/{n}  (tests S-F37's claim that wtime is effectively a depth cap in effect)")
