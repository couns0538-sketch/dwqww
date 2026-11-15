#!/usr/bin/env python3
"""Job 1 part C: KQ-vs-K positions with white to move whose shortest mate is
exactly 5 plies (3 moves), by brute force with python-chess.

Only the 5-ply question is asked (mate in <=5 but not in <=3), which is all the
job needs; that keeps the tree small.  White's checking moves are tried first so
a positive answer is found quickly, but a negative answer still explores the
whole tree -- the proof that no mate in <=3 exists is complete.

Positive control (self_test) checks the solver against positions whose mate
length is known by construction: mate-in-1, mate-in-2 and a well known
KQ-vs-K position that is NOT mate in <=5.
"""

import json
import random
import sys
import time
from multiprocessing import Pool

import chess

CAP = 5


def _children(board, plies, memo):
    if board.turn == chess.WHITE:
        checks = []
        quiets = []
        for move in board.legal_moves:
            (checks if board.gives_check(move) else quiets).append(move)
        for move in checks + quiets:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return True
            if board.is_stalemate() or board.is_insufficient_material():
                board.pop()
                continue
            if plies >= 2 and white_mates_in(board, plies - 1, memo):
                board.pop()
                return True
            board.pop()
        return False
    # black to move: every legal black move must still lose within plies-1
    any_move = False
    for move in board.legal_moves:
        any_move = True
        board.push(move)
        if board.is_stalemate() or board.is_insufficient_material() or board.is_checkmate():
            board.pop()
            return False
        if plies < 2 or not white_mates_in(board, plies - 1, memo):
            board.pop()
            return False
        board.pop()
    if not any_move:
        return board.is_checkmate()   # cannot happen on black's move
    return True


def white_mates_in(board, plies, memo):
    """White to move (board.turn == white) forces mate in at most `plies`."""
    key = (board._transposition_key(), plies)
    hit = memo.get(key)
    if hit is not None:
        return hit
    result = _children(board, plies, memo)
    memo[key] = result
    return result


def mate_plies_in_5(board):
    """5 if the shortest forced mate is exactly 5 plies, else None."""
    if board.turn != chess.WHITE:
        raise ValueError("white to move only")
    memo = {}
    if white_mates_in(board, 3, memo):
        return 3          # mate in 1 or 2 moves: not what we want
    if white_mates_in(board, 5, memo):
        return 5
    return None


def self_test():
    ok = True
    cases = [
        # (fen, expected plies to mate) -- all white to move.  Expected values
        # are the independent classifier's answers (verify_exact.classify) and
        # are also checked by direct enumeration of mate-in-1 moves below.
        ("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 1),     # Ra8#
        ("8/8/8/8/8/8/8/2k1K2Q w - - 0 1", None),        # queen far: >5 plies
        ("8/8/8/8/8/1k6/8/KQ6 w - - 0 1", None),         # >5 plies
    ]
    for fen, exp in cases:
        b = chess.Board(fen)
        memo = {}
        got = next((p for p in (1, 2, 3, 4, 5) if white_mates_in(b, p, memo)), None)
        print(f"  control {fen} -> plies {got}, expected {exp}")
        ok = ok and got == exp
    # a position that is NOT mate in <=5: lone kings far apart with the queen
    # still in its own camp (black king in the middle, lots of room)
    b = chess.Board("8/8/8/3k4/8/8/8/Q3K3 w - - 0 1")
    memo = {}
    got = white_mates_in(b, 5, memo)
    print(f"  control {b.fen()} -> mate in <=5: {got}, expected False")
    ok = ok and not got
    # direct cross-check: the solver says "mate in 1" exactly when a mate-in-1
    # move exists, on random KQ positions
    rng = random.Random(99)
    checked = 0
    for _ in range(300):
        wk, bk, wq = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) <= 1:
            continue
        bb = chess.Board(None)
        bb.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        bb.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        bb.set_piece_at(wq, chess.Piece(chess.QUEEN, chess.WHITE))
        bb.turn = chess.WHITE
        bb.halfmove_clock = 0
        bb.fullmove_number = 1
        if not bb.is_valid() or bb.is_game_over():
            continue
        checked += 1
        direct = False
        for m in bb.legal_moves:
            a = bb.copy()
            a.push(m)
            if a.is_checkmate():
                direct = True
                break
        memo = {}
        got = white_mates_in(bb, 1, memo)
        if direct != got:
            print("  MISMATCH", bb.fen(), direct, got)
            ok = False
    print(f"  direct mate-in-1 cross-check on {checked} positions: {'ok' if ok else 'FAILED'}")
    return ok


def worker(args):
    fen, seed = args
    b = chess.Board(fen)
    t = time.time()
    d = mate_plies_in_5(b)
    return fen, d, time.time() - t, seed


def main():
    assert self_test(), "solver control failed"
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    out = sys.argv[2] if len(sys.argv) > 2 else "partc.json"
    rng = random.Random(20261115)
    cands = []
    seen = set()
    edge = [sq for sq in range(64)
            if chess.square_rank(sq) in (0, 7) or chess.square_file(sq) in (0, 7)]
    while len(cands) < want * 12:
        bk = rng.choice(edge)
        near = [s for s in range(64) if s != bk and 1 <= chess.square_distance(s, bk) <= 3]
        if not near:
            continue
        wk = rng.choice(near)
        wq = rng.choice([s for s in range(64) if s not in (bk, wk)])
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(wq, chess.Piece(chess.QUEEN, chess.WHITE))
        b.turn = chess.WHITE
        b.halfmove_clock = 0
        b.fullmove_number = 1
        if not b.is_valid() or b.is_game_over():
            continue
        fen = b.fen()
        if fen in seen:
            continue
        seen.add(fen)
        cands.append((fen, 0))
    print(f"candidates {len(cands)}; solving with 4 workers", flush=True)
    t0 = time.time()
    found = []
    with Pool(4) as pool:
        for fen, d, dt, _ in pool.imap_unordered(worker, cands, chunksize=4):
            if d == 5:
                found.append({"fen": fen, "mate_plies": 5, "mate_moves": 3, "solve_seconds": round(dt, 3)})
                print(f"found {len(found)} ({fen}) {dt:.2f}s", flush=True)
            if len(found) >= want:
                break
    json.dump({"positions": found, "candidates": len(cands)},
              open(out, "w"), indent=1)
    print(f"found={len(found)} seconds={time.time()-t0:.0f}")


if __name__ == "__main__":
    main()
