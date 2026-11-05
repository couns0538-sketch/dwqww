# T04D-01-cutnode-nott-lmr: one more LMR ply at cut nodes that have no TT move
Status: PARTIAL (every unfinished field says PENDING)

## Source
- Stockfish commit [9cc15b3](https://github.com/official-stockfish/Stockfish/commit/9cc15b3049) (2025-02-13), "Do more
  reductions for cut nodes without a tt move", PR text https://github.com/official-stockfish/Stockfish/pull/5875.
- Test logs: STC https://tests.stockfishchess.org/tests/view/67abc9aaa04df5eb8dbeb452 , LTC
  https://tests.stockfishchess.org/tests/view/67abcd7ba04df5eb8dbeb96c (TC, book, threads read from the fishtest
  run API `api/get_run/<id>`).

## Licence
Stockfish GPL-3.0 (Copying.txt at ff7cee4244, 2026-10-28, `tools/licence_at.py`): ideas only. Read: the commit
title and message and the two fishtest run records. No source file or diff was read.

## Mechanism
PENDING

## Forge fit
PENDING

## Expected gain
Source: STC 10+0.1, 1 thread, UHO_Lichess_4852_v1, SPRT normalized [0,2]: LLR 2.93, 42,304 games, W 11,223 L 10,892
D 20,189, Ptnml 184 / 4,904 / 10,669 / 5,187 / 208 = +2.72 +- 1.74 Elo (95 %, own pentanomial arithmetic).
LTC 60+0.6, same book, SPRT [0.5,2.5]: LLR 2.95, 32,334 games, W 8,386 L 8,074 D 15,874, Ptnml 26 / 3,446 / 8,916 /
3,748 / 31 = +3.35 +- 1.81 Elo. Engine: Stockfish master of 2025-02-13 (NNUE).
Forge estimate: PENDING **UNPROVEN**.

## Effort
PENDING

## Test plan
PENDING

## OFF-by-default design
PENDING
