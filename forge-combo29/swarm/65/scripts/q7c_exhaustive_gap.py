#!/usr/bin/env python3
"""Q7c: exhaustive quality sweep over every book move.

For each (position, book move) the engine scores the position twice at a fixed
depth, book OFF:

    score_best   unrestricted
    score_forced with `searchmoves <book move>`

gap = score_best - score_forced, in centipawns. A book move that loses material
or throws away the position shows a large gap.

One engine process is reused, and `setoption name Clear Hash` runs between every
pair so a warm table cannot make the second search of a pair look better than
the first. Positions come from probe_book, so the set is exactly the reachable
book.

Prints max/mean gap and the worst offenders. Exit 1 if any gap exceeds
--threshold, so the script can fail.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402
from q7b_verify import score_of  # noqa: E402
from q7_soundness import parse_probe  # noqa: E402


def search(eng: Engine, fen: str, depth: int, restrict: str | None) -> int | None:
    eng.position_checked(f"fen {fen}")
    body = f"depth {depth}" + (f" searchmoves {restrict}" if restrict else "")
    reply = eng.go_and_wait(body, timeout=30.0)
    if reply.timed_out:
        return None
    lines = reply.info_depth_lines()
    return score_of(lines[-1]) if lines else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv", nargs="?", default="/tmp/book_full.txt")
    ap.add_argument("--binary", default="/tmp/build65/forge")
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--threshold", type=int, default=150)
    ap.add_argument("--max-positions", type=int, default=0)
    args = ap.parse_args()

    rows = parse_probe(Path(args.tsv))
    if args.max_positions:
        rows = rows[: args.max_positions]

    eng = Engine(args.binary)
    eng.handshake()
    eng.newgame()
    eng.setoption("OwnBook", "false")

    gaps: list[tuple[int, str, str, str, int, int]] = []
    checked = 0
    skipped = 0
    try:
        for fen, _key, ply, moves_field in rows:
            board = chess.Board(fen)
            if not board.is_valid():
                skipped += 1
                continue
            for token in [t for t in moves_field.split(",") if t]:
                uci, weight = token.split(":")
                eng.setoption("Clear Hash", "")
                best = search(eng, fen, args.depth, None)
                eng.setoption("Clear Hash", "")
                forced = search(eng, fen, args.depth, uci)
                if best is None or forced is None:
                    skipped += 1
                    continue
                checked += 1
                gaps.append((best - forced, uci, fen, weight, best, forced))
    finally:
        eng.quit()

    gaps.sort(reverse=True)
    print(f"depth {args.depth}, Clear Hash between each pair")
    print(f"book moves scored: {checked} (skipped/unscoreable {skipped})")
    if not checked:
        print("FAIL: nothing was scored")
        return 2

    values = [g[0] for g in gaps]
    print(f"max gap: {max(values)} cp")
    print(f"mean gap: {statistics.mean(values):.2f} cp")
    print(f"median gap: {statistics.median(values)} cp")
    for bound in (0, 25, 50, 75, 100, 150, 200, 300):
        n = sum(1 for v in values if v > bound)
        print(f"  gap > {bound:>3} cp: {n}/{checked}")

    print("\nworst 15 book moves by gap:")
    print("| gap | book move | weight | score best | score forced | fen |")
    print("| ---: | --- | ---: | ---: | ---: | --- |")
    for gap, uci, fen, weight, best, forced in gaps[:15]:
        print(f"| {gap} | {uci} | {weight} | {best} | {forced} | {fen} |")

    over = [g for g in gaps if g[0] > args.threshold]
    print(f"\nbook moves with gap > {args.threshold} cp: {len(over)}/{checked}")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
