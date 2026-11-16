#!/usr/bin/env python3
"""match_clock_game.py EXE -- play a whole GAME at the owner's match clock (6 s + 0.06), PC20, Threads 1, Hash 16,
OwnBook false, and record per move: what the engine actually spent, the depth reached, and whether the clock held.

This is file 6's "worth most" path: the real match condition rather than a single search. Two questions:
  1. across a whole game, does the unspent-clock behaviour persist (S-F37-S-F44) or does the increment accumulate?
  2. does either side ever lose on time, or produce an illegal move?
Self-play, so both sides use the same clock; the game ends at mate, a repetition, the 50-move rule, or 80 moves.
"""
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
START_FEN = sys.argv[2] if len(sys.argv) > 2 else None
MAX_MOVES = int(sys.argv[3]) if len(sys.argv) > 3 else 80

WTIME = 6000
WINC = 60

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


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        self.until("uciok")
        for o in OPTS:
            self.send(o)
            self.send("isready")
            self.until("readyok")

    def send(self, x):
        self.p.stdin.write(x + "\n")
        self.p.stdin.flush()

    def until(self, tok, lim=200):
        L = []
        t0 = time.time()
        while time.time() - t0 < lim:
            l = self.p.stdout.readline()
            if l == "":
                return L, False
            l = l.rstrip()
            L.append(l)
            if l.startswith(tok):
                return L, True
            if any(b in l for b in BAD):
                return L, False
        return L, False

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


board = chess.Board(START_FEN) if START_FEN else chess.Board()
e = Engine()

white_ms = WTIME
black_ms = WTIME
rows = []
illegal = 0
lost_on_time = None
result = None

print(f"exe: {EXE}   clock {WTIME} + {WINC}   Threads 1, Hash 16, OwnBook false, PC20   "
      f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| move | side | wall (s) | depth | nodes | white ms left | black ms left | move played |")
print("|---|---|---|---|---|---|---|---|")

for ply in range(MAX_MOVES * 2):
    if board.is_game_over(claim_draw=True):
        result = ("mate/stalemate" if board.is_checkmate() or board.is_stalemate() else "draw rule")
        break
    side = "white" if board.turn else "black"
    cmd = (f"go wtime {white_ms} btime {black_ms} winc {WINC} binc {WINC}")
    t0 = time.monotonic()
    e.send(f"position fen {board.fen()}")
    e.send("isready")
    e.until("readyok")
    e.send(cmd)
    L, ok = e.until("bestmove")
    wall = time.monotonic() - t0
    if not ok:
        result = "NO BESTMOVE"
        break
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    last = pv[-1] if pv else ""
    d = re.search(r"depth (\d+)", last)
    nm = re.search(r"\bnodes (\d+)", last)
    bm = next((x for x in L if x.startswith("bestmove")), "")
    toks = bm.split()
    mv = toks[1] if len(toks) > 1 else None

    # clock accounting
    spent = int(wall * 1000)
    if side == "white":
        white_ms = white_ms - spent + WINC
    else:
        black_ms = black_ms - spent + WINC
    if white_ms <= 0 or black_ms <= 0:
        lost_on_time = side
        result = f"{side} LOST ON TIME"
        break

    try:
        m = chess.Move.from_uci(mv)
        if m not in board.legal_moves:
            illegal += 1
            result = f"ILLEGAL MOVE {mv}"
            break
        san = board.san(m)
        board.push(m)
    except Exception as ex:
        illegal += 1
        result = f"UNPARSABLE MOVE {mv}: {ex}"
        break

    rows.append((board.ply(), side, wall, d.group(1) if d else None,
                 nm.group(1) if nm else None, white_ms, black_ms, san))
    print(f"| {board.ply()} | {side} | {wall:.2f} | {d.group(1) if d else '-'} | "
          f"{nm.group(1) if nm else '-'} | {white_ms} | {black_ms} | {san} |")
    if len(rows) >= MAX_MOVES * 2:
        result = "move limit reached"
        break

e.close()

print()
print(f"plies played: {len(rows)}")
print(f"result: {result}")
print(f"illegal moves: {illegal}")
print(f"lost on time: {lost_on_time}")
print(f"final white/black ms: {white_ms}/{black_ms}")
print(f"final position: {board.fen()}")
if rows:
    walls = [r[2] for r in rows]
    depths = [int(r[3]) for r in rows if r[3]]
    print(f"per-move wall: min {min(walls):.2f} median {sorted(walls)[len(walls)//2]:.2f} max {max(walls):.2f}")
    print(f"depths reached: min {min(depths)} median {sorted(depths)[len(depths)//2]} max {max(depths)}")
