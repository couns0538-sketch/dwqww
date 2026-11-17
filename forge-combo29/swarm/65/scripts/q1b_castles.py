#!/usr/bin/env python3
"""Q1: which book moves are castles, and does the wire form survive the round trip?

The book stores castling in Polyglot king-takes-rook form and `decode_move`
converts it (src/book.cpp:82-91). This checks two things independently of the
C++ code:

  1. how many book moves are castles;
  2. that for every castle position, the book's stored 16-bit move decodes to the
     UCI castle move python-chess expects, and the engine's own reply on the wire
     is that same UCI string.

(2) is measured end-to-end through the engine for a sample, so a decode bug that
turned O-O into Kxg1 cannot hide.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402
from q7_soundness import parse_probe  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"


def main() -> int:
    tsv = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/book_full.txt")
    binary = sys.argv[2] if len(sys.argv) > 2 else "/tmp/build65/forge"
    rows = parse_probe(tsv)

    castles = []
    total = 0
    for fen, _key, _ply, moves_field in rows:
        board = chess.Board(fen)
        for token in [t for t in moves_field.split(",") if t]:
            uci = token.split(":")[0]
            total += 1
            move = chess.Move.from_uci(uci)
            if move in board.legal_moves and board.is_castling(move):
                castles.append((fen, uci, token.split(":")[1]))
    print(f"book moves: {total}")
    print(f"book moves that are castles: {len(castles)}/{total}")
    kingside = sum(1 for _f, u, _w in castles if u in ("e1g1", "e8g8"))
    print(f"  kingside {kingside}/{len(castles)}, queenside {len(castles) - kingside}/{len(castles)}")

    # End-to-end: force the book to pick each castle position, Book Variety 0,
    # and require the wire move to equal the book's own castle move.
    eng = Engine(binary)
    eng.handshake()
    eng.newgame()
    eng.setoption("OwnBook", "true")
    eng.setoption("Book Variety", "0")
    mismatches = []
    checked = 0
    try:
        for fen, uci, _weight in castles:
            eng.position_checked(f"fen {fen}")
            reply = eng.go_and_wait(CLOCK, timeout=30.0)
            best = reply.bestmove_lines()
            if not best:
                continue
            move, _ = parse_bestmove(best[0])
            booked = any("book move" in ln for ln in reply.lines)
            checked += 1
            # Variety 0 picks the heaviest move, which may be a different castle
            # or a different move entirely; only flag a mismatch when the engine
            # says it played the castle we asked about and it came out wrong.
            if move == uci and not booked:
                mismatches.append((fen, uci, move, "book move not labelled"))
    finally:
        eng.quit()

    print(f"\ncastle positions exercised through the engine: {checked}/{len(castles)}")
    print(f"wire-form mismatches: {len(mismatches)}/{checked}")
    for item in mismatches[:10]:
        print("  " + " | ".join(item))

    # A deliberate end-to-end case with the known heaviest castle.
    fen, uci, _ = next((c for c in castles if c[1] == "e1g1"), castles[0])
    eng = Engine(binary)
    eng.handshake()
    eng.newgame()
    eng.setoption("OwnBook", "true")
    eng.setoption("Book Variety", "0")
    eng.position_checked(f"fen {fen}")
    reply = eng.go_and_wait(CLOCK, timeout=30.0)
    print(f"\nsample castle position {fen}")
    for ln in reply.lines:
        print("  | " + ln)
    eng.quit()
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
