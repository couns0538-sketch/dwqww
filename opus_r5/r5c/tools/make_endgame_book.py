#!/usr/bin/env python3
"""R5C M2: a small endgame-heavy opening book for the N3 smoke.

Source: tests/data/nnue_selfplay_sample_916.txt (916 Forge self-play positions, the lock archive's 5_nnue
forge_text_sample format: `fen | score | result`). Kept: 6 to 9 pieces including the kings (one or two captures from
the 3-4-5 tablebases), no castling rights, side to move not in check, game not over; sorted by |score| (most balanced
first, ties by file order) and the first --count written as EPD lines `fen ; c0 "<source line> score <cp>"`.
usage: make_endgame_book.py <sample.txt> <out.epd> [--count 100]
"""
import argparse

import chess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sample")
    ap.add_argument("out")
    ap.add_argument("--count", type=int, default=100)
    a = ap.parse_args()
    rows = []
    for number, line in enumerate(open(a.sample, encoding="utf-8"), start=1):
        parts = [p.strip() for p in line.split("|")]
        if not parts[0]:
            continue
        board = chess.Board(parts[0])
        pieces = len(board.piece_map())
        if not 6 <= pieces <= 9 or board.has_castling_rights(chess.WHITE) or board.has_castling_rights(chess.BLACK):
            continue
        if board.is_check() or board.is_game_over():
            continue
        score = int(parts[1]) if len(parts) > 1 and parts[1].lstrip("-").isdigit() else 0
        rows.append((abs(score), number, board.fen(), score, pieces))
    rows.sort()
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# R5C N3 endgame book: 6-9 pieces, no castling, not in check; from tests/data/nnue_selfplay_sample_916.txt\n")
        f.write(f"# {min(a.count, len(rows))} of {len(rows)} qualifying positions, most balanced first (make_endgame_book.py)\n")
        for _, number, fen, score, pieces in rows[: a.count]:
            f.write(f'{fen} ; c0 "sample line {number} score {score} pieces {pieces}"\n')
    print(f"{len(rows)} qualifying positions, {min(a.count, len(rows))} written to {a.out}")


if __name__ == "__main__":
    main()
