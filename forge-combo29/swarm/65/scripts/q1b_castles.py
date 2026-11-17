#!/usr/bin/env python3
"""Q1b: castling survives the Polyglot decode, checked on the wire.

The book stores castling as Polyglot king-takes-rook (e1h1, e8a8, ...) and
`decode_move` must rewrite it to the king's two-square move before it reaches
UCI. The failure mode that matters is a stored castle reaching the wire in
king-takes-rook form, which no GUI will accept.

So the assertion is not "the engine plays the castle I expected" (Book Variety 0
may legitimately pick a different move). It is:

  1. every book position whose stored moves include a castle, played with
     Variety 0, returns a move that is legal in that position;
  2. that move is never in king-takes-rook form (e1h1/e1a1/e8h8/e8a8);
  3. when the returned move IS a castle, python-chess agrees it is a castle and
     the string is the king's two-square form.

Plus the population count, so the denominator is explicit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402
from q7_soundness import parse_probe  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"
KING_TAKES_ROOK = {"e1h1", "e1a1", "e8h8", "e8a8"}


def main() -> int:
    tsv = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/book_full.txt")
    binary = sys.argv[2] if len(sys.argv) > 2 else "/tmp/build65/forge"
    rows = parse_probe(tsv)

    castle_positions: list[tuple[str, str]] = []
    total_moves = 0
    for fen, _key, _ply, moves_field in rows:
        board = chess.Board(fen)
        for token in [t for t in moves_field.split(",") if t]:
            uci = token.split(":")[0]
            total_moves += 1
            move = chess.Move.from_uci(uci)
            if move in board.legal_moves and board.is_castling(move):
                castle_positions.append((fen, uci))

    kingside = sum(1 for _f, u in castle_positions if u in ("e1g1", "e8g8"))
    print(f"book moves: {total_moves}")
    print(f"book moves that are castles: {len(castle_positions)}/{total_moves}")
    print(f"  kingside {kingside}/{len(castle_positions)}, "
          f"queenside {len(castle_positions) - kingside}/{len(castle_positions)}")

    eng = Engine(binary)
    eng.handshake()
    eng.newgame()
    eng.setoption("OwnBook", "true")
    eng.setoption("Book Variety", "0")
    illegal = []
    ktr = []
    castles_seen = 0
    booked_count = 0
    checked = 0
    try:
        for fen, _uci in castle_positions:
            board = chess.Board(fen)
            eng.position_checked(f"fen {fen}")
            reply = eng.go_and_wait(CLOCK, timeout=30.0)
            lines = reply.bestmove_lines()
            if not lines:
                illegal.append((fen, "NO BESTMOVE", "timeout"))
                continue
            checked += 1
            move_str, _ = parse_bestmove(lines[0])
            if any("book move" in ln for ln in reply.lines):
                booked_count += 1
            if move_str in KING_TAKES_ROOK:
                ktr.append((fen, move_str))
                continue
            try:
                move = chess.Move.from_uci(move_str)
            except ValueError:
                illegal.append((fen, move_str, "unparseable"))
                continue
            if move not in board.legal_moves:
                illegal.append((fen, move_str, "not legal per python-chess"))
                continue
            if board.is_castling(move):
                castles_seen += 1
    finally:
        eng.quit()

    print(f"\ncastle positions exercised through the engine: {checked}/{len(castle_positions)}")
    print(f"  replies that were book moves: {booked_count}/{checked}")
    print(f"  replies that were a castle:   {castles_seen}/{checked}")
    print(f"king-takes-rook strings on the wire: {len(ktr)}/{checked}")
    print(f"illegal or unparseable replies:      {len(illegal)}/{checked}")
    for item in ktr[:5]:
        print(f"  KTR {item[0]} -> {item[1]}")
    for item in illegal[:5]:
        print(f"  BAD {item[0]} -> {item[1]} ({item[2]})")

    if ktr or illegal:
        print("\nFAIL: a stored castle reached the wire in a form a GUI cannot use")
        return 1
    print("\nOK: castling decodes to the king's two-square move; no king-takes-rook "
          "string ever reaches the wire.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
