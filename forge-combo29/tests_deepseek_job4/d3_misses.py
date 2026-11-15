#!/usr/bin/env python3
"""Job 4 D3: for each job-3 B1 miss, the true shortest line and the engine's report
at depths 12 and 18.

The true line is found by the corrected brute force in b_truth.py: pick the move with
mate_in(parent, plies) == plies, then repeatedly the move that keeps the shortest
forced mate.

Usage: d3_misses.py <fens-file> <out.txt>
"""
import sys

import chess

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek_job3")
import b_truth as T

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek_job4")
from b_setting import Engine  # noqa: E402


def shortest_line(board, plies):
    """A shortest forced-mating line as a list of UCI moves, from the mover's side."""
    if plies <= 0:
        return []
    best = None
    for move in board.legal_moves:
        board.push(move)
        if plies == 1:
            ok = board.is_checkmate()
            board.pop()
            if ok:
                return [move.uci()]
            continue
        child = T.mate_in(board, plies - 1)
        want = -(plies - 1)
        if child == want:
            rest = shortest_line(board, plies - 1)
            board.pop()
            if rest is not None:
                return [move.uci()] + rest
            continue
        board.pop()
    return best


def main():
    fens_path, out_path = sys.argv[1:3]
    with open(fens_path) as f:
        fens = [l.strip() for l in f if l.strip() and not l.strip().isdigit()]

    eng = Engine([])
    lines = []
    for fen in fens:
        board = chess.Board(fen)
        # Classify: is the side to move mating (positive) or being mated?
        value = T.mate_in(board, 5)
        plies = abs(value) if value is not None else None
        line = shortest_line(board, plies) if value is not None and value > 0 else None
        d12_move, d12_last = eng.search_at(fen, "depth 12")
        d18_move, d18_last = eng.search_at(fen, "depth 18")
        lines.append(f"FEN   {fen}")
        lines.append(f"  truth mate_in(5) = {value} plies")
        lines.append(f"  shortest line    = {' '.join(line) if line else '(none found / losing side)'}")
        lines.append(f"  depth 12         = {d12_last}")
        lines.append(f"  depth 18         = {d18_last}")
        lines.append("")
    eng.close()
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
