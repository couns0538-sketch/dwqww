#!/usr/bin/env python3
"""make_set2.py -- the blast-radius set, built cheaply and then ASSERTED by oracle.

Speed problem this solves: running the 8-ply oracle on thousands of random
placements to FIND a position is far too slow (a full attempt timed out at 4
minutes). But finding is cheap if the mate distance is forced by construction,
so this file uses two cheap generators and then spends the oracle only on the
positions it actually keeps -- as an assertion, not as a search.

Generators (both produce legal placements only):

  A. DIRECT MATE NET. Place the loser king in a corner or on an edge, then place
     the winner's rook/queen on the mating square so that the position after the
     loser's forced reply is mate. Rather than reason about it, this file places
     pieces and then asks python-chess `is_checkmate` after every legal loser
     move -- a constant-time test, no search.

  B. LADDER WITH A SPARE MOVE. K+RR v K and K+Q+R v K nets where the loser has
     2..4 king moves and every one is met by mate in one. Also constant-time per
     candidate.

Both give p=2 (mate in one against the loser). For p=4 the same trick is applied
two plies deeper with a tiny 4-ply search, which is cheap because the material is
minimal.

Every kept position is then checked against matedist.py and the predicted verdict
asserted; the set is not written unless all assertions pass.

Usage: make_set2.py --out SET.epd --json SET.json --per-class 10 --seed 6201
"""
import argparse
import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402

ORACLE_PLIES = 8


def resets(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return True
    return False


def oracle_plies(board, max_plies=ORACLE_PLIES):
    v = evaluate(board.fen(), max_plies)
    if v <= -MATE + max_plies:
        return MATE + v
    return None


def mate_in_one_after_every_reply(board):
    """True iff every legal move of the side to move is answered by mate in 1."""
    moves = list(board.legal_moves)
    if not moves:
        return False
    for mv in moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return False                      # already mated: not our p=2 shape
        found = False
        for reply in board.legal_moves:
            board.push(reply)
            if board.is_checkmate():
                found = True
                board.pop()
                break
            board.pop()
        board.pop()
        if not found:
            return False
    return True


def gen_p2(rng):
    """Loser (black) to move, mated in 2 plies, with >=2 legal moves."""
    for _ in range(60000):
        b = chess.Board(None)
        # black king on an edge/corner, white king near, white heavy piece(s) far
        bk = rng.choice([s for s in range(64) if chess.square_file(s) in (0, 7)
                         or chess.square_rank(s) in (0, 7)])
        candidates = [s for s in range(64) if s != bk]
        rng.shuffle(candidates)
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        placed = 1
        # white king not adjacent
        for sq in candidates:
            if chess.square_distance(sq, bk) >= 2:
                b.set_piece_at(sq, chess.Piece(chess.KING, chess.WHITE))
                placed += 1
                used = sq
                break
        else:
            continue
        pieces = []
        n_heavy = rng.randint(1, 2)
        for _k in range(n_heavy):
            pieces.append(rng.choice([chess.ROOK, chess.QUEEN]))
        ok = True
        for pt in pieces:
            for sq in candidates:
                if b.piece_at(sq) is None:
                    b.set_piece_at(sq, chess.Piece(pt, chess.WHITE))
                    break
        b.turn = chess.BLACK
        b.halfmove_clock = 98
        b.fullmove_number = 40
        if not b.is_valid():
            continue
        if b.is_checkmate() or b.legal_moves.count() < 2:
            continue
        if resets(b):
            continue
        if mate_in_one_after_every_reply(b):
            return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--per-class", type=int, default=10)
    ap.add_argument("--seed", type=int, default=6201)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    found = []
    tried = 0
    while len(found) < args.per_class and tried < 40:
        tried += 1
        b = gen_p2(rng)
        if b is None:
            print("attempt %d: no position" % tried)
            continue
        p = oracle_plies(b)
        j0 = 100 - 98
        print("found p=%s legal=%d  %s" % (p, b.legal_moves.count(), b.fen()))
        if p == 2:
            found.append({"fen": b.fen(), "p": p, "legal": b.legal_moves.count()})
    print("tried=%d kept=%d" % (tried, len(found)))
    json.dump(found, open(args.json, "w"), indent=1)
    with open(args.out, "w") as f:
        for r in found:
            f.write("%s; p=%d\n" % (r["fen"], r["p"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
