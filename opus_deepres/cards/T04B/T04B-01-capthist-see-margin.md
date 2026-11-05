# T04B-01: Capture history in the noisy-move SEE pruning threshold
Status: COMPLETE

## Source
- Stormphrax PR 269 "use capthist in noisy see pruning margin" (merged 2025-11-20 as commit a5807f3a9e42):
  https://github.com/Ciekce/Stormphrax/pull/269 , https://github.com/Ciekce/Stormphrax/commit/a5807f3a9e42
- Its OpenBench tests (result blocks quoted in the PR text): STC https://chess.swehosting.se/test/12560/ ,
  LTC https://chess.swehosting.se/test/12563/

## Licence
Stormphrax @d1468d99e3: GPL-3.0 (notes/T04B/licences.md) - ideas only. Read: the PR title and the OpenBench result
lines of the PR text; no source file, no diff. The PR text carries no formula, so the mechanism below is the plain
reading of the title, and every constant is our own.

## Mechanism
In the move loop, a noisy move (capture or promotion) at any depth is skipped when its static exchange loses more
than a material allowance that grows with depth. The idea moves that allowance by the move's capture history: a
capture that has often refuted lines in the same (moving piece, to-square, victim) context may lose a little more
material before it is skipped; one with a poor record is skipped sooner (with a two-sided shift even at a slightly
positive exchange). The shift is clamped so history can never dominate the material test.

## Forge fit
`bash tools/forge_has.sh 'see_threshold'` -> `src/search.cpp:1081-1083`: threshold `-SeeNoisyMultiplier * depth`
(150 cp per ply), no history term. The capture's history is already at hand (`history` = `capture_history_value`,
`src/search.cpp:1058`; table `[piece][to][victim]` int16 +-16384, `include/forge/search.hpp:255`). The same `else`
branch also holds quiet checks, whose `history` is the quiet sum: apply the term to `!quiet` moves only. The
shortcut at `:1082` (picker's good-capture stage and threshold <= 0 skips SEE) stays valid while the threshold is
<= 0; a positive threshold must call SEE. Not the TRIED CaptSeeDiv (packf2 P16a, gates 47 / 48: +3.24 / -3.94 at
1,500 games): that moved the picker's good / bad capture split (ordering, relax-only), not the pruning. Not in R15
C1-C6, Sf26Bundle bits, round-1 O5 CorrMargins or sol-A1 HistRework. Lines to touch: ~3.

## Expected gain
Source: Stormphrax PR 269, OpenBench SPRT [0, 3], Threads=1: STC 8+0.08 Hash 16 MB n=28,964 (W 6991 L 6734
D 15239) +3.08 +- 2.21, LLR 2.95; LTC 40+0.4 Hash 128 MB n=10,130 (W 2245 L 2056 D 5829) +6.48 +- 3.34, LLR 2.93.
Book not stated in the PR (OpenBench default, unknown). The gain was larger at LTC.
Forge estimate: +1 to +4 Elo **UNPROVEN** (Forge's capture history has no threat / defended dimension - Stormphrax
added one later, PR 209 - so the signal may be weaker here).

## Effort
Crew 2 h (option, OFF identity, ON bench, smoke, one debug assert). CPU: one STC SPRT [0, 5], about 3-6k games at the
measured 430-502 games/h = 6-14 h of the gate PC, then one LTC (k times longer per game). No GPU.

## Test plan
Pre-gate: OFF bench pins d11-d22 equal the lock; ON bench live and within 1.5x of OFF; perft unchanged; debug assert
that the term is only added for `!quiet` moves and that a threshold > 0 never takes the SEE shortcut; mate probe
OFF / ON. Gate: UHO SPRT [0, 5] at STC, then LTC (decide at LTC: the source gained more there). Gate it alone first,
then together with T04B-02 (same pruning site).

## OFF-by-default design
UCI spin `NoisySeeHistDiv` default 0 (0 = off; range 16-512, own start 96) and spin `NoisySeeHistCap` (default 150 cp,
range 50-400): for `!quiet` moves the threshold becomes `-SeeNoisyMultiplier * depth - clamp(history /
NoisySeeHistDiv, -NoisySeeHistCap, +NoisySeeHistCap)`. At 0 the expression is the lock's, so every node and the bench
pins are unchanged; the cap is inert while the divisor is 0. Own values; the source's constants were not read.
