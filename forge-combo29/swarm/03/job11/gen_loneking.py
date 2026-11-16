#!/usr/bin/env python3
"""gen_loneking.py N SEED OUT : build a set of real-game positions with a lone king on the board.

"Real game" means: played by my own search driver as a real game (both sides the engine at a fixed depth under S14
and the same settings the PC uses), and every position where one side owns nothing but its king is a candidate. This
reaches lone-king endings the way games actually reach them, instead of constructing them.

To get 50 candidates efficiently, each game is sampled: play until one side has a lone king, then take the first
position with a lone king, and stop that game (so the set does not consist of 50 near-identical positions from one
long ending). Games are played at depth 6 for speed; this is a POSITION GENERATOR, not a strength measurement.

Records for each candidate: the FEN, which side has the lone king, the material, and the game/ply it came from.
"""
import hashlib
import os
import subprocess
import sys

import chess

TARGET = int(sys.argv[1])
SEED = int(sys.argv[2])
OUT = sys.argv[3]
EXE = os.environ.get("LK_EXE", "/home/ubuntu/build-pc/forge")
DEPTH = int(os.environ.get("LK_DEPTH", "6"))
rawdir = OUT + ".raw"
os.makedirs(rawdir, exist_ok=True)

S14 = [("Threads", "1"), ("Hash", "16"), ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"),
       ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"),
       ("NullMoveBase", "5"), ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"),
       ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"),
       ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("OwnBook", "false")]


def bestmove(fen, tag):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"died waiting {tok} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            if s.startswith(tok):
                return s

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for o, v in S14:
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go depth {DEPTH}")
    mv = None
    while True:
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError(f"died before bestmove ({tag})")
        raw.write(line)
        raw.flush()
        if line.strip().startswith("bestmove"):
            mv = line.split()[1]
            break
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    return mv


def lone_side(b):
    """a colour owning nothing but its king. NOTE: b.pieces() returns a SquareSet, and comparing it to the int
    occupied_co[col] is silently False — int(...) is required. (First version of this file omitted the int() and
    found 0 candidates in 40 games; caught by a sanity check, not by luck.)"""
    for col in (chess.WHITE, chess.BLACK):
        if b.occupied_co[col] == int(b.pieces(chess.KING, col)):
            return col
    return None


def self_test():
    """known-answer test of the predicate: it must fire on a lone king, and NOT on K+N or a full board."""
    lone = chess.Board("8/8/8/8/8/5n2/4K1k1/8 w - - 0 60")        # white K only vs black K+N
    both = chess.Board("8/8/8/8/8/5n2/4K1k1/4N3 b - - 11 60")     # K+N vs K+N: neither side is lone
    full = chess.Board()
    got = (lone_side(lone), lone_side(both), lone_side(full))
    ok = got[0] is not None and got[1] is None and got[2] is None
    print(f"self_test: lone -> {got[0]}, K+N vs K+N -> {got[1]}, full board -> {got[2]}, pass={ok}")
    if not ok:
        raise SystemExit("FAIL: lone_side is broken; refusing to generate a meaningless position set")
    return ok


self_test()
cands, game, seen = [], 0, set()
while len(cands) < TARGET and game < TARGET * 40:
    game += 1
    b = chess.Board()
    ply = 0
    while ply < 300:
        if b.is_game_over(claim_draw=False):
            break
        if ply >= 10 and lone_side(b) is not None:
            fen = b.fen()
            h = hashlib.sha1(fen.encode()).hexdigest()[:10]
            if h not in seen:
                seen.add(h)
                cands.append((fen, "white" if lone_side(b) == chess.WHITE else "black", game, ply))
            break
        fen = b.fen()
        h = hashlib.sha1(fen.encode()).hexdigest()[:12]
        mv = bestmove(fen, f"g{game:03d}_p{ply:03d}_{h}")
        if mv not in [m.uci() for m in b.legal_moves]:
            raise RuntimeError(f"illegal engine move {mv} in game {game} ply {ply}: {fen}")
        b.push_uci(mv)
        ply += 1
    if game % 10 == 0:
        print(f"game {game}, candidates {len(cands)}", flush=True)

with open(OUT, "w") as f:
    for fen, side, g, ply in cands:
        f.write(f"{fen}\t{side}\tgame {g} ply {ply}\n")
print(f"wrote {len(cands)} lone-king positions from {game} games to {OUT}")
