# T07-02: score-stability scaling of the soft limit (stop sooner when the score holds still)
Status: PARTIAL (every unfinished field says PENDING)

## Source
Alexandria PR 618, commit https://github.com/PGG106/Alexandria/commit/49391d7b70f3d90b936f6db9c646e37e8fba1858
(2026-07-22, "Introduce score stability TM scaling"). OpenBench logs: STC https://chess.swehosting.se/test/14309/ ,
LTC https://chess.swehosting.se/test/14310/ . Earlier variant: PR 438, commit
https://github.com/PGG106/Alexandria/commit/8e3fc66e52 (2024-06-24, "Introduce eval stability in time management").

## Licence
GPL-3.0 at 49391d7b70 (notes/T07/licences.md) -> ideas only. Read: commit messages, PR text, OpenBench pages. No source.

## Mechanism
PENDING

## Forge fit
PENDING

## Expected gain
Source (PR 618): STC 8+0.08 Threads=1 Hash=16MB +4.24 +- 2.63 (95 %), 16,560 games, LLR 2.89 (-2.25, 2.89) bounds
[0.00, 3.00], Penta [28, 1830, 4365, 2026, 31]; LTC 40+0.4 Threads=1 Hash=64MB +4.00 +- 2.49, 16,844 games, LLR 2.91
[0.00, 3.00]. Book: PENDING. Older variant (PR 438): STC +1.42 +- 1.15 (92,920 games), LTC +1.71 +- 1.37 (56,588).
Forge estimate: PENDING **UNPROVEN**.

## Effort
PENDING

## Test plan
PENDING (gate route: UHO SPRT [0,5] at STC, then LTC)

## OFF-by-default design
PENDING
