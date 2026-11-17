#!/usr/bin/env python3
"""Q4c: the book pre-empts drawn-root detection. Three drawn roots, measured.

search.cpp:1686 computes `root_drawn` and answers without searching: score cp 0,
an empty pv, and 64 info depth lines. That is the only signal a caller gets that
the root is drawn. The book check at uci.cpp:371-387 runs before the search is
entered, so on a drawn root the book wins and the caller gets a book move with no
score and no pv instead.

Three roots, each with the book on and off:
  A. halfmove clock 100 (the fifty-move rule), pieces of the start position
  B. insufficient material (king and king)
  C. threefold repetition reached through a real move history

Each row records: book marker, info depth line count, bestmove, and the score
found in the last info depth line (None when there is no info depth line).
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402
from q7b_verify import score_of  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"

FIFTY = "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1"
KVK = "fen 8/8/8/4k3/8/8/4K3/8 w - - 0 1"
# Knights out and back twice: the start position occurs three times.
REPETITION = ("startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8")

CASES = [
    ("fifty-move rule (halfmove 100)", FIFTY, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1"),
    ("insufficient material (KvK)", KVK, "8/8/8/4k3/8/8/4K3/8 w - - 0 1"),
    ("threefold repetition history", REPETITION, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
]


def run(binary: str, position: str, own_book: str) -> tuple[bool, int, str | None, int | None]:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", own_book)
        eng.position_checked(position)
        reply = eng.go_and_wait(CLOCK, timeout=60.0)
        best = reply.bestmove_lines()
        move, _ = parse_bestmove(best[0]) if best else (None, None)
        lines = reply.info_depth_lines()
        score = score_of(lines[-1]) if lines else None
        booked = any("book move" in ln for ln in reply.lines)
        return booked, len(lines), move, score
    finally:
        eng.quit()


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build65/forge"
    for _label, _pos, fen in CASES:
        board = chess.Board(fen)
        assert board.is_valid(), fen

    print(f"binary {binary}")
    print()
    print("| root | OwnBook | book fired | info depth | bestmove | score in last info depth |")
    print("| --- | --- | --- | ---: | --- | --- |")
    rows = {}
    for label, position, _fen in CASES:
        for own in ("true", "false"):
            booked, n, move, score = run(binary, position, own)
            rows[(label, own)] = (booked, n, move, score)
            print(f"| {label} | {own} | {'YES' if booked else 'no'} | {n} | {move} | "
                  f"{'none' if score is None else score} |")

    print()
    preempted = []
    for label, _pos, _fen in CASES:
        on = rows[(label, "true")]
        off = rows[(label, "false")]
        if on[0] and off[3] is not None and off[3] == 0:
            preempted.append(label)
    print(f"roots where the book fired instead of the drawn-root answer: "
          f"{len(preempted)}/{len(CASES)}")
    for label in preempted:
        print(f"  {label}")

    # The fifty-move root is the sharpest case: book on gives a book move with no
    # score at all; book off gives score cp 0 with 64 info depth lines.
    fifty_on = rows[("fifty-move rule (halfmove 100)", "true")]
    fifty_off = rows[("fifty-move rule (halfmove 100)", "false")]
    if not (fifty_on[0] and fifty_on[3] is None and fifty_off[3] == 0):
        print("\nFAIL: the fifty-move case did not demonstrate score loss")
        return 1
    print("\nOK: on a drawn root the book reply drops the score cp 0 / empty pv that the "
          "drawn-root branch would have sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
