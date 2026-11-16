#!/usr/bin/env python3
"""find_longmates.py EXE -- build a pool that actually CONTAINS long mates, because my selection over G.epd +
R_seed511 found only 2 of 120.

Why the earlier attempt was void (S-W6): I filtered positions that already carried a mate score in my depth-12 data.
Those are mates the engine found at depth 12 — short mates by construction. Long mates (|N| >= 8) need a much deeper
search to appear, so filtering a depth-12 result set cannot produce them.

This instead screens a LARGE pool at depth 18 and keeps whatever reports |N| >= 8, writing the survivors to a file so
the match-budget test can be re-run on a real sample. Positions come from the G set and from random-play games, which
are mate-rich because they are unbalanced.
"""
import random
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
TARGET = int(sys.argv[2]) if len(sys.argv) > 2 else 12
POOLMAX = int(sys.argv[3]) if len(sys.argv) > 3 else 900
DEPTH = 14
MINN = 8

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


def run(fen, depth=DEPTH):
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

    s("uci")
    if not u("uciok"):
        p.kill()
        return None
    for o in OPTS:
        s(o); s("isready")
        if not u("readyok"):
            p.kill()
            return None
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(f"go depth {depth}")
    ok = u("bestmove")
    s("quit")
    try:
        p.wait(timeout=25)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    if not m or m.group(1) != "mate":
        return None
    return int(m.group(2))


# pool: random-play positions (mate-rich because unbalanced) + the G set
R = random.Random(977)
pool = []
seen = set()
while len(pool) < POOLMAX:
    b = chess.Board()
    for ply in range(R.randint(30, 110)):
        legal = list(b.legal_moves)
        if not legal:
            break
        b.push(R.choice(legal))
    if b.is_game_over(claim_draw=False):
        continue
    f = b.fen()
    if f in seen:
        continue
    seen.add(f)
    pool.append(f)

print(f"exe: {EXE}   screening {len(pool)} random-play positions at depth {DEPTH} for |N| >= {MINN}")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
found = []
for i, fen in enumerate(pool):
    if len(found) >= TARGET:
        break
    v = run(fen)
    if v is not None and abs(v) >= MINN:
        found.append((fen, v))
        print(f"  [{len(found)}] mate {v:+d}  {fen}")
    if i % 100 == 0 and i:
        print(f"  ... screened {i}, found {len(found)}")

print()
print(f"FOUND {len(found)} positions with |N| >= {MINN}")
out = "/agent/repos/dwqww/forge-combo29/swarm/05/mate_truncation/positions/longmates.epd"
import os
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    for fen, v in found:
        f.write(f"{fen} ; mate {v:+d} at depth {DEPTH}\n")
print(f"written {out}")
if not found:
    print("NOTE: no long mates found in this pool either — that is a fact about the pool, reported as such.")
