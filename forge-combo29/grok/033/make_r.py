#!/usr/bin/env python3
"""Random legal games. Keep a FEN every 7 plies from ply 8. Drop games that end."""
import random
import sys
from pathlib import Path

import chess


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: make_r.py SEED COUNT OUT", file=sys.stderr)
        return 2
    seed = int(sys.argv[1])
    count = int(sys.argv[2])
    out = Path(sys.argv[3])
    rng = random.Random(seed)
    wanted = list(range(8, 80, 7))
    fens: list[str] = []
    games = 0
    dropped = 0
    while len(fens) < count:
        games += 1
        board = chess.Board()
        taken: list[str] = []
        ended = False
        for ply in range(1, wanted[-1] + 1):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(moves))
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            if ply in wanted:
                taken.append(board.fen())
        if ended or len(taken) != len(wanted):
            dropped += 1
            continue
        fens.extend(taken)
    fens = fens[:count]
    out.write_text("\n".join(fens) + "\n", encoding="utf-8")
    print(f"games_started={games} dropped={dropped} kept={count} file={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
