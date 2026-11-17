#!/usr/bin/env python3
"""Q1/Q2 matrix: which `go` forms reach the book, and what the book's wire output is.

Two positions are used for each form:
  BOOK   - startpos (the embedded book has a move here)
  NOBOOK - after 1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O (out of the book)

Both are validated with python-chess before use, and the engine's own
`invalid FEN` diagnostic is scanned in BOTH the position reply and the go reply.

For every cell we record: book_fired, info_depth_line_count, bestmove, wall ms.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402

BOOK_POSITION = ("fen", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
# Ruy Lopez Closed-ish: 1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O, 9 plies in.
NOBOOK_POSITION = (
    "fen",
    "r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6",
)


def validate(fen: str) -> None:
    board = chess.Board(fen)
    if not board.is_valid():
        raise SystemExit(f"python-chess rejects FEN: {fen} -> {board.status()}")


GO_FORMS = [
    ("clock wtime/btime", "wtime 10000 btime 10000", None),
    ("movetime", "movetime 100", None),
    ("depth", "depth 6", None),
    ("nodes", "nodes 50000", None),
    ("infinite", "infinite", 0.35),
]


def run_cell(binary: str, pos_cmd: str, go_body: str, stop_after: float | None) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        pos_reply = eng.position(pos_cmd)
        t0 = time.monotonic()
        go_reply = eng.go_and_wait(go_body, timeout=30.0, stop_after=stop_after)
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        diag = "invalid FEN" in pos_reply.text() or "invalid FEN" in go_reply.text()
        best = go_reply.bestmove_lines()
        move, ponder = parse_bestmove(best[0]) if best else (None, None)
        return {
            "book": any("book move" in ln for ln in go_reply.lines),
            "info_depth": len(go_reply.info_depth_lines()),
            "move": move,
            "ponder": ponder,
            "diag": diag,
            "timed_out": go_reply.timed_out,
            "ms": elapsed_ms,
            "lines": go_reply.lines,
        }
    finally:
        eng.quit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default="/tmp/build65/forge")
    args = ap.parse_args()

    validate(BOOK_POSITION[1])
    validate(NOBOOK_POSITION[1])

    print(f"binary {args.binary}")
    print(f"BOOK   {BOOK_POSITION[1]}")
    print(f"NOBOOK {NOBOOK_POSITION[1]}")
    print()
    print("| position | go form | book_fired | info depth lines | bestmove | invalid FEN | wall ms |")
    print("| --- | --- | --- | ---: | --- | --- | ---: |")
    rows = []
    for label, pos_cmd in (("BOOK", BOOK_POSITION[1]), ("NOBOOK", NOBOOK_POSITION[1])):
        for form_name, go_body, stop_after in GO_FORMS:
            cmd = f"fen {pos_cmd}"
            r = run_cell(args.binary, cmd, go_body, stop_after)
            rows.append((label, form_name, r))
            print(
                f"| {label} | go {form_name} | {'YES' if r['book'] else 'no'} | {r['info_depth']} | "
                f"{r['move']}{' ponder ' + r['ponder'] if r['ponder'] else ''} | "
                f"{'YES' if r['diag'] else 'no'} | {r['ms']:.1f} |"
            )

    print()
    print("--- raw go output, book cells ---")
    for label, form_name, r in rows:
        if label == "BOOK":
            print(f"[BOOK / go {form_name}]")
            for ln in r["lines"]:
                print("   " + ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
