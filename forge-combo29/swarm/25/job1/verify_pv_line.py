#!/usr/bin/env python3
"""verify_pv_line.py FEN "moves..." : plays the PV and reports whether it ends in checkmate,
and what the real terminal state is. Used on the engine's own lines."""
import sys

import chess

fen = sys.argv[1]
moves = sys.argv[2].split()
b = chess.Board(fen)
print("start:", fen)
print("plies:", len(moves))
for i, m in enumerate(moves):
    mv = chess.Move.from_uci(m)
    if mv not in b.legal_moves:
        print(f"ILLEGAL at ply {i}: {m}")
        sys.exit(1)
    san = b.san(mv)
    b.push(mv)
    print(f"  {i+1:>2}. {m:<6} {san:<8} {b.fen()}")
print("final FEN:", b.fen())
print("is_checkmate:", b.is_checkmate())
print("is_check:", b.is_check())
print("is_stalemate:", b.is_stalemate())
print("legal moves left:", b.legal_moves.count())
if b.is_checkmate():
    print(f"RESULT: checkmate after {len(moves)} plies = mate in {len(moves)//2} moves"
          if len(moves) % 2 == 0 else
          f"RESULT: checkmate after {len(moves)} plies")
else:
    print("RESULT: NOT checkmate")
