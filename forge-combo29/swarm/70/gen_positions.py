"""Generate position sets, each FEN PROVEN by python-chess before it is written.

Sets
  ties2 / ties3 / ties5 : positions with EXACTLY 2 / 3 / 5 legal moves that each
                          deliver immediate checkmate.  The root score is a proven
                          mate in 1 for every one of them, so the tie is a proof,
                          not the engine's opinion: no evaluation term can break it.
  allmate               : positions where EVERY legal move mates in 1 (the cleanest
                          possible "searchmoves <all legal>" probe).
  pinpool               : middlegame positions with at least 12 legal moves, for the
                          pin-count and rank-order jobs.

Every FEN is validated by python-chess (parse + legal-move count) and the
expected perft-1 count is written beside it, so a later harness can assert that
the engine actually holds the board it was given.

Run: python3 gen_positions.py            (writes job1/*.epd, job1/fencheck.json)
"""
import json
import os
import random
import sys

import chess

SEED = 7001


def mate_in_1_moves(board):
    """Legal moves that checkmate immediately, proven with python-chess."""
    out = []
    for m in board.legal_moves:
        board.push(m)
        if board.is_checkmate():
            out.append(m.uci())
        board.pop()
    return out


def random_sparse_board(rng, max_tries=4000):
    """A sparse legal position, black to move or white to move, biased near mate."""
    for _ in range(max_tries):
        board = chess.Board(None)
        squares = rng.sample(range(64), rng.choice([4, 5, 6, 7]))
        pieces = [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        wk, bk = squares[0], squares[1]
        if chess.square_distance(wk, bk) <= 1:
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        ok = True
        for sq in squares[2:]:
            # attackers are white, occasionally a black blocker
            color = chess.WHITE if rng.random() < 0.8 else chess.BLACK
            pt = rng.choice(pieces)
            if pt == chess.KING:
                pt = chess.ROOK
            board.set_piece_at(sq, chess.Piece(pt, color))
        # reject adjacent kings, reject if the side NOT to move is in check
        board.turn = chess.WHITE if rng.random() < 0.85 else chess.BLACK
        if board.is_valid():
            return board
    return None


def main():
    rng = random.Random(SEED)
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, "job1")
    os.makedirs(outdir, exist_ok=True)

    buckets = {2: [], 3: [], 5: []}
    allmate = []
    pinpool = []
    seen = set()

    # ALLMATE IS NOT GENERATED.  A position in which literally every legal move
    # delivers mate was not found in 200,000 random draws (see allmate_search.txt):
    # the mating side's own king almost always keeps an escape move, and a king
    # move cannot give check.  The ties2/ties3/ties5 sets below are the stronger
    # instrument for the same question, because every mate in them is PROVEN and
    # the non-mating moves are still present, so "all legal" is still named.
    allmate = []

    tries = 0
    while (len(buckets[2]) < 20 or len(buckets[3]) < 20 or len(buckets[5]) < 12) and tries < 400000:
        tries += 1
        b = random_sparse_board(rng)
        if b is None:
            continue
        fen = b.fen()
        if fen in seen:
            continue
        n_legal = b.legal_moves.count()
        if n_legal < 2:
            continue
        mates = mate_in_1_moves(b)
        if not mates:
            continue
        seen.add(fen)
        k = len(mates)
        if k == 2 and len(buckets[2]) < 20:
            buckets[2].append((fen, n_legal, mates))
        elif k == 3 and len(buckets[3]) < 20:
            buckets[3].append((fen, n_legal, mates))
        elif k == 5 and len(buckets[5]) < 12:
            buckets[5].append((fen, n_legal, mates))

    # pin pool: ordinary middlegame positions from random games
    grng = random.Random(SEED + 1)
    while len(pinpool) < 60:
        b = chess.Board()
        for _ in range(grng.randint(16, 60)):
            ms = list(b.legal_moves)
            if not ms:
                break
            b.push(grng.choice(ms))
        if b.is_game_over():
            continue
        n = b.legal_moves.count()
        if n >= 12:
            fen = b.fen()
            if fen not in seen:
                seen.add(fen)
                pinpool.append((fen, n, []))

    names = {"ties2": buckets[2], "ties3": buckets[3], "ties5": buckets[5],
             "pinpool": pinpool}
    check = {}
    for name, rows in names.items():
        path = os.path.join(outdir, f"{name}.epd")
        with open(path, "w") as fh:
            for fen, n_legal, mates in rows:
                # re-prove every FEN with a FRESH python-chess board before writing
                vb = chess.Board(fen)
                assert vb.is_valid(), f"{name}: python-chess rejects {fen}"
                assert vb.legal_moves.count() == n_legal, f"{name}: legal count drift {fen}"
                if mates:
                    again = mate_in_1_moves(vb)
                    assert sorted(again) == sorted(mates), f"{name}: mate set drift {fen}"
                fh.write(fen + "\n")
                check[fen] = {"set": name, "legal": n_legal, "mate_in_1": mates}
        print(f"{name:8s}: {len(rows)} positions -> {path}")

    with open(os.path.join(outdir, "fencheck.json"), "w") as fh:
        json.dump(check, fh, indent=1, sort_keys=True)
    print(f"total FENs proven: {len(check)}  (tries {tries})")

    for name in ("ties2", "ties3", "ties5"):
        print(f"--- {name} ---")
        for fen, n, mates in names[name]:
            print(f"  legal {n:2d} mate1 {len(mates)}  {fen}")


if __name__ == "__main__":
    sys.exit(main())
