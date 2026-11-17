#!/usr/bin/env python3
"""replay_pv.py EXE FEN BUDGET... -- replay the engine's PV in python-chess and report whether the line MATES.

This is the stronger test than comparing PV length against 2N-1: it proves the line does or does not end in
checkmate, rather than inferring it from a ply count. Adopted after seat 15 used it to confirm S-F63.

For each `go nodes N` budget: capture the last `info ... pv` line, replay every move with python-chess (stopping at
the first illegal one), and report the score, the PV length, whether the final position is checkmate, and the exact
ply at which a mate is delivered if there is one.
"""
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
FEN = sys.argv[2] if len(sys.argv) > 2 else "r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b - - 1 40"
BUDGETS = [int(x) for x in sys.argv[3:]] or [20000, 50000, 80000, 250000]

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


def run(go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def u(t, lim=300):
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
    s(f"position fen {FEN}"); s("isready"); u("readyok")
    s(go)
    ok = u("bestmove")
    s("quit")
    try:
        p.wait(timeout=25)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    return pv[-1] if pv else None


print(f"exe: {EXE}")
print(f"board: {FEN}")
print(f"PC20, Threads 1, Hash 16, OwnBook false. PV replay in python-chess.")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| budget | score | pv plies | replayed to | final position checkmate? | mate delivered at ply |")
print("|---|---|---|---|---|---|")

for n in BUDGETS:
    line = run(f"go nodes {n}")
    if line is None:
        print(f"| {n} | NO PV — not measured | - | - | - | - |")
        continue
    m = re.search(r"score (mate|cp) (-?\d+)", line)
    if not m:
        print(f"| {n} | NO SCORE — not measured | - | - | - | - |")
        continue
    kind, val = m.group(1), int(m.group(2))
    moves = line.split(" pv ", 1)[1].split() if " pv " in line else []
    board = chess.Board(FEN)
    played = 0
    illegal_at = None
    mate_at = None
    for i, uci in enumerate(moves):
        try:
            mv = chess.Move.from_uci(uci)
        except Exception:
            illegal_at = (i, uci, "unparsable")
            break
        if mv not in board.legal_moves:
            illegal_at = (i, uci, "illegal")
            break
        board.push(mv)
        played += 1
        if board.is_checkmate() and mate_at is None:
            mate_at = played
            # keep replaying only if there are more moves (should not be)
    ismate = board.is_checkmate()
    verdict = "**YES**" if ismate else "**NO**"
    if illegal_at:
        verdict += f" (PV had an illegal move at ply {illegal_at[0]}: {illegal_at[1]})"
    print(f"| {n} | {kind} {val:+d} | {len(moves)} | {played} plies | {verdict} | "
          f"{mate_at if mate_at else '—'} |")

print()
print("This is the mechanical proof: if the final position is not checkmate, the score's promise of mate in")
print("2|N|-1 plies is NOT delivered by the line the engine printed, whatever the ply count looks like.")
