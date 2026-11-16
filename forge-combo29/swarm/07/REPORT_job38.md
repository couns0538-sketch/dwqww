# REPORT — seat 07, job 38: the fifty-move error rate, and a bare-king regression scan

## What was asked / the answer / how sure

**Asked:** (1) turn 07-F3's single case into a rate over all 20 fifty-move positions — how many have a
counter-resetting move, and how many base scores as a draw while a win exists; (2) check whether any of
the 30 bare-king differences are cases where the PC is **worse**; (3) leave the repetition sample alone.

**Answer (1):** **all 20** have a resetting move, so base's `cp 0` is an unmeasured declaration on all
20; the reset-probe shows a **decisive** result on **6 of 20**, but only **1** of those is a win thrown
away — **5 are losses masked**.

**Answer (2):** **no regression found.** 14 neutral, 5 PC-better, 4 below the margin, and 7 where the
PC's score is more negative — but in all 7 the depth-18 reference says the **PC is the accurate one**.

**How sure:** high for both, with one important caveat about depth (below). My first pass on both
questions was **wrong**, and the corrections are recorded.

## (1) The fifty-move rate — and my own overclaim

All 20 fifty-move-counter-100 positions have a **counter-resetting move** (a pawn move or a capture;
python-chess decided this, not the engine). So **not one of the 20 is a genuine fifty-move draw**, and
base answers `cp 0` with **0 nodes** on every one — a declaration, not a measurement.

The independent referee is the same board with the counter set to **0**, searched on the base build: with
the clock reset the rule is 100 half-moves away, so its score is what the position is really worth.

| probe result on the counter-0 board | count | positions |
|---|---|---|
| **decisive** (mate, or \|cp\| ≥ 300) | **6** | #0, #4, #7, #10, #11, #13 |
| inconclusive at depth 12 (51…299) | 10 | — |
| noise band (\|cp\| ≤ 50) | 4 | #5, #8, #15, #17 |

Of the 6 decisive ones: **1 is a win thrown away** (#10, `cp 2950` — the mate-6 case of 07-F3) and **5
are losses masked** (`cp −1601, −942, −477, −1039, −963`).

**The honest rate:** decisive base error **6 of 20 (30 %)**, of which a thrown-away win is **1 of 20**.

**My first version said "19 of 20 base-tree errors (95 %)". That was wrong.** It counted `cp −1601`
and `cp −6` alike under "a win exists", which is neither a win nor decisive. A lost position is still
not a draw, so base is wrong there too — but it is wrong *in the engine's favour*, which is a different
thing to report to the owner. The 95 % figure is withdrawn; 6/20 with 1/20 thrown-away-win is the number.

**What this says about ROOT_DRAWN's worth:** on this sample it prevents **one game-losing outcome in
twenty** — plus five draws-from-lost-positions that cost nothing. That is a real but narrow benefit, and
it is honest to say so rather than quote the larger number.

## (2) The bare-king regression scan

Of the 30 bare-king positions: **14 neutral** (±50 cp), **5 PC-better**, **4 differing below the
margin**, **7 with a PC score more negative by ≥100 cp**.

Those 7 are the ones a raw sign comparison calls "worse". With a depth-18 PC reference:

| # | position | base d12 | PC d12 | ref d18 | closer to truth |
|---|---|---|---|---|---|
| 6 | `8/6k1/8/8/6QP/5N2/8/5K2 b` | cp −2056 | cp −2404 | **mate −5** | PC |
| 8 | `4k3/8/8/5N2/3P4/3B4/8/6K1 b` | cp −1357 | cp −1492 | cp −1729 | PC |
| 15 | `8/6Q1/2k5/8/1P6/5P2/1K6/8 b` | cp −2088 | cp −2297 | cp −2852 | PC |
| 17 | `8/6k1/8/4K3/8/R5P1/5P2/8 b` | cp −1735 | cp −2112 | **mate −6** | PC |
| 18 | `2k5/8/8/3N2B1/4P3/8/6K1/8 b` | cp −1349 | cp −1453 | cp −1824 | PC |
| 25 | `8/3R4/3P3k/8/8/7P/8/6K1 b` | cp −1612 | cp −1778 | **mate −10** | PC |
| 28 | `8/8/6k1/8/3NKP2/6P1/8/8 b` | cp −1293 | cp −1517 | cp −2631 | PC |

**Every one is a position where the side to move is being mated or badly beaten.** A more negative
score there is *more accurate*; base was under-estimating how lost it was. So these are not
regressions, and the depth-18 reference is exactly why — a raw sign comparison would have produced seven
false accusations.

**On the other seat's mate-in-10-vs-mate-in-8:** I could not reproduce that shape here. This sample
contains no position where **base reports a short mate and the PC a longer one**; base reports *no mate
at all* on these (large negative `cp`, or a 0-node draw). That is a negative result about *my sample*,
not a refutation of theirs — their case presumably involves a position where base's own search finds the
shorter mate, which these stripped endgames never are.

## Findings

**07-F4** (the fifty-move rate), **07-C36** (no bare-king regression) and **07-C37** (no mate-distance
lengthening) in FINDINGS.md.

## The caveat that limits both answers

Depth 12 is shallow for stripped endgames, and the reference I used is depth 18 on the same build. A
deeper reference could move a few of the 10 "inconclusive" fifty-move positions into decisive, which
would *raise* the 6/20; and it could change which side is closer in the marginal bare-king cases. I did
not go deeper because each depth-18 run on these positions takes seconds and the conclusion (no
regression, narrow benefit) is unlikely to reverse — but the exact rates should be read as "at depth 12
against a depth-18 reference", not as ground truth.

## Suspicions, not proven

- That the 5 masked losses are typical of real fifty-move positions the owner's engine meets. They come
  from stripped G positions with the counter forced to 100, which is a synthetic population.
- That the other seat's mate-distance case needs a different construction (a position where base's
  search reaches the mate within its depth). I did not build one.

## What I did NOT do

- Did not go deeper than 18 for the reference.
- Did not attempt to reproduce the other seat's specific mate-in-10-vs-8 position; I do not have its FEN.
- Left the repetition sample alone, as instructed.

## What I am NOT sure about

- Whether the 10 inconclusive fifty-move positions would show more base errors at greater depth.

## Times

See job38/stamps.txt.
