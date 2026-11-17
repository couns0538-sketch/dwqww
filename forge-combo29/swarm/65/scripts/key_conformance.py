#!/usr/bin/env python3
"""Systematic check: does the engine's polyglot key ever disagree with the
reference implementation, and specifically on en-passant positions?

Builds positions by making random legal double pushes from a few start FENs, so
the FENs always carry a real ep square, then compares /tmp/key_probe with
chess.polyglot.zobrist_hash.

Prints a denominator. Exit 1 on any disagreement, so the script can fail.
"""

from __future__ import annotations

import random
import subprocess
import sys

import chess
import chess.polyglot

SEEDS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1",
    "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
    "8/8/8/4k3/8/8/8/4K3 w - - 0 1",
]


def ep_positions(n: int) -> list[str]:
    rng = random.Random(20261117)
    fens: list[str] = []
    while len(fens) < n:
        board = chess.Board(rng.choice(SEEDS))
        for _ in range(rng.randint(2, 24)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        if board.ep_square is not None:
            fens.append(board.fen())
    return fens


def main() -> int:
    fens = ep_positions(60)
    valid = []
    for fen in fens:
        board = chess.Board(fen)
        if board.is_valid():
            valid.append(fen)

    proc = subprocess.run(["/tmp/key_probe", *valid], capture_output=True, text=True)
    lines = [ln for ln in proc.stdout.strip().split("\n") if ln]

    diffs = []
    checked = 0
    for line in lines:
        if line.startswith("INVALID"):
            print("engine rejected a FEN python-chess accepted: " + line)
            diffs.append((line, "", ""))
            continue
        key, fen = line.split("\t", 1)
        ref = format(chess.polyglot.zobrist_hash(chess.Board(fen)), "016x")
        checked += 1
        if key != ref:
            diffs.append((fen, key, ref))

    print(f"ep positions generated: {len(fens)}")
    print(f"FENs the engine accepted: {checked}/{len(valid)}")
    print(f"key disagreements: {len(diffs)}/{checked}")
    for fen, key, ref in diffs[:10]:
        print(f"  engine {key} reference {ref} | {fen}")

    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
