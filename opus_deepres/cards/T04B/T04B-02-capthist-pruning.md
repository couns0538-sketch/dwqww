# T04B-02: Capture-history pruning of noisy moves at shallow depth
Status: COMPLETE

## Source
- Stormphrax PR 201 "capthist pruning" (merged 2024-11-09 as commit 29e175a2f594):
  https://github.com/Ciekce/Stormphrax/pull/201 , https://github.com/Ciekce/Stormphrax/commit/29e175a2f594
- Its OpenBench tests (result blocks quoted in the PR text): STC https://chess.swehosting.se/test/8996/ ,
  LTC https://chess.swehosting.se/test/8999/

## Licence
Stormphrax @d1468d99e3: GPL-3.0 (notes/T04B/licences.md) - ideas only. Read: the PR title and the OpenBench result
lines of the PR text; no source file, no diff. The PR text carries no formula or description: the mechanism below is
the reading of the title by analogy with quiet history pruning, and every constant is our own.

## Mechanism
Quiet moves with a very bad history are already skipped at low remaining depth. The same test for captures: when the
remaining depth is small and the capture history of this (moving piece, to-square, victim) is far below zero - the
capture has failed again and again in that context - the capture is skipped without a search. The bar falls with
depth, so only captures with a long bad record are cut, and only near the leaves. The first move of a node (usually
the TT move) is never pruned, nor a capture that gives check.

## Forge fit
`bash tools/forge_has.sh 'HistoryPruneMultiplier \*'` -> `src/search.cpp:1070`: history pruning exists for quiet,
non-checking moves only (inside `if (quiet && !gives_check)`, `:1064`). Noisy moves are cut only by capture futility
(off at the lock: `CaptureFutilityBase = 0`, `:1075-1080`) and SEE (`:1081-1083`). The capture history value is
already computed for the move (`:1058`). The guard `best_score > -MateInMaxPly` (`:1061`) keeps the first move and
mate-defence searches safe. Tried gates (`--grep 'Capt|Hist'`): CaptSeeDiv (picker split), PawnHist, ThreatHist,
HistMalusPct - none prunes captures by history; not in R15 C1-C6, Sf26Bundle, round-1 O5 CorrMargins or sol-A1
HistRework. ~4 lines.

## Expected gain
Source: Stormphrax PR 201, OpenBench SPRT [0, 3], Threads=1: STC 8+0.08 Hash 32 MB n=13,814 (W 3470 L 3256 D 7088)
+5.38 +- 3.11, LLR 2.93; LTC 40+0.4 Hash 128 MB n=14,602 (W 3375 L 3178 D 8049) +4.69 +- 2.76, LLR 2.93. Book (corrected by
verify 00:45, read from the OpenBench pages 8996 / 8999): UHO_Lichess_4852_v1.epd, both runs (standard chess, the same
book family as the Forge gate); adjudication win movecount=3 score=400, draw movenumber=40 movecount=8 score=10.
Forge estimate: +1 to +4 Elo **UNPROVEN** (overlaps T04B-01 at the same pruning site; Forge's capture history is
updated only at beta cutoffs with the lock's bonus, `src/search.cpp:752-765`, so its scale differs from the source's).

## Effort
Crew 2 h (option, OFF identity, ON bench, smoke). CPU: one STC SPRT [0, 5], about 3-6k games at 430-502 games/h =
6-14 h, then one LTC. No GPU. Optional: a 2-parameter SPSA (multiplier, depth) before the SPRT.

## Test plan
Pre-gate: OFF bench pins d11-d22 equal the lock; ON bench live; perft unchanged; WAC / mate probe OFF / ON (pruning a
capture can hide a tactic: check the mate counts do not drop). Gate: UHO SPRT [0, 5] at STC, then LTC. Gate alone,
then stacked with T04B-01.

## OFF-by-default design
UCI spin `NoisyHistPrune` default 0 (0 = off; range 500-6000 per ply, own start 2500) and spin `NoisyHistPruneDepth`
(default 3, range 1-6): skip a move when `capture && !move.is_promotion() && !gives_check && !in_check && depth <=
NoisyHistPruneDepth && history < -NoisyHistPrune * depth`. At 0 the condition is never evaluated, so every node and
the bench pins equal the lock. Own values; the source's constants were not read.
