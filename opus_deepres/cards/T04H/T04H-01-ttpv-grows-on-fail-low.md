# T04H-01-ttpv-grows-on-fail-low: a node that fails low under a ttpv parent is stored as ttpv
Status: PARTIAL (every unfinished field says PENDING)

## Source
- Stockfish commit [c02b3a4](https://github.com/official-stockfish/Stockfish/commit/c02b3a4c7a) (2020-08-30), "Add /
  remove leaves from search tree ttPv", PR https://github.com/official-stockfish/Stockfish/pull/3075 . Tests: STC
  https://tests.stockfishchess.org/tests/view/5f49203c3def640786115314 , LTC
  https://tests.stockfishchess.org/tests/view/5f494bea3def640786115336 .

## Licence
Stockfish GPL-3.0 (Copying.txt at c02b3a4c7a): ideas only. Read: commit title and message. No source file or diff.

## Mechanism
PENDING

## Forge fit
PENDING

## Expected gain
STC +2.16 (n=29,968, LLR 2.95), LTC +1.17 (n=84,952, LLR 2.96); TC / book PENDING.
Forge estimate: PENDING **UNPROVEN**.

## Effort
PENDING

## Test plan
PENDING (UHO SPRT [0,5] at STC, then LTC)

## OFF-by-default design
PENDING
