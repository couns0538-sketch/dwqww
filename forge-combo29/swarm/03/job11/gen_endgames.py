#!/usr/bin/env python3
"""gen_endgames.py N OUT : lone-king endings from material-imbalanced play.

Why not self-play games (see prediction_amendment.txt): every engine-vs-engine game at depth 6 collapsed into the
same K+N vs K+N drawn position, so self-play yields no varied lone-king population. Real games reach a lone king
because one side has converted an advantage, so each game here starts from a position where one side is materially
ahead and both sides play the engine at depth 6.

Starts: randomised, from a fixed set of material preconditions (rook up, two rooks up, queen up, rook+minor up, two
minors up, and the same with the strong side to move or not), with the pieces placed on pseudo-random legal squares
seeded by SEED. A start is used only if it is legal and not already game over.
"""
import hashlib
import os
import random
import subprocess
import sys

import chess

N = int(sys.argv[1])
OUT = sys.argv[2]
SEED = int(os.environ.get("EG_SEED", "301"))
EXE = os.environ.get("EG_EXE", "/home/ubuntu/build-pc/forge")
DEPTH = int(os.environ.get("EG_DEPTH", "6"))
rawdir = OUT + ".raw"
os.makedirs(rawdir, exist_ok=True)
rng = random.Random(SEED)

S14 = [("Threads", "1"), ("Hash", "16"), ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"),
       ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"),
       ("NullMoveBase", "5"), ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"),
       ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"),
       ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("OwnBook", "false")]

# (strong side extra material) -> list of piece types
EXTRA_SETS = [
    [chess.ROOK],
    [chess.ROOK, chess.ROOK],
    [chess.QUEEN],
    [chess.ROOK, chess.KNIGHT],
    [chess.ROOK, chess.BISHOP],
    [chess.KNIGHT, chess.BISHOP],
]


def lone_side(b):
    for col in (chess.WHITE, chess.BLACK):
        if b.occupied_co[col] == int(b.pieces(chess.KING, col)):
            return col
    return None


def self_test():
    lone = chess.Board("8/8/8/8/8/5n2/4K1k1/8 w - - 0 60")
    both = chess.Board("8/8/8/8/8/5n2/4K1k1/4N3 b - - 11 60")
    full = chess.Board()
    got = (lone_side(lone), lone_side(both), lone_side(full))
    ok = got[0] is not None and got[1] is None and got[2] is None
    print(f"self_test: lone -> {got[0]}, K+N vs K+N -> {got[1]}, full -> {got[2]}, pass={ok}")
    if not ok:
        raise SystemExit("FAIL: lone_side broken; refusing to generate a meaningless set")


def start_position():
    """strong side has king + the extra pieces; weak side has king + a few pawns and one minor sometimes."""
    b = chess.Board(None)
    squares = list(chess.SQUARES)
    rng.shuffle(squares)
    used = []

    def place(piece, forbid_rank1_8_pawn=True, pawn=False):
        while squares:
            sq = squares.pop()
            r = chess.square_rank(sq)
            if pawn and (r in (0, 7)):
                continue
            b.set_piece_at(sq, piece)
            used.append(sq)
            return sq
        raise RuntimeError("ran out of squares")

    strong = rng.choice((chess.WHITE, chess.BLACK))
    weak = not strong
    place(chess.Piece(chess.KING, strong))
    place(chess.Piece(chess.KING, weak))
    for pt in rng.choice(EXTRA_SETS):
        place(chess.Piece(pt, strong))
    # weak side gets a little material so it is not a bare king from move one
    for _ in range(rng.randint(1, 4)):
        place(chess.Piece(chess.PAWN, weak), pawn=True)
    if rng.random() < 0.5:
        place(chess.Piece(rng.choice((chess.KNIGHT, chess.BISHOP)), weak))
    b.turn = rng.choice((chess.WHITE, chess.BLACK))
    b.clear_stack()
    return b


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


self_test()
cands, seen = [], set()
game = 0
while len(cands) < N and game < N * 30:
    game += 1
    b = start_position()
    if b.status() != chess.STATUS_VALID or b.is_game_over(claim_draw=False):
        continue
    # the strong side should convert; record the first position where the WEAK side is lone
    weak = None
    for _ in range(2):
        b2 = b.copy()
        # determine weak side as the one with less material
        def mat(col):
            v = 0
            for pt in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
                v += len(b2.pieces(pt, col)) * {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                                                chess.ROOK: 5, chess.QUEEN: 9}[pt]
            return v
        weak = chess.WHITE if mat(chess.WHITE) < mat(chess.BLACK) else chess.BLACK
        break
    ply = 0
    while ply < 200:
        if b.is_game_over(claim_draw=False):
            break
        if len([c for c in (chess.WHITE, chess.BLACK) if b.occupied_co[c] == int(b.pieces(chess.KING, c))]) == 0:
            pass
        ls = lone_side(b)
        if ls is not None and ply >= 4:
            fen = b.fen()
            h = hashlib.sha1(fen.encode()).hexdigest()[:10]
            if h not in seen:
                seen.add(h)
                cands.append((fen, "white" if ls == chess.WHITE else "black", game, ply))
            break
        fen = b.fen()
        h = hashlib.sha1(fen.encode()).hexdigest()[:12]
        mv = bestmove(fen, f"g{game:03d}_p{ply:03d}_{h}")
        if mv == "0000" or mv not in [m.uci() for m in b.legal_moves]:
            break
        b.push_uci(mv)
        ply += 1
    if game % 5 == 0:
        print(f"game {game}, candidates {len(cands)}", flush=True)

with open(OUT, "w") as f:
    for fen, side, g, ply in cands:
        f.write(f"{fen}\t{side}\tgame {g} ply {ply}\n")
print(f"wrote {len(cands)} lone-king endings from {game} games to {OUT}")
