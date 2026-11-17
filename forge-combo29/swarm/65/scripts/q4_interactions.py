#!/usr/bin/env python3
"""Q4: does `OwnBook true` interact with the drawn-root bail, MultiPV, or the clock?

Each block below runs one engine process per row so that a leaked option cannot
colour the next row.

Signals recorded for every row:
  book        - an `info string book move` line appeared
  info_depth  - count of `info depth` lines
  bestmove    - the move, plus the `ponder` suffix if any
  invalid     - `invalid FEN` seen in the position reply or the go reply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# Same start position, 100-ply halfmove clock: search calls this a drawn root.
DRAWN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1"
# KvK: insufficient material, the other drawn-root trigger.
KVK = "8/8/8/4k3/8/8/4K3/8 w - - 0 1"
# Checkmate is not a drawn root; it is the "no legal moves" branch.
MATED = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"


def cell(binary: str, options: list[tuple[str, str]], fen: str, go: str,
         stop_after: float | None = None) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        for name, value in options:
            reply = eng.setoption(name, value)
            if reply.timed_out:
                raise RuntimeError(f"no readyok after setoption {name}")
        pos = eng.position(f"fen {fen}")
        go_reply = eng.go_and_wait(go, timeout=30.0, stop_after=stop_after)
        best = go_reply.bestmove_lines()
        move, ponder = parse_bestmove(best[0]) if best else (None, None)
        return {
            "book": any("book move" in ln for ln in go_reply.lines),
            "info_depth": len(go_reply.info_depth_lines()),
            "move": move,
            "ponder": ponder,
            "invalid": "invalid FEN" in pos.text() or "invalid FEN" in go_reply.text(),
            "lines": list(go_reply.lines),
            "timed_out": go_reply.timed_out,
        }
    finally:
        eng.quit()


def report(title: str, rows: list[tuple[str, list[tuple[str, str]], str, str, float | None]]) -> None:
    print(f"### {title}")
    print("| case | book | info depth | bestmove | invalid FEN |")
    print("| --- | --- | ---: | --- | --- |")
    for name, opts, fen, go, stop in rows:
        r = cell(BINARY, opts, fen, go, stop)
        bm = f"{r['move']}" + (f" ponder {r['ponder']}" if r["ponder"] else "")
        print(f"| {name} | {'YES' if r['book'] else 'no'} | {r['info_depth']} | {bm} | "
              f"{'YES' if r['invalid'] else 'no'} |")
    print()


BINARY = "/tmp/build65/forge"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default="/tmp/build65/forge")
    global BINARY
    BINARY = ap.parse_args().binary

    for fen in (START, DRAWN, KVK, MATED):
        board = chess.Board(fen)
        assert board.is_valid(), f"python-chess rejects {fen}"

    print(f"binary {BINARY}")
    print()

    report("A. drawn-root bail vs OwnBook", [
        ("drawn root (halfmove 100), book ON", [("OwnBook", "true")], DRAWN, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("drawn root (halfmove 100), book OFF", [("OwnBook", "false")], DRAWN, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("drawn root by insufficient material, book ON", [("OwnBook", "true")], KVK, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("checkmated root, book ON", [("OwnBook", "true")], MATED, "wtime 10000 btime 10000 winc 100 binc 100", None),
    ])

    report("B. MultiPV vs OwnBook", [
        ("MultiPV 1", [("OwnBook", "true"), ("MultiPV", "1")], START, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("MultiPV 2", [("OwnBook", "true"), ("MultiPV", "2")], START, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("MultiPV 3", [("OwnBook", "true"), ("MultiPV", "3")], START, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("MultiPV 3, book OFF, movetime 100", [("OwnBook", "false"), ("MultiPV", "3")], START, "movetime 100", None),
    ])

    report("C. clock extremes vs OwnBook", [
        ("wtime 1 btime 1 winc 1 binc 1", [("OwnBook", "true")], START, "wtime 1 btime 1 winc 1 binc 1", None),
        ("wtime 10 btime 10 winc 1 binc 1", [("OwnBook", "true")], START, "wtime 10 btime 10 winc 1 binc 1", None),
        ("wtime 0 btime 0 winc 1 binc 1", [("OwnBook", "true")], START, "wtime 0 btime 0 winc 1 binc 1", None),
        ("movetime 1", [("OwnBook", "true")], START, "movetime 1", None),
        ("movetime 0", [("OwnBook", "true")], START, "movetime 0", None),
        ("movetime 0, book OFF", [("OwnBook", "false")], START, "movetime 0", None),
    ])

    report("D. forms the book is excluded from, with OwnBook true", [
        ("go depth 6", [("OwnBook", "true")], START, "depth 6", None),
        ("go nodes 50000", [("OwnBook", "true")], START, "nodes 50000", None),
        ("go infinite + stop", [("OwnBook", "true")], START, "infinite", 0.4),
        ("go wtime + searchmoves e2e4", [("OwnBook", "true")], START,
         "wtime 10000 btime 10000 winc 100 binc 100 searchmoves e2e3", None),
        ("go wtime + mate 2", [("OwnBook", "true")], START, "wtime 10000 btime 10000 winc 100 binc 100 mate 2", None),
        ("go ponder + stop", [("OwnBook", "true"), ("Ponder", "true")], START,
         "wtime 10000 btime 10000 winc 100 binc 100 ponder", 0.4),
    ])

    report("E. Book Depth gate (game_ply)", [
        ("Book Depth 0, clock", [("OwnBook", "true"), ("Book Depth", "0")], START, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("Book Depth 1, clock (ply 0)", [("OwnBook", "true"), ("Book Depth", "1")], START, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("Book Depth 1, clock, black to move (ply 1)", [("OwnBook", "true"), ("Book Depth", "1")],
         "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("Book Depth 2, clock, black to move (ply 1)", [("OwnBook", "true"), ("Book Depth", "2")],
         "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", "wtime 10000 btime 10000 winc 100 binc 100", None),
    ])

    report("F. Ponder prediction on a book move", [
        ("Ponder false", [("OwnBook", "true"), ("Ponder", "false")], START, "wtime 10000 btime 10000 winc 100 binc 100", None),
        ("Ponder true", [("OwnBook", "true"), ("Ponder", "true")], START, "wtime 10000 btime 10000 winc 100 binc 100", None),
    ])
    return 0


if __name__ == "__main__":
    sys.exit(main())
