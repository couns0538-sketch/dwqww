#!/usr/bin/env python3
"""Q5: what happens at a book boundary, one ply past the last book line.

Two boundaries are measured:

A. BOOK -> NOBOOK, same process, walking a line until the book runs out.
   The book answers with `info string book move` + `bestmove` and no info depth.
   The first position without a book entry answers with info depth lines and no
   book marker. The transition is one reply, with nothing in between.

B. The same walk with `Book Depth` set so the gate, not the data, is what stops
   the book. That separates "the book has no entry here" from "the book is not
   allowed here", which look identical on the wire.

C. A clock that expires at the boundary: the search path has to answer, and its
   first answer must still be a legal move.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CLOCK = "wtime 20000 btime 20000 winc 200 binc 200"


def walk_line(binary: str, max_plies: int, book_depth: int | None) -> None:
    """Play bestmove-vs-bestmove from startpos, recording each reply's shape."""
    eng = Engine(binary)
    board = chess.Board()
    try:
        eng.handshake()
        eng.newgame()
        if book_depth is not None:
            eng.setoption("Book Depth", str(book_depth))
        eng.setoption("Book Variety", "0")
        eng.setoption("OwnBook", "true")

        print("| ply | book | info depth | bestmove | legal | wall ms |")
        print("| ---: | --- | ---: | --- | --- | ---: |")
        for ply in range(max_plies):
            pos = f"fen {board.fen()}"
            eng.position_checked(pos)
            t0 = time.monotonic()
            reply = eng.go_and_wait(CLOCK, timeout=60.0)
            ms = (time.monotonic() - t0) * 1000.0
            if reply.timed_out:
                print(f"| {ply} | TIMEOUT | - | - | - | {ms:.1f} |")
                return
            best = reply.bestmove_lines()
            move_str, _ = parse_bestmove(best[0]) if best else (None, None)
            legal = move_str in [m.uci() for m in board.legal_moves] if move_str else False
            booked = any("book move" in ln for ln in reply.lines)
            print(f"| {ply} | {'YES' if booked else 'no'} | {len(reply.info_depth_lines())} | "
                  f"{move_str} | {'yes' if legal else 'NO'} | {ms:.1f} |")
            if not legal:
                return
            board.push(chess.Move.from_uci(move_str))
    finally:
        eng.quit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default="/tmp/build65/forge")
    ap.add_argument("--plies", type=int, default=14)
    args = ap.parse_args()

    chess.Board(START)

    print(f"binary {args.binary}")
    print(f"clock {CLOCK}, Book Variety 0, OwnBook true")
    print()

    print("### A. default Book Depth 30: walk until the data runs out")
    walk_line(args.binary, args.plies, None)
    print()

    print("### B. Book Depth 4: the gate stops the book, data permitting")
    walk_line(args.binary, args.plies, 4)
    print()

    print("### C. Book Depth 100: the gate never stops it; only the data can")
    walk_line(args.binary, args.plies, 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
