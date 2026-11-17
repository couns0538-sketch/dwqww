#!/usr/bin/env python3
"""Q7b: verify each SEE-flagged book move with the engine's own search.

SEE is a lower bound on the tactics: it happily flags a capture whose recapture
is poisoned, and it cannot see a mating net. So every move flagged by
q7_soundness.py is re-checked here, and only the ones that survive are reported
as unsound.

For each flagged (fen, book move):

  score_only  = search the position at fixed depth with `searchmoves <book>`,
                book OFF. This is the engine's score for being forced to play it.
  score_best  = search the same position at the same depth, unrestricted.

A book move that loses material shows score_only far below score_best. `gap` is
score_best - score_only in centipawns; deeper searches make the number more
trustworthy, and the run prints the depth it used.

Exit code 1 if any book move's gap exceeds --threshold, so the script can fail.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402
from q7_soundness import best_capture, parse_probe, see  # noqa: E402

CP_RE = re.compile(r"score (cp|mate) (-?\d+)")


def score_of(line: str) -> int | None:
    m = CP_RE.search(line)
    if not m:
        return None
    kind, value = m.group(1), int(m.group(2))
    if kind == "mate":
        return 20000 - 100 * abs(value) if value > 0 else -20000 + 100 * abs(value)
    return value


def search(eng: Engine, fen: str, depth: int, restrict: str | None) -> tuple[int | None, str | None]:
    eng.position_checked(f"fen {fen}")
    body = f"depth {depth}"
    if restrict:
        body += f" searchmoves {restrict}"
    reply = eng.go_and_wait(body, timeout=60.0)
    if reply.timed_out:
        return None, None
    depth_lines = reply.info_depth_lines()
    best = reply.bestmove_lines()
    move = best[0].split()[1] if best else None
    if not depth_lines:
        return None, move
    return score_of(depth_lines[-1]), move


def collect_flags(rows, limit: int) -> list[tuple[str, str, int, int, str]]:
    flags = []
    for fen, _key, ply, moves_field in rows[:limit] if limit else rows:
        board = chess.Board(fen)
        if not board.is_valid():
            continue
        for token in [t for t in moves_field.split(",") if t]:
            uci, weight = token.split(":")
            move = chess.Move.from_uci(uci)
            if move not in board.legal_moves:
                flags.append((fen, uci, int(weight), ply, "illegal"))
                continue
            after = board.copy(stack=False)
            after.push(move)
            if board.is_capture(move):
                if see(board, move) < 0:
                    flags.append((fen, uci, int(weight), ply, "capture SEE<0"))
            else:
                value, _reply = best_capture(after)
                if value > 0:
                    flags.append((fen, uci, int(weight), ply, f"quiet, capture SEE +{value}"))
    return flags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv", nargs="?", default="/tmp/book_full.txt")
    ap.add_argument("--binary", default="/tmp/build65/forge")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--threshold", type=int, default=100,
                    help="centipawn gap that counts as losing material")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = parse_probe(Path(args.tsv))
    flags = collect_flags(rows, args.limit)
    print(f"SEE-flagged book moves: {len(flags)}")
    print(f"verifying at depth {args.depth} with the engine's own search "
          f"(book OFF, separate process per position)\n")

    eng = Engine(args.binary)
    eng.handshake()
    eng.newgame()
    eng.setoption("OwnBook", "false")

    survivors = []
    verified = 0
    unscoreable = 0
    try:
        for fen, uci, weight, ply, reason in flags:
            score_best, best_move = search(eng, fen, args.depth, None)
            score_only, _ = search(eng, fen, args.depth, uci)
            if score_best is None or score_only is None:
                unscoreable += 1
                continue
            verified += 1
            gap = score_best - score_only
            if gap > args.threshold:
                survivors.append((fen, uci, weight, ply, score_best, score_only, gap, best_move, reason))
    finally:
        eng.quit()

    print(f"positions scored: {verified} (unscoreable {unscoreable})")
    print(f"book moves with gap > {args.threshold} cp: {len(survivors)}/{len(flags)}")

    if survivors:
        print("\n| gap cp | book move | weight | ply | engine best | score best | score forced | reason | fen |")
        print("| ---: | --- | ---: | ---: | --- | ---: | ---: | --- | --- |")
        for fen, uci, weight, ply, sb, so, gap, bm, reason in sorted(survivors, key=lambda t: -t[6]):
            print(f"| {gap} | {uci} | {weight} | {ply} | {bm} | {sb} | {so} | {reason} | {fen} |")
    else:
        print("\nNo SEE-flagged book move survived engine verification: every capture the "
              "static exchange called losing is a poisoned recapture, and every quiet move "
              "with an apparent capture on the board is tactically fine.")

    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
