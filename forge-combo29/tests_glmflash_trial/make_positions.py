#!/usr/bin/env python3
"""glmflash trial Step 3: 500 different legal positions for the TSan soak.

Spec (from the job prompt):
  - 500 different legal chess positions
  - random legal moves from the start position
  - 8 to 60 plies
  - fixed random seed 20261115
  - no position where the game is over

Method: for each attempt, pick a target ply count uniformly in [8, 60] with the
seeded RNG, play that many uniformly random legal moves from the start
position, and keep the final position only if
  * the game did not end early (we could always complete the planned plies),
  * the position is not game over per python-chess is_game_over()
    (checkmate / stalemate / insufficient material / dead position), and
  * its FEN has not been kept before (all 500 are different).

Ply counts are recorded while generating because a FEN carries no move
history; they are printed with the run summary and written to
positions_validation.txt together with a per-position re-check
(valid FEN, legal, not game over, ply within [8, 60]).

"Game is over" is judged by python-chess 1.11.2; within 60 plies from the
start the 50-move and repetition rules cannot trigger, so this is in practice
checkmate / stalemate / insufficient material / dead position.

Dependency used at run time: python-chess 1.11.2, installed during the trial
with `pip3 install python-chess` (recorded here so the run is reproducible).
Output: positions.txt (one FEN per line) next to this script.

Run as:
  python3 make_positions.py
"""

import random
import pathlib

import chess

SEED = 20261115
COUNT = 500
MIN_PLIES = 8
MAX_PLIES = 60

def main() -> None:
    rng = random.Random(SEED)
    out: list[str] = []
    plies: list[int] = []
    seen: set[str] = set()
    attempts = 0
    while len(out) < COUNT:
        attempts += 1
        target = rng.randint(MIN_PLIES, MAX_PLIES)
        board = chess.Board()
        completed = True
        for _ in range(target):
            moves = list(board.legal_moves)
            if not moves:
                completed = False
                break
            board.push(rng.choice(moves))
        if not completed:
            continue
        if board.is_game_over():
            continue
        fen = board.fen()
        if fen in seen:
            continue
        seen.add(fen)
        out.append(fen)
        plies.append(len(board.move_stack))
    here = pathlib.Path(__file__).resolve().parent
    (here / "positions.txt").write_text("\n".join(out) + "\n")
    invalid = over = wrong_ply = 0
    with (here / "positions_validation.txt").open("w") as report:
        for i, (fen, ply) in enumerate(zip(out, plies), 1):
            board = chess.Board(fen)
            ok = board.is_valid() and not board.is_game_over() and MIN_PLIES <= ply <= MAX_PLIES
            if not board.is_valid():
                invalid += 1
            if board.is_game_over():
                over += 1
            if not (MIN_PLIES <= ply <= MAX_PLIES):
                wrong_ply += 1
            if not ok:
                report.write(f"BAD {i} plies={ply} {fen}\n")
        report.write(
            f"attempts={attempts} written={len(out)} unique={len(set(out))} "
            f"invalid={invalid} game_over={over} wrong_ply={wrong_ply} "
            f"plies min={min(plies)} max={max(plies)} seed={SEED}\n")
    print(f"attempts={attempts} written={len(out)} unique={len(set(out))} "
          f"invalid={invalid} game_over={over} wrong_ply={wrong_ply} "
          f"plies min={min(plies)} max={max(plies)}")

if __name__ == "__main__":
    main()
