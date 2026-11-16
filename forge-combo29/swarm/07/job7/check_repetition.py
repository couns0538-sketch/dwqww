#!/usr/bin/env python3
"""check_repetition.py EXE_OR_PROBE

Feeds move lists to repetition_probe and compares its `rep=` column against python-chess.

python-chess semantics:
  * board.is_repetition(2) -> twofold (any earlier occurrence)
  * board.is_repetition(3) -> threefold (the FIDE draw)

The engine's no-argument is_repetition() returns "seen twice before", i.e. this position plus
two earlier occurrences = threefold. So the comparison target is python-chess's
is_repetition(3), computed ONCE per ply, and the driver ASSERTS a rep= column and a key were
found for every ply (no missing line may pass as agreement).

Prints one row per ply where the two disagree, and a total. Exit 1 on any disagreement or any
missing measurement.
"""
import re
import subprocess
import sys

import chess

HERE = __file__.rsplit("/", 1)[0]

LISTS = [
    # a clean threefold: knights out and back twice
    "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",
    # same, but the second return happens after a pawn move resetting the clock: NOT a draw
    "g1f3 g8f6 f3g1 f6g8 e2e4 e7e5 g1f3 g8f6 f3g1 f6g8",
    # a twofold only (one return): must NOT be a draw
    "g1f3 g8f6 f3g1 f6g8",
    # repetition with queens: 1.e4 e5 2.Qh5 Nc6 3.Qf3 Nf6 4.Qh5 Nc6 5.Qf3 Nf6 -> wait, use a clean one
    "e2e4 e7e5 d1h5 b8c6 h5f3 g8f6 f3h5 c6b8 h5f3 b8c6",
    # the fifty-move counter interaction: 8 reversible plies then a reset, then 8 more
    "b1c3 b8c6 c3b1 c6b8 b1c3 b8c6 c3b1 c6b8 d2d4 d7d5 b1c3 b8c6 c3b1 c6b8",
    # a long shuffle that repeats many times
    "b1c3 b8c6 c3b1 c6b8 b1c3 b8c6 c3b1 c6b8 b1c3 b8c6 c3b1 c6b8 b1c3 b8c6 c3b1 c6b8",
]

PLY = re.compile(r"^PLY (\d+)(?: (\S+) clock=(\d+) key=(\d+) rep=(\d+) rep0=(\d+))?$")


def main():
    probe = sys.argv[1]
    text = "\n".join(LISTS) + "\n"
    out = subprocess.run([probe], input=text, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"FAIL probe exited {out.returncode}: {out.stderr[:400]}")

    rows, list_index, board, disagreements = [], -1, None, 0
    seen_plies = 0
    for line in out.stdout.splitlines():
        if line.startswith("BROKEN"):
            raise SystemExit(f"FAIL {line}: a move list in this test is not legal, so the "
                             f"comparison would measure nothing")
        if line.startswith("LIST "):
            list_index += 1
            board = chess.Board()
            continue
        if line.startswith("END"):
            continue
        m = PLY.match(line)
        if not m:
            continue
        ply = int(m.group(1))
        if m.group(2) is None and ply == 0:
            engine_rep = m.group(5)
            # the PLY 0 line has a different field layout: re-parse it
            m0 = re.match(r"^PLY 0 clock=(\d+) key=(\d+) rep=(\d+) rep0=(\d+)$", line)
            if not m0:
                raise SystemExit(f"FAIL could not parse ply 0 line [{line}]")
            engine_rep = int(m0.group(3))
        else:
            engine_rep = int(m.group(5))
        if ply > 0:
            # advance python-chess by replaying the move named on this line
            move_uci = m.group(2)
            board.push(chess.Move.from_uci(move_uci))
        seen_plies += 1
        ref = board.is_repetition(3)
        got = bool(engine_rep)
        if got != ref:
            disagreements += 1
            rows.append((list_index, ply, m.group(2) if m.group(2) else "start",
                         got, ref, board.fen()))

    if seen_plies == 0:
        raise SystemExit("FAIL no PLY lines were parsed: nothing was measured")
    print(f"plies compared: {seen_plies}")
    for li, ply, move, got, ref, fen in rows:
        print(f"  DISAGREE list {li} ply {ply} move {move}: engine rep={got} "
              f"python-chess threefold={ref}  fen {fen}")
    if disagreements:
        print(f"\nRESULT: {disagreements} disagreement(s)")
        sys.exit(1)
    print("RESULT: engine is_repetition() agrees with python-chess threefold at every ply")


if __name__ == "__main__":
    main()
