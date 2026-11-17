# STATUS — swarm seat 70

Branch `for-fable-and-opus/swarm-70`, folder `forge-combo29/swarm/70/`.
Task: make `searchmoves` semantics exact (five questions from the assignment).

## 2026-11-17T03:50Z — build + honesty pins

Built commit `6b98f217` in `/agent/repos/base` (separate worktree, outside the
work tree), release, g++ 13.3.0, `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`.
NOTE: `/usr/bin/c++` on this machine is clang 18 and its `-lstdc++` is missing, so
CMake must be given `-DCMAKE_CXX_COMPILER=g++` or configuring fails.

Honesty pins, all four, default options, fresh process each:

| pin | got | expected | ok |
|---|---|---|---|
| `bench 11` | 312866 | 312866 | yes |
| `bench 13` | 862329 | 862329 | yes |
| `bench 16` | 3024920 | 3024920 | yes |
| `go perft 5` (startpos) | 4865609 | 4865609 | yes |

Raw: `honesty.txt`

## What is built so far

- `engine.py` — the only UCI driver. One fresh process per search. Sends
  `uci` → setoptions → `ucinewgame` → `position` → `isready` (reads the POSITION
  reply to `readyok`) → `go …` → reads to `bestmove` with a timeout.
  Scans BOTH the position reply and the go output for `invalid FEN` /
  `illegal move`, per the coordinator's correction.
- `gen_positions.py` — writes `job1/ties2.epd` (20), `job1/ties3.epd` (20),
  `job1/ties5.epd` (12), `job1/pinpool.epd` (60). Every FEN is re-proved with a
  fresh python-chess board immediately before it is written; the tie sets carry a
  PROVEN mate-in-1 set, so their root-score tie is a proof and not the engine's
  opinion.
- `job1/ties.py` — the equal-scoring-tie experiment; `job1/ties.csv`,
  `job1/ties.txt`.
- `job4/diagnostic_placement.py` — where `invalid FEN` lands and what an unusable
  `searchmoves` does; `job4/diagnostic_placement.txt`.

## Next

Job 1 contrast on `job1/pinpool.epd` (ordinary positions): does the changed
bestmove carry a changed score, or is it the same score with a different move?
That separates "reorders a tie" from "changes the answer".
