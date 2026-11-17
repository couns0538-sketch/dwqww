"""Extract the (position, book move) pairs the games actually played.

Q3 must judge the moves the book REALLY played in games, not the move a single
deterministic probe returns, because the book RNG makes those two different at
`Book Variety 30` (see q0_rng.py). This writes the pair list that
`q3_book_vs_search.py --played` consumes.

Output: JSON list of {"fen": ..., "move": ...}, deduplicated, in first-seen order.
"""

from __future__ import annotations

import argparse
import json
import sys

import chess


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    games = json.load(open(args.games))
    pairs: list[tuple[str, str]] = []
    for g in games:
        board = chess.Board()
        for i, uci in enumerate(g["moves"]):
            if i >= g["book_plies"]:
                break
            if g["book_flags"][i] == 1:
                pairs.append((board.fen(), uci))
            board.push_uci(uci)

    unique = list(dict.fromkeys(pairs))
    out = [{"fen": fen, "move": mv} for fen, mv in unique]
    json.dump(out, open(args.out, "w"), indent=0)
    print(f"{len(pairs)} book move instances from {len(games)} games -> "
          f"{len(unique)} distinct (position, move) pairs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
