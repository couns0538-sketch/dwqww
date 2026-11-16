#!/usr/bin/env python3
"""make_positions.py -- builds the job2 position sets with random.Random(501). Text only.
Writes to positions/:
  KvK.epd KNvK.epd KBvK.epd KNNvK.epd      (20 each, one FEN per line)
  fifty99.epd fifty98.epd fifty0.epd        (the same 20 boards, the three counters; K+Q / K+R so a win exists)
  threefold_moves.txt                       (20 lines: a move list whose final position occurred 3 times)
  threefold_meta.txt                        (per line: whether the repeated position is a dead draw)
"""
import os
import random

import chess

R = random.Random(501)
OUT = "positions"
os.makedirs(OUT, exist_ok=True)

FILES = chess.SQUARES


def free_squares(exclude):
    return [s for s in chess.SQUARES if s not in exclude]


def place_ok(b):
    """basic sanity: python-chess says the position is legal, not terminal, and the side not to move is not in check"""
    if not b.is_valid():
        return False
    if b.is_checkmate() or b.is_stalemate():
        return False
    if b.is_insufficient_material() and False:
        return False
    return True


def make_bare(kind, n=20):
    """kind: 'KvK','KNvK','KBvK','KNNvK' -- both kings plus the named white pieces"""
    out = []
    tries = 0
    while len(out) < n and tries < 200000:
        tries += 1
        sq = R.sample(list(chess.SQUARES), 4)
        b = chess.Board(None)
        b.set_piece_at(sq[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sq[1], chess.Piece(chess.KING, chess.BLACK))
        if kind == "KvK":
            pass
        elif kind == "KNvK":
            b.set_piece_at(sq[2], chess.Piece(chess.KNIGHT, chess.WHITE))
        elif kind == "KBvK":
            b.set_piece_at(sq[2], chess.Piece(chess.BISHOP, chess.WHITE))
        elif kind == "KNNvK":
            b.set_piece_at(sq[2], chess.Piece(chess.KNIGHT, chess.WHITE))
            b.set_piece_at(sq[3], chess.Piece(chess.KNIGHT, chess.WHITE))
        b.turn = chess.WHITE
        b.halfmove_clock = 0
        b.fullmove_number = 1
        b.clear_stack()
        if not place_ok(b):
            continue
        # the side NOT to move (black) must not be in check
        if b.is_attacked_by(chess.WHITE, b.king(chess.BLACK)):
            continue
        b.castling_rights = chess.BB_EMPTY
        b.ep_square = None
        out.append(b.fen())
    return out


def make_fifty(n=20):
    """K+Q or K+R versus a lone king: a win exists, so the fifty-move counter is the only reason for cp 0"""
    out = []
    tries = 0
    while len(out) < n and tries < 200000:
        tries += 1
        sq = R.sample(list(chess.SQUARES), 3)
        b = chess.Board(None)
        b.set_piece_at(sq[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sq[1], chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(sq[2], chess.Piece(R.choice([chess.QUEEN, chess.ROOK]), chess.WHITE))
        b.turn = chess.WHITE
        b.castling_rights = chess.BB_EMPTY
        b.ep_square = None
        b.halfmove_clock = 0
        b.fullmove_number = 1
        b.clear_stack()
        if not b.is_valid() or b.is_checkmate() or b.is_stalemate():
            continue
        if b.is_attacked_by(chess.WHITE, b.king(chess.BLACK)) and False:
            continue
        if b.is_insufficient_material():
            continue
        # require that black is not already in check (white is to move, so black must not be in check)
        if b.is_attacked_by(chess.WHITE, b.king(chess.BLACK)):
            continue
        out.append(b)
    return out


def with_counter(fen_template, hm):
    b = chess.Board(fen_template)
    parts = b.fen().split()
    parts[4] = str(hm)
    return " ".join(parts)


def make_threefold(n=20):
    """random play until some position occurs 3 times, using a python-chess board with a stack"""
    made = []
    tries = 0
    while len(made) < n and tries < 20000:
        tries += 1
        b = chess.Board()
        moves = []
        seen = {}
        found = False
        for ply in range(300):
            key = b._transposition_key()
            seen[key] = seen.get(key, 0) + 1
            if seen[key] >= 3:
                found = True
                break
            legal = list(b.legal_moves)
            if not legal:
                break
            mv = R.choice(legal)
            b.push(mv)
            moves.append(mv.uci())
        if not found:
            continue
        # is the repeated position a dead draw?
        dead = b.is_insufficient_material() or b.is_stalemate()
        made.append((" ".join(moves), dead, b.fen()))
    return made


sets = {}
for kind in ("KvK", "KNvK", "KBvK", "KNNvK"):
    fens = make_bare(kind)
    sets[kind] = fens
    with open(f"{OUT}/{kind}.epd", "w") as f:
        for x in fens:
            f.write(x + "\n")

wins = make_fifty(20)
for name, hm in (("fifty0", 0), ("fifty98", 98), ("fifty99", 99)):
    with open(f"{OUT}/{name}.epd", "w") as f:
        for b in wins:
            f.write(with_counter(b.fen(), hm) + "\n")

three = make_threefold(20)
with open(f"{OUT}/threefold_moves.txt", "w") as f, open(f"{OUT}/threefold_meta.txt", "w") as m:
    for i, (mv, dead, fen) in enumerate(three):
        f.write(f"{i}\t{mv}\n")
        m.write(f"{i}\tdead_draw={dead}\tfen_after={fen}\n")

print("counts:")
for k, v in sets.items():
    print(f"  {k}: {len(v)}")
print(f"  fifty0/fifty98/fifty99: {len(wins)} each")
print(f"  threefold: {len(three)}  "
      f"(dead draws among them: {sum(1 for _, d, _ in three if d)})")
