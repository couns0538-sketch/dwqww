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

## O-3: is the ~5 % clock utilisation intended conservatism, or wasted strength? — the test, ready to run

**Known.** The engine uses 3.3-5.8 % of a 6 s + 0.06 clock in the median on every shape class (my S-F13), and on
startpos the clock path is literally identical to `go depth 19` — 650,246 nodes in 360 ms — while the same
6 seconds given as `go movetime 6000` buys depth 27 (seat 05's S-F37, which I confirmed to the digit as S-C6). The
knob that drives this is `TmSoftDivisor` (default 22): **the soft plan is `available/22 + increment*0.75`, so
22 gives 317 ms of a 6 s clock**, and lowering it measurably buys depth on the same board — I measured
`TmSoftDivisor` 22 -> 364 ms / depth 19, 14 -> 519 ms / depth 20, 10 -> 1265 ms / depth 21, 6 -> 1290 ms / depth 21.

**The fair test, which settles it with games rather than measurement.** Play two versions of the PC r15 engine
against each other, differing in ONE UCI option and nothing else: **A = PC20 unchanged (`TmSoftDivisor` 22)** versus
**B = PC20 plus `setoption name TmSoftDivisor value 10`** (soft plan 644 ms of the same 6 s clock, the setting I
measured at 1265 ms wall and depth 21 on startpos). Send BOTH the same `setoption` list — the full 22-name PC20 set
plus `TmSoftDivisor` at its two values — plus `Threads 1`, `Hash 16`, `MultiPV 1`, `OwnBook false`, and the clock
`wtime 6000 btime 6000 winc 60 binc 60` for every move; change no other constant, no code, and no build (both
sides run the same exe, so any difference is the option alone). Use **positions from real games, not startpos**,
and **at least 400 games** with colours reversed in pairs (200 opening pairs) so a 55 % score is not mistaken for a
real effect: with 400 games the 95 % interval on a 50 % score is about +/-5 %, so **a score outside 45-55 % for B
is evidence the extra time is worth something, and a score inside 45-55 % is evidence it is not**. Report wins,
losses and draws separately, and report B's actual clock usage per move so the reader can see the option took
effect (it should be ~2-4x A's 160-380 ms).

**What the result would mean.** If B scores above 55 %, the 5 % utilisation is wasted strength and `TmSoftDivisor`
is a strength knob worth tuning on the owner's clock; if B sits inside 45-55 % while using 2-4x the time, the
conservatism is correct and the current setting should stay. In strength terms, a 55 % score is **+35 Elo** and
52 % is +14 Elo (the brief's own conversion, `-400*log10(1/m-1)`), so the band 45.1-54.9 % at 400 games
corresponds to roughly **-35 to +34 Elo** — i.e. this test detects an effect of about 35 Elo and would NOT detect
a real 15-Elo gain.

**If 400 games comes out flat but the owner expected a small effect, do NOT conclude "no effect" — escalate to
1,000 games.** The reason is arithmetic, not caution: at 400 games a genuine 15-Elo gain is only a 52 % score,
which sits INSIDE the 45.1-54.9 % flat band, so a flat 400-game result cannot distinguish "no effect" from "a
15-Elo effect"; the test is simply not powered for it. At 1,000 games the band tightens to **46.9-53.1 %
(+/-3.1 %, which is +/-21.6 Elo exactly)**, so a 52 % / +14-Elo gain is still marginal but a 53 % / +21-Elo gain
becomes visible, and resolving 15 Elo properly needs about 1,750 games (**47.7-52.3 %, +/-2.34 %, +/-16.0 Elo**). The formula is `1.96*sqrt(0.25/n)` throughout and I recomputed each of these
rather than estimating them. So the rule is: **400 games answers "is it worth 35 Elo or more"; if the answer is no
and a small effect is plausible, 1,000 games; below that, do not believe a small number without 1,750.** Either answer is useful, which is why this is worth
400 games — and it is the only way to answer it, since both settings produce legal, deterministic, reproducible
search and only a score can separate them.

## O-4: how to size a resource budget for a node-budgeted match
`go nodes N` and `go softnodes N` do not spend N: the search stops at the end of the first iteration that passes
N, so it overshoots by that iteration's cost. Measured over 31 cells (my 28 plus seat 13's 3 worst):
**median 1.30x, 90th percentile 1.72x, maximum 2.24x on my 28 cells; median 1.39x, 90th percentile 2.06x,
maximum 2.64x including seat 13's three worst cells; hard-capped at 4x** (nodes spent / nodes nominated).
**Size from the median or the 90th percentile; budget at 1x and a typical move is 30 % short while one move in ten
is 72 % short, and the worst observed move cost 659,130 nodes against a 250,000 nomination (2.64x).** The 4x cap is
a ceiling for a worst case, not a working figure.
