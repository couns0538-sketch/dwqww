# REPORT_clockseq — the clock path across a sequence of moves in one process

**What was asked (my own follow-up):** every clock test so far used one `go` per process. The PC's matches keep
ONE process for a whole game. Three scenarios, PC build under PC20, Threads 1, Hash 16.

**The answer: no overruns, no illegal moves, and no leakage between limit types — but under an IDENTICAL clock
the engine's own time use varies by 2.5x from move to move.**

## Scenario A — a real game, clock decreasing by the measured time used plus the increment

```
move  1 w clock 6000 best e2e4 depth 19 engine  430 wall  430.6
move  2 b clock 6000 best c7c5 depth 20 engine  215 wall  216.0
move  3 w clock 5629 best c2c3 depth 20 engine  330 wall  331.1
move  4 b clock 5844 best g8f6 depth 19 engine  151 wall  151.6
move  5 w clock 5357 best e4e5 depth 21 engine  197 wall  198.2
move  6 b clock 5752 best f6d5 depth 22 engine  126 wall  126.3
move  7 w clock 5218 best g1f3 depth 21 engine  167 wall  168.0
move  8 b clock 5685 best b8c6 depth 21 engine  401 wall  402.1
move  9 w clock 5109 best f1c4 depth 20 engine  413 wall  414.3
move 10 b clock 5342 best e7e6 depth 21 engine  148 wall  148.5
overruns: 0 of 10
```
**P1 confirmed:** all 10 moves returned, 0 overruns, every move legal.

## Scenario B — identical 6000 ms clock every move

```
move  1 best e2e4 depth 19 engine 380     move  6 best f6d5 depth 20 engine 174
move  2 best c7c5 depth 20 engine 189     move  7 best g1f3 depth 21 engine 383
move  3 best c2c3 depth 20 engine 312     move  8 best d7d6 depth 18 engine 275
move  4 best g8f6 depth 20 engine 166     move  9 best d2d4 depth 19 engine 191
move  5 best e4e5 depth 19 engine 174     move 10 best c5d4 depth 21 engine 416
engine time: min 166  max 416  ratio 2.51
```
**P3 as I wrote it (within a factor of 2) is REFUTED:** the ratio is **2.51x** with a constant clock. The time
manager varies its own budget move to move — which is expected from a soft limit that reacts to how the previous
iterations behaved, but it is a measured fact and it means "6 s per move" does not mean a consistent effort.

## Scenario C — `go movetime 100` interleaved with clock searches, same position, one process

```
clock search 1: best e2e4 engine 377
movetime 100  : best e2e4 engine  88
clock search 2: best d2d4 engine 552
```
**P4 confirmed:** the movetime limit does not leak — the clock search after it behaves like a clock search. (The
move differs because the intervening search filled the hash table, which is the same search-state effect my
S-F9/S-F19 measured.)

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16, one process per scenario, `position` resent before every `go`
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| A: 10 moves, clock decreasing by measured use + increment | done | `raw/clockseq.txt` | 0 overruns, 0 illegal, all 10 answered |
| B: 10 moves at a constant 6000 ms clock | done | same | engine use 166–416 ms, ratio 2.51x — P3 refuted |
| C: movetime between clock searches | done | same | no leak; the 3rd search behaves as a clock search |
| a full game with increment accumulation | done separately | `../ten_games/raw/ten_games.txt` | 600 moves, 0 overruns |

## Findings

`S-F28 | 6 | in one process across a move sequence the PC build under PC20 at Threads 1 never overruns its clock (0 of 10 moves in a game-shaped sequence, and `go movetime` does not leak into a following clock search), but with an IDENTICAL 6000 ms clock on every move the engine's own search time ranges 166–416 ms — a 2.51x ratio across ten moves — so "6 s per move" does not buy a consistent effort | clockseq/raw/clockseq.txt | NEW |`

## Suspicions, not proven

- That the 2.51x ratio is the soft limit reacting to the previous move's effort. The sequence is consistent with
  it but I did not read the time-manager state.

## What I did NOT do

- Did not isolate why the identical clock gives 166–416 ms (time-manager internals, area 8).
- Did not test a sequence where the clock actually runs low (the ten-game study never fell below ~5 s).

## Times

`clockseq/stamps.txt`, every line a `date -u`.
