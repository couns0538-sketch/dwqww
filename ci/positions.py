"""Seeded random chess positions for the Fable/Opus checks (Opus session, 2026-11-15).

The same method as the two helper trials of 2026-11-15, whose two independently written scripts produced the very
same 500 positions for seed 20261115 and 8 to 60 plies: a seeded random.Random; for every playout a ply count drawn
with randint(min, max); that many uniformly random legal moves (python-chess's move order) from the start position;
a playout in which the game ends early is thrown away and the next one starts from the same random stream.

    python positions.py <seed> <min plies> <max plies> <count> <out file>
"""
from __future__ import annotations

import random
import sys

import chess


def generate(seed: int, min_plies: int, max_plies: int, count: int) -> tuple[list[str], int]:
    rng = random.Random(seed)
    out: list[str] = []
    attempts = 0
    while len(out) < count:
        attempts += 1
        board = chess.Board()
        plies = rng.randint(min_plies, max_plies)
        ok = True
        for _ in range(plies):
            moves = list(board.legal_moves)
            if not moves:
                ok = False
                break
            board.push(rng.choice(moves))
            if board.is_game_over():
                ok = False
                break
        if ok and not board.is_game_over():
            out.append(board.fen())
    return out, attempts


def features(fen: str) -> dict[str, bool]:
    """What a position offers the move generator: a legal en passant capture, a legal promotion, a legal castling
    move, the side to move in check."""
    b = chess.Board(fen)
    moves = list(b.legal_moves)
    return {"en_passant": any(b.is_en_passant(m) for m in moves),
            "promotion": any(m.promotion for m in moves),
            "castling": any(b.is_castling(m) for m in moves),
            "check": b.is_check()}


def main() -> int:
    seed, lo, hi, count, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    fens, attempts = generate(seed, lo, hi, count)
    with open(out, "w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(fens) + "\n")
    print(f"wrote {len(fens)} positions (seed {seed}, plies {lo}..{hi}, {attempts} playouts) to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
