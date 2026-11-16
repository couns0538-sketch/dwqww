# REPORT job11 — area 1 job 3 AGAIN (SEED 2111 game), seat 21

**What was asked.** The cycle's repeat of area 1 job 3 on a second, independent game, with
the 19-F12-safe driver and an assertion that every perft answer contained a `nodes` line.

**The answer.** Exact on every case at both depths. The 1,000-ply legal list is applied
completely (perft 1 = 8, perft 2 = 37, both equal to python-chess on a fresh game — a very
long random game that has reached a sparse endgame). An illegal move at ply 1, 10 and 500
keeps exactly the legal prefix at perft 1 **and** perft 2 (20/400, 28/778, 8/34, all equal to
python-chess); a non-UCI token at ply 1 keeps startpos (20/400). One `info string illegal move`
per bad token; 0 crashes; 0 sanitizer lines.

**How sure.** High: the numbers are exact at two depths on a game nobody has used before; the
parser raises if no `nodes` line is present; every FEN/position command was accepted (the
`full` case has no answer line at all, which is the correct silence for a legal list).

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job11/prediction.txt` | 5 predictions, all held |
| seed-2111 1,000-ply game | done | `job11/out/game_moves.txt` | 1,000 plies |
| perft 1 and 2, engine vs python-chess | done | `job11/out/summary.md` | 5/5 cases exact |
| `nodes` line asserted present | done | `job11/long_moves2.py` (`nodes_of`) | never fired |

## Table (pasted from `job11/out/summary.md`)

| case | answer line | perft1 engine | perft1 python | perft2 engine | perft2 python |
|---|---|---|---|---|---|
| full | none | 8 | 8 | 37 | 37 |
| illegal_1 | `info string illegal move a1b1` | 20 | 20 | 400 | 400 |
| illegal_10 | `info string illegal move a1c1` | 28 | 28 | 778 | 778 |
| illegal_500 | `info string illegal move e2a1` | 8 | 8 | 34 | 34 |
| garbage_1 | `info string illegal move z9z9` | 20 | 20 | 400 | 400 |

## Prediction outcome

P1–P5 all held. Note the incidental fact: the seed-2111 game runs down to 8 legal moves by
ply 1,000, so the two seeds' games have very different character, which is exactly what a
repeat with a new seed is for.

## Findings

No new finding; this is 21-C2's rule reproduced on an independent game.

## Suspicions, not proven

- The random game reaching a sparse position (8 legal moves) is unusual; I did not check how
  often a 1,000-ply random game gets that sparse, so I cannot say whether the prefix rule was
  tested on a "typical" or an extreme case. Both depths agree, which is what matters.

## What I did NOT do

- Did not run under TSan; did not test 5,000-ply lists.

## What I am NOT sure about

- Whether `e2a1` at ply 500 was illegal for a reason a GUI could easily explain (it is a move
  by a piece that is not the side to move's? no — it is simply not in the legal set). The
  engine's single refusal line does not say why; that is the same cosmetic point as in job4.

## Times

see `job11/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job11
long_moves2.py  out  prediction.txt  safe_engine.py  stamps.txt
```
