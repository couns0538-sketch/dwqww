#!/usr/bin/env python3
"""Q4b/Q6b: the two remaining gates, measured rather than argued.

A. The `game_ply` gate reads the FEN's move counters, not the game history. Two
   FENs with identical pieces, side to move, castling and en-passant but a
   different fullmove number are the same chess position and different book
   decisions. This measures that.

B. Determinism inside one process: with `Book Variety` above 0 the RNG advances
   on every probe, so ten probes in one process and ten in separate processes
   both vary. With variety 0 the RNG is untouched and both are constant.

C. A repeated identical `go` in one process (same position, no intervening
   command) for both variety settings.
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"


def one(eng: Engine) -> tuple[str | None, bool]:
    reply = eng.go_and_wait(CLOCK, timeout=30.0)
    best = reply.bestmove_lines()
    move, _ = parse_bestmove(best[0]) if best else (None, None)
    return move, any("book move" in ln for ln in reply.lines)


def in_process(binary: str, fen: str, variety: str, n: int) -> list[tuple[str | None, bool]]:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("Book Variety", variety)
        eng.position_checked(f"fen {fen}")
        return [one(eng) for _ in range(n)]
    finally:
        eng.quit()


def per_process(binary: str, fen: str, variety: str, n: int) -> list[tuple[str | None, bool]]:
    out = []
    for _ in range(n):
        eng = Engine(binary)
        try:
            eng.handshake()
            eng.newgame()
            eng.setoption("Book Variety", variety)
            eng.position_checked(f"fen {fen}")
            out.append(one(eng))
        finally:
            eng.quit()
    return out


def summarise(label: str, results: list[tuple[str | None, bool]], n: int) -> None:
    counts = collections.Counter(r[0] for r in results)
    booked = sum(1 for r in results if r[1])
    print(f"{label}: book {booked}/{n}, distinct {len(counts)}/{n} -> "
          + ", ".join(f"{m}:{c}/{n}" for m, c in counts.most_common()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default="/tmp/build65/forge")
    ap.add_argument("--runs", type=int, default=10)
    args = ap.parse_args()

    # Same position, different fullmove numbers. Both are the start position, so
    # the *chess* position is identical and only the FEN counter differs.
    fen_1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    fen_21 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 21"
    for fen in (fen_1, fen_21):
        assert chess.Board(fen).is_valid()

    print(f"binary {args.binary}")
    print()
    print("### A. game_ply gate reads the FEN's fullmove counter, not the history")
    print("fullmove 1 -> game_ply 0; fullmove 21 -> game_ply 40.")
    print()
    print("| FEN fullmove | game_ply | Book Depth 40 | Book Depth 41 |")
    print("| ---: | ---: | --- | --- |")
    for fen, fm in ((fen_1, 1), (fen_21, 21)):
        row = []
        for depth in (40, 41):
            eng = Engine(args.binary)
            try:
                eng.handshake()
                eng.newgame()
                eng.setoption("OwnBook", "true")
                eng.setoption("Book Depth", str(depth))
                eng.position_checked(f"fen {fen}")
                move, booked = one(eng)
            finally:
                eng.quit()
            row.append((move, booked))
        print(f"| {fm} | {(fm - 1) * 2} | {row[0][0]} ({'book' if row[0][1] else 'search'}) | "
              f"{row[1][0]} ({'book' if row[1][1] else 'search'}) |")

    print()
    print("### B. determinism, ten fresh processes vs ten probes in one process")
    for variety in ("0", "30", "100"):
        summarise(f"variety {variety:>3}, fresh processes", per_process(args.binary, fen_1, variety, args.runs), args.runs)
        summarise(f"variety {variety:>3}, one process    ", in_process(args.binary, fen_1, variety, args.runs), args.runs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
