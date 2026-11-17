#!/usr/bin/env python3
"""Q8c: four `game_ply` derivations against every position form, retracting the
earlier "defect" claim only if the data supports the retraction.

Why this exists: the first write-up called the `Book Depth` counter dependence a
defect. Building candidate fixes showed the lock is exact and the "fixes" are not.
This script is the systematic test, covering every `position` form the UCI spec
allows crossed with both counter directions, so the retraction (or its absence)
rests on a matrix rather than on an anecdote.

Derivations:

  LOCK    `2*(fullmove-1) + (black?1:0)`   on the board after `position`
  NAIVE   `history_size() - 1`
  HYBRID  `history_size() > 1 ? history-1 : 2*(fullmove-1)+(black?1:0)`
  BASEPLY recorded at `position` time as (counter ply) + (moves appended)

Expected behaviour is defined from *the caller's own input*: whatever ply the
supplied command implies. A FEN carries no history, so its counter is the caller's
statement of how many moves preceded it and that statement is not verifiable — a
derivation is judged against it, not against a history the caller never sent.

Exit 1 if LOCK is not correct on every case, so the retraction cannot be published
unless the matrix agrees.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"
LINE = "e2e4 c7c5 c2c3 e7e5 g1f3 b8c6"


def probe(binary: str, position: str, depth: int) -> bool:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "true")
        eng.setoption("Book Variety", "0")
        eng.setoption("Book Depth", str(depth))
        eng.position_checked(position)
        reply = eng.go_and_wait(CLOCK, timeout=30.0)
        return any("book move" in ln for ln in reply.lines)
    finally:
        eng.quit()


def main() -> int:
    args = sys.argv[1:]
    lock = args[0] if len(args) > 0 else "/tmp/build65/forge"
    naive = args[1] if len(args) > 1 else "/tmp/sw65-fixes/naive-build/forge"
    hybrid = args[2] if len(args) > 2 else "/tmp/sw65-fixes/hybrid-build/forge"
    baseply = args[3] if len(args) > 3 else "/tmp/fix3build/forge"
    builds = [("LOCK", lock), ("NAIVE", naive), ("HYBRID", hybrid), ("BASEPLY", baseply)]

    moves = LINE.split()
    b = chess.Board()
    for _ in range(2):
        b.push(chess.Move.from_uci(moves.pop(0)))
    honest = b.fen()
    tail = " ".join(moves)

    # Counter variants, in plies.
    def shift(fen: str, fullmoves: int) -> str:
        parts = fen.split()
        parts[5] = str(max(1, int(parts[5]) + fullmoves))
        return " ".join(parts)

    # (key, position command, ply the command implies, Book Depth, expected)
    cases = [
        # startpos: the engine generates the counter, so it cannot be wrong.
        ("A1", f"startpos moves {LINE}", 6, 7, True),
        ("A2", f"startpos moves {LINE}", 6, 6, False),
        ("A3", f"startpos moves {' '.join(LINE.split()[:2])}", 2, 3, True),
        ("A4", f"startpos moves {' '.join(LINE.split()[:2])}", 2, 2, False),
        # fen + moves, counter honest for the FEN (2 plies played before it).
        ("B1", f"fen {honest} moves {tail}", 6, 7, True),
        ("B2", f"fen {honest} moves {tail}", 6, 6, False),
        # fen + moves, counter inflated by 2 plies: the input says ply 8.
        ("B3", f"fen {shift(honest, 1)} moves {tail}", 8, 7, False),
        ("B4", f"fen {shift(honest, 1)} moves {tail}", 8, 9, True),
        # fen + moves, counter deflated by 2 plies: the input says ply 4.
        ("B5", f"fen {shift(honest, -1)} moves {tail}", 4, 3, False),
        ("B6", f"fen {shift(honest, -1)} moves {tail}", 4, 5, True),
        # bare fen, no moves at all.
        ("C1", f"fen {honest}", 2, 3, True),
        ("C2", f"fen {honest}", 2, 2, False),
        ("C3", f"fen {shift(honest, 1)}", 4, 3, False),
        ("C4", f"fen {shift(honest, 1)}", 4, 5, True),
    ]

    for key, pos, _ply, _d, _e in cases:
        if pos.startswith("fen"):
            body = pos.split(" moves")[0][4:]
            assert chess.Board(body).is_valid(), (key, body)

    print("builds:")
    for name, path in builds:
        print(f"  {name:<8} {path}")
    print()
    print("| case | form | input implies ply | Book Depth | expected | "
          + " | ".join(n for n, _ in builds) + " |")
    print("| --- | --- | ---: | ---: | --- | " + " | ".join("---" for _ in builds) + " |")

    wrong = {name: 0 for name, _ in builds}
    total = 0
    for key, pos, ply, depth, expect in cases:
        form = "startpos" if pos.startswith("startpos") else (
            "fen+moves" if " moves" in pos else "fen")
        cells = []
        for name, binary in builds:
            got = probe(binary, pos, depth)
            if got != expect:
                wrong[name] += 1
                cells.append(("book" if got else "no book") + " WRONG")
            else:
                cells.append("book" if got else "no book")
        total += 1
        print(f"| {key} | {form} | {ply} | {depth} | {'book' if expect else 'no book'} | "
              + " | ".join(cells) + " |")

    print()
    for name, _ in builds:
        print(f"{name:<8} wrong: {wrong[name]}/{total}")

    lock_ok = wrong["LOCK"] == 0
    print()
    print(f"LOCK correct on every case: {'YES' if lock_ok else 'NO'}")
    return 0 if lock_ok else 1


if __name__ == "__main__":
    sys.exit(main())
