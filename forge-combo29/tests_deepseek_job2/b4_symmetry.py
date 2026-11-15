#!/usr/bin/env python3
"""Job 2 B4: colour symmetry, engine only.

For every position, build its colour-swapped copy and check that the engine's eval
is the same for both:
  * the board is flipped top to bottom (rank r -> rank 7-r) and colours exchange,
  * the side to move exchanges,
  * castling rights exchange (KQ <-> kq),
  * an en passant square, if any, is flipped with the board.

The engine here is the real one (optimised build, v3 net active), asked one `eval`
per position. Comparison is exact integers.

Usage: b4_symmetry.py <net> <fens> <outdir>
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b2_compare import engine_values


def swap_colours(fen):
    """The colour-swapped copy of a FEN: ranks mirrored, colours exchanged, stm exchanged."""
    board = chess.Board(fen)
    mirrored = board.mirror()
    return mirrored.fen()


def main():
    net, fens_path, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    with open(fens_path) as f:
        fens = [l.strip() for l in f if l.strip()]
    swapped = [swap_colours(fen) for fen in fens]

    # One engine process, both lists through it, so the net is loaded once.
    both = fens + swapped
    values, _raw, code = engine_values("/tmp/ds/build-release/forge", net, both)
    if len(values) != 2 * len(fens):
        raise SystemExit(f"engine returned {len(values)} for {2 * len(fens)} evals")
    original = values[:len(fens)]
    copy_vals = values[len(fens):]

    diffs = []
    for i in range(len(fens)):
        if original[i] != copy_vals[i]:
            diffs.append({"index": i, "fen": fens[i], "swapped_fen": swapped[i],
                          "eval_original": original[i], "eval_swapped": copy_vals[i],
                          "difference": original[i] - copy_vals[i]})

    # The smallest example: fewest pieces, then shortest FEN.
    smallest = None
    if diffs:
        def pieces(fen):
            return len(chess.Board(fen).piece_map())
        smallest = sorted(diffs, key=lambda d: (pieces(d["fen"]), len(d["fen"])))[0]

    result = {"net": net, "positions": len(fens), "engine_exit_code": code,
              "differences": len(diffs), "smallest_example": smallest,
              "first_differences": diffs[:10]}
    with open(f"{outdir}/B4-symmetry.json", "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    with open(f"{outdir}/B4-symmetry.values.txt", "w") as f:
        f.write("# index  original swapped\n")
        for i in range(len(fens)):
            f.write(f"{i} {original[i]} {copy_vals[i]}\n")
    print(json.dumps({k: v for k, v in result.items() if k != "first_differences"}, sort_keys=True))


if __name__ == "__main__":
    main()
