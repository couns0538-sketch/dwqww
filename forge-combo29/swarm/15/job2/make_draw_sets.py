#!/usr/bin/env python3
"""make_draw_sets.py OUTDIR SEED

Builds the six position sets of area 5 job 2 from scratch with python-chess, deterministically
from SEED:
  kvk_20.fens    20 legal K v K positions, legal to build and legal to play
  knk_20.fens    KN v K
  kbk_20.fens    KB v K
  knnk_20.fens   KNN v K
  rep_20.ucimoves  20 move lists that reach a THREE-fold repetition (verified with python-chess)
  fifty_20.fens  20 positions whose halfmove clock is at 99

Every set is validated with python-chess before it is written; a set that does not validate
raises and writes nothing.
"""
import os
import random
import sys

import chess


def rand_square(rng, avoid=()):
    while True:
        s = rng.randrange(64)
        if s not in avoid and chess.square_rank(s) in (0, 7):
            continue  # keep pieces off the back ranks so files stay sane
        if s not in avoid:
            return s


def place_kings(rng):
    while True:
        wk, bk = rng.randrange(64), rng.randrange(64)
        if wk == bk:
            continue
        if max(abs(chess.square_file(wk) - chess.square_file(bk)),
               abs(chess.square_rank(wk) - chess.square_rank(bk))) < 1:
            continue
        return wk, bk


def build(kind, rng, tries=4000):
    """Build a legal position of the requested material. Returns a FEN or None."""
    wk, bk = place_kings(rng)
    board = chess.Board(None)
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    square_pool = [s for s in range(64) if s not in (wk, bk)]
    rng.shuffle(square_pool)
    if kind == "knk":
        board.set_piece_at(square_pool.pop(), chess.Piece(chess.KNIGHT, chess.WHITE))
    elif kind == "kbk":
        board.set_piece_at(square_pool.pop(), chess.Piece(chess.BISHOP, chess.WHITE))
    elif kind == "knnk":
        a, b = square_pool.pop(), square_pool.pop()
        board.set_piece_at(a, chess.Piece(chess.KNIGHT, chess.WHITE))
        board.set_piece_at(b, chess.Piece(chess.KNIGHT, chess.WHITE))
    board.castling_rights = chess.BB_EMPTY
    board.ep_square = None
    board.halfmove_clock = 0
    board.fullmove_number = 1
    # the side NOT to move must not be in check, so try both colours to move
    for turn in (chess.WHITE, chess.BLACK):
        board.turn = turn
        if not board.is_valid():
            continue
        # the opponent (not to move) must not be in check
        probe = board.copy()
        probe.turn = not turn
        if probe.is_check():
            continue
        return board.fen()
    return None


def make_set(kind, n, rng, outdir):
    got = []
    guard = 0
    while len(got) < n and guard < 200000:
        guard += 1
        fen = build(kind, rng)
        if fen and fen not in got:
            got.append(fen)
    if len(got) < n:
        raise SystemExit("could not build %d %s positions (got %d)" % (n, kind, len(got)))
    path = os.path.join(outdir, "%s_%d.fens" % (kind, n))
    with open(path, "w", encoding="utf-8") as fh:
        for f in got:
            b = chess.Board(f)
            assert b.is_valid()
            fh.write(f + "\n")
    return path, got



def poskey(b):
    """Position identity without the halfmove clock / fullmove counter."""
    return (b.board_fen(), b.turn, b.castling_xfen(), b.ep_square)


def make_repetition_set(n, rng, outdir):
    """Move lists from startpos that reach a position three times. Verified by python-chess.

    Structure: a varied quiet opening (0, 2, 4 or 6 plies) followed by the 4-ply knight
    shuffle g1f3 g8f6 f3g1 f6g8 played twice, which returns to the same position, so the
    position after the opening occurs three times (before, after cycle 1, after cycle 2).
    """
    cycle = ["g1f3", "g8f6", "f3g1", "f6g8"]
    lines = []
    seen_lines = set()
    guard = 0
    while len(lines) < n and guard < 20000:
        guard += 1
        board = chess.Board()
        moves = []
        # varied quiet opening of an even number of plies, so white is to move again
        for _ in range(rng.choice([0, 0, 2, 2, 4, 6])):
            # single pawn pushes only: they keep castling rights and never set an ep square
            quiet = [m for m in board.legal_moves
                     if board.piece_type_at(m.from_square) == chess.PAWN
                     and not board.is_capture(m) and not m.promotion
                     and abs(chess.square_rank(m.to_square) - chess.square_rank(m.from_square)) == 1
                     and chess.square_rank(m.to_square) not in (0, 7)]
            if not quiet:
                break
            mv = rng.choice(quiet)
            board.push(mv)
            moves.append(mv.uci())
        if len(moves) % 2:
            continue
        start_key = poskey(board)
        counts = {start_key: 1}
        ok = True
        for _ in range(2):
            for uci in cycle:
                mv = chess.Move.from_uci(uci)
                if mv not in board.legal_moves:
                    ok = False
                    break
                board.push(mv)
                moves.append(uci)
                k = poskey(board)
                counts[k] = counts.get(k, 0) + 1
            if not ok:
                break
        if not ok:
            continue
        # verify with python-chess that a position really occurred three times
        rep3 = max(counts.values()) >= 3
        if not rep3:
            continue
        line = " ".join(moves)
        if line in seen_lines:
            continue
        seen_lines.add(line)
        lines.append(line)
    if len(lines) < n:
        raise SystemExit("only %d repetition lines verified" % len(lines))
    path = os.path.join(outdir, "rep_%d.ucimoves" % n)
    with open(path, "w", encoding="utf-8") as fh:
        for l in lines[:n]:
            fh.write(l + "\n")
    return path, lines[:n]


def make_fifty_set(n, rng, outdir):
    """Positions with the halfmove clock at 99: a normal middlegame/endgame, quiet last move."""
    got = []
    guard = 0
    while len(got) < n and guard < 400000:
        guard += 1
        b = chess.Board()
        # play a handful of quiet random moves, then set the clock to 99
        for _ in range(rng.randrange(6, 14)):
            caps = [m for m in b.legal_moves if b.is_capture(m) or b.gives_check(m)]
            quiet = [m for m in b.legal_moves if m not in caps]
            if not quiet:
                break
            b.push(rng.choice(quiet))
        if b.is_game_over() or not b.is_valid():
            continue
        b.halfmove_clock = 99
        if not b.is_valid():
            continue
        f = b.fen()
        if f not in got:
            got.append(f)
    if len(got) < n:
        raise SystemExit("could not build %d fifty-move positions" % n)
    path = os.path.join(outdir, "fifty_%d.fens" % n)
    with open(path, "w", encoding="utf-8") as fh:
        for f in got:
            assert chess.Board(f).is_valid()
            fh.write(f + "\n")
    return path, got


def main():
    outdir = sys.argv[1]
    seed = int(sys.argv[2])
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(seed)
    made = []
    for kind in ("kvk", "knk", "kbk", "knnk"):
        p, g = make_set(kind, 20, rng, outdir)
        made.append((p, len(g)))
    p, g = make_repetition_set(20, rng, outdir)
    made.append((p, len(g)))
    p, g = make_fifty_set(20, rng, outdir)
    made.append((p, len(g)))
    for p, n in made:
        print("%-28s %d lines" % (os.path.basename(p), n))


if __name__ == "__main__":
    main()
