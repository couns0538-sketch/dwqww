#!/usr/bin/env python3
"""verify_walk.py : replays a recorded move list independently and asserts the reached position.

Reads the move list from reach.txt (the line after "exact move list"), replays it from the recorded start
FEN with python-chess, and asserts: every move legal, halfmove clock == 99, not terminal, not a threefold,
and at least one clock-resetting move still available. If any assertion fails the reachability claim is void.
"""
import re
import sys

import chess

txt = open(sys.argv[1]).read()
start = re.search(r"^start .*?: (.+)$", txt, re.M).group(1).strip()
moves_line = None
lines = txt.split("\n")
for i, l in enumerate(lines):
    if l.strip().startswith("exact move list") and i + 1 < len(lines):
        moves_line = lines[i + 1].strip()
        break
assert moves_line, "no move list found"
moves = moves_line.split()

b = chess.Board(start)
print("start:", start)
print("plies to replay:", len(moves))
for i, mv in enumerate(moves):
    m = chess.Move.from_uci(mv)
    assert m in b.legal_moves, f"ILLEGAL move {mv} at ply {i}"
    b.push(m)

print("reached FEN:", b.fen())
print("halfmove clock:", b.halfmove_clock)
resets = [m.uci() for m in b.legal_moves
          if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN]
print("clock-resetting moves available:", len(resets), resets[:5])
print("checkmate:", b.is_checkmate(), "| stalemate:", b.is_stalemate(),
      "| threefold:", b.is_repetition(2), "| insufficient:", b.is_insufficient_material())
ok = (b.halfmove_clock == 99 and not b.is_game_over(claim_draw=False)
      and not b.is_repetition(2) and len(resets) > 0)
print()
print("VERDICT:", "REACHABLE — every move legal, clock 99, game live, reset moves available"
      if ok else "NOT REACHABLE — an assertion failed, do not claim reachability")
sys.exit(0 if ok else 3)
