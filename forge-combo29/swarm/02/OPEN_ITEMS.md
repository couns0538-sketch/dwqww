# Open items on the owner's clock path — for the owner, not findings

These are questions my measurements made precise but did NOT settle. Each names what is known, what is unknown,
and why it is hard, so nobody re-derives the setup.

## O-1 (the one that matters): there is no forward predictor for the hard-limit cut
**Known.** A move's wall time is the last completed iteration's cost, and a hard-limit cut shows up retrospectively
as a wall-to-last-iteration ratio near 2.4 (1585.6 ms wall against a 667 ms last iteration on
`8/8/6k1/Q7/1P4PP/1K3P2/8/8 b`). Two candidate predictors were tested and both failed: "last iteration / soft plan
> 1" gives 8 false positives in 20 boards, and `TmFinishIteration true` changes nothing (1585.5 vs 1585.7 ms
medians, zero hold lines in 10 runs).

**Unknown.** A predictor would need the engine to estimate the NEXT depth's cost at the moment the plan is
crossed — and that is hard because the effective deadline is not the plan: the stop test compares cumulative
elapsed against `soft_limit_ms` multiplied by `factor`, and **`factor` ranges from 0.45 to 3.0** (TmStableFactor
60/100, TmSemiStableFactor 80/100, TmUnstableFactor 140/100, floor TmMinFactorPercent 45), further scaled by an
effort-share term and a falling-evaluation term (src/search.cpp:2934-2981). So the deadline itself is only known
to within a factor of ~6.7 while the search runs, before any question of estimating the next iteration's cost.

**Why I did not do it.** It is a search change, not an option, and it belongs to whoever owns the search with a
match to validate it. Nothing in my measurements suggests a cheap approximation would work: seat 28's S-F35
measured a naive next-iteration predictor at a 58 % median absolute error and a >3000 % worst case, which is
independent agreement that this is genuinely hard rather than un-attempted.

## O-2: why the hard limit is reachable at all on a sparse endgame
**Known.** On a board with 5 legal moves the engine crossed its 317 ms soft plan at depth 16 (~667 ms), started
depth 17, and was killed at the 1585 ms hard limit.
**Unknown.** Whether that is specific to sparse endgames or simply needs a position where one depth costs more
than the remaining plan. 20 boards establish the mechanism, not a rate — seat 08's 08-F29 puts the heavy-tail rate
at ~4 % of searches over 60 boards per class, which is a larger sample than mine and I would defer to it.

## O-3: the utilisation number is not explained by the tail
**Known.** The engine uses 3.3-5.8 % of a 6 s clock in the median, in every class, and 26.2 % at the worst single
board in twenty.
**Unknown.** Whether using ~5 % of the clock is intended conservatism or leaves strength on the table. Seat 05's
S-F37 measures the same shape from the other side (`go movetime 6000` uses 5.99 s and reaches depth 27 where the
clock path reaches depth 19 in 0.36 s), which suggests the gap is a time-management choice rather than a limit of
the search. Settling which is right needs a strength match, not more measurement.
