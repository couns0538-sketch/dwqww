# T06C-01-hce-refit-frozen-residual: re-fit the HCE table with the residual net frozen in the loss
Status: PARTIAL (every unfinished field says PENDING)

## Source
- Ethereal b552e36 "Tune all of the NORMAL terms following the NN additions" (commit text, OpenBench tests 7551 /
  7552): https://github.com/AndyGrant/Ethereal/commit/b552e36f88 , http://chess.grantnet.us/test/7551/ ,
  http://chess.grantnet.us/test/7552/
- The net it re-tuned under: Ethereal 513a93c (pawn-king net that augments the HCE, trained as a residual):
  https://github.com/AndyGrant/Ethereal/commit/513a93c232 ; net retrain c8b7199 the same day:
  https://github.com/AndyGrant/Ethereal/commit/c8b7199c3e
- PENDING: method detail (whether the tuner held the net output fixed inside the sigmoid).

## Licence
Ethereal GPL-3.0 (LICENSE at b552e36f88, tools/licence_at.py): ideas only - commit titles and messages read, never
source.

## Mechanism
PENDING

## Forge fit
PENDING

## Expected gain
Ethereal b552e36: STC +6.75 +- 4.22 (10+0.1s, Threads 1, SPRT [0,4], LLR 2.99, 10,240 games), LTC +7.06 +- 3.88
(60+0.6s, LLR 2.96, 8,464 games); data 3 sets of ~10M self-play positions (1s, 2s, 4s games) + 12.5M FRC positions.
Forge estimate: PENDING **UNPROVEN**.

## Effort
PENDING

## Test plan
PENDING

## OFF-by-default design
PENDING
