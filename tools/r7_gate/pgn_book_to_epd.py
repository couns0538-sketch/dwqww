"""R7 J4: turn a PGN opening book into an EPD book (the position after each game's moves), python-chess.
usage: python -I -B pgn_book_to_epd.py <book.pgn> <out.epd>
The EPD keeps only the final position: the book moves' history (repetition context) is lost, so an EPD gate is
not identical to a PGN gate; this file is only for the loading-time comparison. Refuses to overwrite."""
import sys

import chess.pgn

src, dst = sys.argv[1], sys.argv[2]
n = 0
with open(src, encoding="utf-8", errors="replace") as f, open(dst, "x", encoding="utf-8", newline="\n") as out:
    while True:
        game = chess.pgn.read_game(f)
        if game is None:
            break
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
        out.write(board.epd() + "\n")
        n += 1
print(f"wrote {n} positions to {dst}")
