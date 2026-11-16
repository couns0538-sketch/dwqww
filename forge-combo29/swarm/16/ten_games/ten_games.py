#!/usr/bin/env python3
"""ten_games.py EXE OUTDIR : does the clock-utilisation fraction drift across a self-play game?

Ten games of up to 60 moves, PC build under PC20, Threads 1, Hash 16, 6.00 s + 0.06 s per side, one process
per game (as a match program would run it). After every move the clock is decremented by the WALL time measured
and incremented by 0.06 s, so the clock state evolves as in a real game.

For each game it reports: the fraction of the *allocated* time the engine used on each tenth of the game, the
overall range, and whether the fraction trends. Pooled across ten games it reports the fraction by game phase
(first / middle / last third), which is the question: does 2.6-5.3 % stay stable over a game or drift?
"""
import os
import re
import statistics
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
GAMES = 10
MAX_MOVES = 60
START_MS = 6000
INC_MS = 60

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def play_game(g):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=60):
        out = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return out, False
            l = l.rstrip("\n")
            out.append(l)
            if l.strip().startswith(tok):
                return out, True
        return out, False

    send("uci"); uci, ok = to("uciok", 20)
    if not ok:
        raise Missing("no uciok")
    known = {m.group(1) for l in uci for m in [re.match(r"option name (.*) type ", l)] if m}
    send("isready"); to("readyok", 20)
    for n, v in PC20.items():
        if n not in known:
            raise Missing(f"option {n} absent")
        send(f"setoption name {n} value {v}")
        send("isready"); to("readyok", 20)

    board = chess.Board()
    w, b = START_MS, START_MS
    rows = []
    try:
        for mv_no in range(1, MAX_MOVES + 1):
            if board.is_game_over(claim_draw=False):
                break
            send("ucinewgame"); send("isready"); to("readyok", 20)
            send("position fen " + board.fen())
            send("isready"); to("readyok", 20)
            clock = w if board.turn == chess.WHITE else b
            cmd = f"go wtime {w} btime {b} winc {INC_MS} binc {INC_MS}"
            t0 = time.monotonic()
            send(cmd)
            lines, ok = to("bestmove", 60)
            wall = (time.monotonic() - t0) * 1000.0
            if not ok:
                raise Missing(f"no bestmove on move {mv_no} of game {g}")
            best = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
            if best is None:
                raise Missing("no bestmove token")
            mv = chess.Move.from_uci(best)
            if mv not in board.legal_moves:
                raise Missing(f"ILLEGAL {best} game {g} move {mv_no}")
            allowed = clock + INC_MS
            rows.append({"move": mv_no, "turn": "w" if board.turn else "b", "clock": clock,
                         "allowed": allowed, "wall": wall, "frac": wall / allowed, "best": best})
            board.push(mv)
            if board.turn == chess.BLACK:
                w = max(1, int(w - wall + INC_MS))
            else:
                b = max(1, int(b - wall + INC_MS))
    finally:
        try:
            send("quit")
            p.wait(timeout=10)
        except Exception:
            p.kill()
    return rows, board.fen(), board.is_game_over(claim_draw=False)


all_games = []
out = [f"exe {EXE}", f"games {GAMES}, up to {MAX_MOVES} moves each, {START_MS} ms + {INC_MS} ms",
       "PC20 + Threads 1 + Hash 16, one process per game, position resent each move", ""]
print(out[0])
for g in range(1, GAMES + 1):
    try:
        rows, final_fen, over = play_game(g)
    except Missing as exc:
        out.append(f"game {g}: NOT MEASURED: {exc}")
        print(out[-1], flush=True)
        continue
    all_games.append(rows)
    fr = [r["frac"] for r in rows]
    over_cnt = sum(1 for r in rows if r["wall"] > r["allowed"])
    line = (f"game {g:2d}: moves {len(rows):3d}  fraction min {min(fr)*100:4.2f}% "
            f"median {statistics.median(fr)*100:4.2f}% max {max(fr)*100:4.2f}%  overruns {over_cnt}"
            f"  final {final_fen[:28]}")
    out.append(line)
    print(line, flush=True)
    out.append("   per-move fraction (first 20): " +
               " ".join(f"{r['frac']*100:.1f}" for r in rows[:20]))

# pooled by game third
pooled = []
for rows in all_games:
    n = len(rows)
    if n < 6:
        continue
    third = max(1, n // 3)
    for i, r in enumerate(rows):
        phase = "first" if i < third else ("last" if i >= n - third else "middle")
        pooled.append((phase, r["frac"]))
out.append("")
out.append("### pooled by game phase (all games)")
for phase in ("first", "middle", "last"):
    v = [f for p, f in pooled if p == phase]
    if v:
        out.append(f"  {phase:6s}: n {len(v):4d}  median {statistics.median(v)*100:5.2f}%  "
                   f"min {min(v)*100:5.2f}%  max {max(v)*100:5.2f}%")
        print(out[-1], flush=True)
allf = [f for _, f in pooled]
out.append(f"  ALL   : n {len(allf):4d}  median {statistics.median(allf)*100:5.2f}%  "
           f"min {min(allf)*100:5.2f}%  max {max(allf)*100:5.2f}%")
text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "ten_games.txt"), "w") as fh:
    fh.write(text)
print(text.splitlines()[-1])
