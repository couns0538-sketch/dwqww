#!/usr/bin/env python3
"""Why O depth 12 does not change when DeadMaterial is on.

A recognized ending has no pawns, rooks, or queens. From a position with P
pieces, a depth-12 search can remove at most 12 pieces, so it can reach a
4-piece ending only when P - 12 <= 4, i.e. P <= 16. O is opening positions.
"""
import chess
from pathlib import Path

folder = Path(__file__).resolve().parent
for name in ("O.fens", "G.epd"):
    counts = []
    for line in (folder / name).read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        fen = " ".join(parts[:6]) if len(parts) >= 6 else line
        counts.append(len(chess.Board(fen).piece_map()))
    print(f"{name} positions {len(counts)} min_pieces {min(counts)} max_pieces {max(counts)} at_most_16 {sum(c <= 16 for c in counts)}")
