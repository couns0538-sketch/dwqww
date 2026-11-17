#!/usr/bin/env python3
"""deepgain_test.py EXE -- test seat 15's class-level claim on MY OWN positions and binary.

The claim (seat 15, reproduced in counts by seat 17): at the owner's clock, then a completed deeper search on the same
board, SPARSE ENDGAMES gain mates that the clocked search reported only as a score (2 of 5, median 312 cp movement),
while MIDDLEGAMES do not (0 of 5, median 12 cp).

My version: my own 8 sparse endgames and 8 middlegames, my own PC r15 build, PC20, Threads 1, Hash 16, OwnBook false.
For each position, FRESH PROCESS for each of the two searches:
  1. clocked:  `go wtime 6000 btime 6000 winc 60 binc 60`   -> score, depth D
  2. deeper:   `go depth D+4`                                -> score, and is it a mate?
Then: how many positions GAIN a mate (clocked cp -> deeper mate), and the score movement in cp on the rest.
Any mate the deeper search claims is REPLAYED in python-chess (replay rule), so a claimed mate must actually mate.
"""
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
DPLUS = int(sys.argv[2]) if len(sys.argv) > 2 else 4

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

# ---- my own 8 sparse endgames (3-6 pieces, constructed here, not taken from another seat) ----
SPARSE = [
    ("KQ v K, king active",      "8/8/8/8/4k3/8/8/KQ6 w - - 0 1"),
    ("KQ v K, king boxed",       "8/8/8/8/8/5k2/8/K1Q5 w - - 0 1"),
    ("KR v K, king cut",         "8/8/8/8/4k3/8/8/K1R5 w - - 0 1"),
    ("KR v K, rook active",      "8/8/8/3k4/8/8/8/KR6 w - - 0 1"),
    ("KBB v K, bare",            "8/8/8/8/4k3/8/8/KBB5 w - - 0 1"),
    ("KQ v KR, queen up",        "8/8/8/8/3rk3/8/8/K1Q5 w - - 0 1"),
    ("KRP v KP, extra rook",     "8/8/8/8/4k3/5p2/4P3/K1R5 w - - 0 1"),
    ("KQ v K, far corner",       "7k/8/8/8/8/8/8/KQ6 w - - 0 1"),
]

# ---- my own 8 middlegames: positions from random play with many pieces (built here, reproducible seed) ----
import random


def _middlegames(n=8):
    R = random.Random(31337)
    out = []
    tries = 0
    while len(out) < n and tries < 6000:
        tries += 1
        b = chess.Board()
        for _ in range(R.randint(16, 40)):
            lg = list(b.legal_moves)
            if not lg:
                break
            b.push(R.choice(lg))
        if b.is_game_over(claim_draw=False):
            continue
        if len(b.piece_map()) < 20:          # middlegame = many pieces
            continue
        if b.is_check():
            continue
        out.append((f"midgame {len(out)+1} ({len(b.piece_map())} pieces)", b.fen()))
    return out


MID = _middlegames(8)


def search(fen, go):
    """fresh process per call — COLD, per my MEASURING rule"""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def u(t, lim=400):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                return False
            l = l.rstrip(); L.append(l)
            if any(b in l for b in BAD):
                return False
            if l.startswith(t):
                return True
        return False

    s("uci")
    if not u("uciok"):
        p.kill(); return None
    for o in OPTS:
        s(o); s("isready")
        if not u("readyok"):
            p.kill(); return None
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(go)
    ok = u("bestmove")
    s("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    d = re.search(r"depth (\d+)", last)
    if not m or not d:
        return None
    moves = last.split(" pv ", 1)[1].split() if " pv " in last else []
    return dict(kind=m.group(1), val=int(m.group(2)), depth=int(d.group(1)),
                moves=moves, line=last)


def cp_of(r):
    """map a score to cp for movement arithmetic; mate scores use a large sentinel"""
    if r["kind"] == "cp":
        return r["val"]
    return 100000 - abs(r["val"]) if r["val"] > 0 else -(100000 - abs(r["val"]))


def replay(fen, moves):
    """REPLAY rule: does the line actually end in checkmate, and is every move legal?"""
    b = chess.Board(fen)
    for i, uci in enumerate(moves):
        try:
            mv = chess.Move.from_uci(uci)
        except Exception:
            return False, i, "unparsable"
        if mv not in b.legal_moves:
            return False, i, "illegal"
        b.push(mv)
    return b.is_checkmate(), len(moves), "ok"


def run_set(name, positions):
    print(f"### {name}")
    print()
    print("| position | clocked score | D | deeper (D+%d) | gained mate? | cp movement | replay |" % DPLUS)
    print("|---|---|---|---|---|---|---|")
    gained = 0
    movements = []
    for label, fen in positions:
        c = search(fen, "go wtime 6000 btime 6000 winc 60 binc 60")
        if c is None:
            print(f"| {label} | NO MEASUREMENT | - | - | - | - | - |")
            continue
        d = search(fen, f"go depth {c['depth'] + DPLUS}")
        if d is None:
            print(f"| {label} | {c['kind']} {c['val']:+d} | {c['depth']} | NO MEASUREMENT | - | - | - |")
            continue
        cclock = f"{c['kind']} {c['val']:+d}"
        cdeep = f"{d['kind']} {d['val']:+d}"
        gained_mate = (c["kind"] == "cp" and d["kind"] == "mate" and d["val"] > 0)
        if gained_mate:
            gained += 1
            mv_txt = "GAINED MATE"
        else:
            mv = abs(cp_of(d) - cp_of(c))
            movement = mv if mv < 90000 else None   # exclude mate-vs-cp sentinel arithmetic
            if movement is not None:
                movements.append(movement)
                mv_txt = f"{movement} cp"
            else:
                mv_txt = "mate vs score (excluded)"
        rp = "—"
        if d["kind"] == "mate":
            ok, nply, why = replay(fen, d["moves"])
            rp = ("**MATES at ply %d**" % nply) if ok else f"**NOT A MATE** ({why} at ply {nply})"
        print(f"| {label} | {cclock} | {c['depth']} | {cdeep} d{d['depth']} | "
              f"{'**YES**' if gained_mate else 'no'} | {mv_txt} | {rp} |")
    movements.sort()
    med = movements[len(movements) // 2] if movements else None
    print()
    print(f"**{name}: {gained} of {len(positions)} gained a mate**"
          + (f"; median cp movement on the rest: {med} cp (n={len(movements)})" if med is not None else ""))
    print()
    return gained, med, len(movements)


print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   fresh process per search")
print(f"clock: go wtime 6000 btime 6000 winc 60 binc 60 ; then go depth D+{DPLUS}")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
sg, sm, sn = run_set("SPARSE ENDGAMES (my construction)", SPARSE)
mg, mm, mn = run_set("MIDDLEGAMES (my construction, 20+ pieces)", MID)

print("=" * 90)
print(f"SPARSE: {sg} of {len(SPARSE)} gained a mate; median movement {sm} cp on the rest")
print(f"MIDDLE: {mg} of {len(MID)} gained a mate; median movement {mm} cp on the rest")
print()
print("seat 15 / seat 17 reported: sparse 2 of 5 (median 312 cp), middlegame 0 of 5 (median 12 cp).")
print("A zero on sparse here does not refute them — it would mean the effect is position-set dependent.")
