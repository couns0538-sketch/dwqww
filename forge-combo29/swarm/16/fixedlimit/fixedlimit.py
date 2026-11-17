#!/usr/bin/env python3
"""fixedlimit.py EXE OUTDIR : S-F27's self-play diversity at a FIXED limit (no clock), 10 games, 20 plies.

Replicates seat 11's protocol but replaces the clock with a fixed budget: `go nodes 20000`, then `go depth 10`.
PC20, Threads 1, Hash 16, one process per game, position resent each move. Reports the distinct move sequences.
"""
import os
import re
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
GAMES = 10
PLIES = 20
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def play_game(gov):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=120):
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
    board = chess.Board(START)
    moves = []
    try:
        for _ in range(PLIES):
            if board.is_game_over(claim_draw=False):
                break
            send("ucinewgame"); send("isready"); to("readyok", 20)
            send("position fen " + board.fen()); send("isready"); to("readyok", 20)
            send(gov)
            lines, ok = to("bestmove", 200)
            if not ok:
                raise Missing(f"no bestmove for {gov}")
            best = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
            if best is None:
                raise Missing("no bestmove token")
            mv = chess.Move.from_uci(best)
            if mv not in board.legal_moves:
                raise Missing(f"illegal {best}")
            board.push(mv)
            moves.append(best)
    finally:
        try:
            send("quit"); p.wait(timeout=10)
        except Exception:
            p.kill()
    return " ".join(moves), board.fen()


out = [f"exe {EXE}", f"games {GAMES}, plies {PLIES}, start startpos",
       "PC20 + Threads 1 + Hash 16, one process per game, position resent each move", ""]
print(out[1])
for gov in ("go nodes 20000", "go depth 10"):
    seqs = []
    fins = []
    try:
        for g in range(1, GAMES + 1):
            s, f = play_game(gov)
            seqs.append(s)
            fins.append(f)
            print(f"  {gov} game {g}: {f[:40]}", flush=True)
    except Missing as exc:
        out.append(f"{gov}: NOT MEASURED: {exc}")
        print(out[-1])
        continue
    line = (f"{gov}: {GAMES} games, distinct MOVE SEQUENCES {len(set(seqs))}, "
            f"distinct FINAL positions {len(set(fins))}")
    out.append(line)
    print(line, flush=True)
    if len(set(seqs)) > 1:
        out.append("  distinct sequences:")
        for s in sorted(set(seqs))[:5]:
            out.append("    " + s)
    out.append("")
text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "fixedlimit.txt"), "w") as fh:
    fh.write(text)
