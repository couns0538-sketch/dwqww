# T07-01: time-disadvantage scaling (spend less when own clock is behind)
Status: PARTIAL (every unfinished field says PENDING)

## Source
Stockfish PR 7113, commit https://github.com/official-stockfish/Stockfish/commit/5ca4bfe72b (2026-09-09,
"Decrease time usage if engine has time disadvantage"). Test logs: STC
https://tests.stockfishchess.org/tests/view/6a8738495b1b38ebda864ed0 , LTC
https://tests.stockfishchess.org/tests/view/6a8ade7a08c0f6a39c9e79cc , sudden-death non-regression
https://tests.stockfishchess.org/tests/view/6a94002a08c0f6a39c9e8b31 , 40/10 non-regression
https://tests.stockfishchess.org/tests/view/6a967e3408c0f6a39c9e91 (link as printed in the commit, may be cut short).

## Licence
GPL-3.0 at 5ca4bfe72b (notes/T07/licences.md) -> ideas only. Read: commit title, PR text, fishtest results. No source.

## Mechanism
PENDING

## Forge fit
PENDING

## Expected gain
Source: STC 10+0.1 +1.13 +- 0.90 (pentanomial 95 %, own calc from the printed Ptnml), 127,360 games, LLR 2.97
(-2.94, 2.94) bounds [0.00, 2.00]; LTC 60+0.6 +1.08 +- 0.69, 191,328 games, LLR 2.94 bounds [0.50, 2.50]; fishtest
default book (UHO-type), Stockfish dev vs master, 1 thread. Non-regression passes: 15+0 (+2.23 +- 1.81, 33,984 games,
[-1.75, 0.25]) and 40/10 (+1.44 +- 1.51, 47,872 games, [-1.75, 0.25]).
Forge estimate: PENDING **UNPROVEN**.

## Effort
PENDING

## Test plan
PENDING (gate route: UHO SPRT [0,5] at STC, then LTC)

## OFF-by-default design
PENDING
