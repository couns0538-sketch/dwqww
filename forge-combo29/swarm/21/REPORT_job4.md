# REPORT job4 — area 1 job 3 (long `position startpos moves` lists), seat 21

**What was asked.** `position startpos moves` with 1,000 legal plies of a random game (no
game end allowed by the driver: take back to the last position that still had moves), then
the same with one illegal move at ply 1, 10 and 500: the answer lines and which position
the engine keeps (`go perft 1`). Known: an illegal move keeps the legal prefix
(perft 1 = 29 after e2e4 e7e5 e1e3).

**The answer.** All four predictions hold exactly. A 1,000-ply legal list is applied
completely (perft 1 = 5, matching python-chess). An illegal move at ply 1, 10 or 500 keeps
exactly the legal prefix — checked at **both perft 1 and perft 2** against python-chess, not
just at perft 1, and with illegal moves that have a real piece on the from-square (my first
pass used `a1a1`, which is too weak a probe; it is kept in the record as `out_v1`). One
`info string illegal move <token>` per bad token, `readyok` still answered, 0 crashes,
0 sanitizer lines.

**How sure.** High: the prefix counts are exact at two depths, the control is the legal
list itself (which reads 5, not 20), and the illegal tokens are printed in the table.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before the first measuring command | done | `job4/prediction.txt` | 7 predictions |
| 1,000-ply random game, SEED 2101, no truncated end | done | `job4/out/game_moves.txt` | 1,000 plies |
| full list applied | done | `job4/out/full_list.txt` | perft 1 = 5 = python-chess |
| illegal at ply 1 / 10 / 500, real illegal moves | done | `job4/out/illegal_at_*.txt` | prefixes exact at perft 1 and 2 |
| non-UCI token at ply 1 | done | `job4/out/garbage_at_1.txt` | kept startpos, one answer line |
| first pass with a weak illegal token (`a1a1`) | done, superseded | kept in `job4/out_v1` in the git history of this branch | not used for the conclusion |

## Table (pasted from `job4/out/summary.md`)

| case | engine perft 1 / perft 2 | python-chess (prefix) |
|---|---|---|
| full 1,000-ply legal list | 5 | 5 |
| illegal move at ply 1 (`a1b1`) | 20 / 400 | 20 / 400 |
| illegal move at ply 10 (`a1b1`) | 26 / 726 | 26 / 726 |
| illegal move at ply 500 (`b4d8`) | 22 / 100 | 22 / 100 |
| non-UCI token at ply 1 (`z9z9`) | 20 | 20 / 400 |

## Findings

**21-C2 (CONFIRMS the brief's known value, extended in depth).** The legal-prefix rule holds
for a 1,000-ply list at plies 1, 10 and 500, and it holds at **perft 2** as well as perft 1,
which the brief's known value (perft 1 = 29) does not establish.
`python3 job4/long_moves.py ~/b/asan/forge out`

## Suspicions, not proven

- The engine's `info string illegal move` is emitted for a token that is not UCI at all
  (`z9z9`) with the same wording as for a legal-looking move. A GUI cannot tell "your FEN
  was fine but this move is illegal" from "your move text was garbage". Cosmetic.
- I did not test whether the prefix rule holds when the illegal move is the *last* token of a
  1,000-ply list (I used ply 500 as the deepest probe). Not proven either way.

## What I did NOT do

- Did not run a 1,000-ply list under TSan (that is area 4's job).
- Did not test 5,000-ply lists; the brief asks for 1,000.
- Did not measure how long a 1,000-ply apply takes (it is instant; not measured).

## What I am NOT sure about

- The claim "1,000 plies of a real game" is a random game, not a played one. A real game with
  many captures and promotions could stress the undo/make path differently; I did not compare.

## Times

see `job4/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job4
long_moves.py  out  prediction.txt  stamps.txt
```
