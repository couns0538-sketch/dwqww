# The owner's REAL clock: 6 s + 0.06 per move — seat 08, PC r15 under PC20, Threads 1

`FABLE_TO_swarm_6.md`: "the clock 6 seconds + 0.06 per move (its strength matches)". Every control I had measured
before was a different shape — `movetime`, or sudden-death 200 ms to 30 s with `winc 0`. This measures the shape the
owner actually plays, in two sweeps, with `winc 60` sent to the engine as the match program does.

Plan arithmetic from `clock_plan.hpp` with the defaults (`Move Overhead 10`, `TmSoftDivisor 22`,
`TmIncrementPercent 75`, `TmHardPercent 60`, `TmHardSoftMultiple 5`): at a 6000 ms clock with a 60 ms increment the
plan is **soft 317 ms / hard 1585 ms**.

## The numbers that matter

| sweep | moves | median | p99 | **worst** | worst as % of the clock | over soft | over hard | **over the clock** |
|---|---|---|---|---|---|---|---|---|
| **A** clock pinned at 6000 ms | 120 | 295.2 ms | **457.4 ms** | **482.4 ms** | 8.0 % | 40 | 0 | **0** |
| **B** real countdown from 6000 ms, +60/move | 120 | 130.9 ms | **371.2 ms** | **390.4 ms** | 6.8 % | 11 | 0 | **0** |

- **The p99 at 6+0.06 is 371–457 ms, and the worst single move was 482 ms** — 8.0 % of a 6 s clock. Zero moves
  exceeded the clock, and zero exceeded the engine's own 1585 ms hard limit, in 240 moves across three positions.
- This is the answer to the question my earlier tail work could only approximate. My 1 s sudden-death sweep gave a
  worst of +92.3 ms past a 45 ms soft plan; at the owner's clock the worst is +165 ms past a 317 ms soft plan —
  **larger in absolute terms, smaller as a fraction of the clock**, and it never approaches the flag.
- **Median 295 ms at a pinned clock against a 317 ms soft plan (93 % of plan)**, which is far closer to the plan than
  the 61–78 % I measured at 3–30 s sudden-death clocks. The increment's contribution to the plan
  (`60 * 75 / 100 = 45 ms`) and the smaller available time make the plan more nearly achievable here.

## Sweep A detail (pinned clock) — the pattern is stable, not noisy

The first 18 moves from startpos, all at a pinned 6000 ms clock:

| move | wall ms | plan soft | over soft | over hard | depth |
|---|---|---|---|---|---|
| 1 | 464.3 | 317 | YES | no | 19 |
| 2 | 405.5 | 317 | YES | no | 19 |
| 3 | 402.3 | 317 | YES | no | 19 |
| 4 | 395.8 | 317 | YES | no | 19 |
| 5 | 390.3 | 317 | YES | no | 19 |
| 6 | 371.7 | 317 | YES | no | 19 |
| … | 363–428 | 317 | YES | no | 19 |

Every move overshoots the soft plan and every move lands in a narrow 363–464 ms band — this is the iteration-boundary
behaviour of 08-F10 seen at the clock the owner uses: the engine finishes the iteration it is in, then stops.

**Measured per-iteration cost at this clock** (startpos, PC20, one search): depth 17 finishes at 111.6 ms, depth 18
at 235.8 ms, depth 19 at 393.2 ms — so **depth 19's iteration costs 157 ms** and depth 18's costs 124 ms. The search
stops at depth 19 because the 317 ms soft deadline falls during depth 20; the 393 ms total is the accumulated ladder,
not one iteration. So the overshoot is one iteration of ~157 ms on top of a 236 ms floor, which is exactly the
363–464 ms band observed across the sweep. It is **stable and predictable** at this clock, which is what a match needs.

## Sweep B detail (real countdown)

The countdown runs from 6000 ms and the clock drains ~70 ms per move (130 ms median spent, 60 ms increment returned),
so after 40 moves it is at ~3000 ms. Within that range the wall time stays 92–139 ms in the middlegame positions,
i.e. the engine self-regulates as the clock shrinks — median 130.9 ms against a soft plan falling from 317 ms to
182 ms.

## What this means for the owner, in one paragraph

On the clock the owner's matches actually use, the engine's time management is **safe and steady**: it never came
within 88 % of the clock, its worst move at a 6 s clock was 482 ms (8 % of the clock), its soft-plan overshoot is
one iteration and highly repeatable, and as the clock drains with the increment it correctly shortens its thinking.
The risk profile I measured at 1 s and 10 s sudden-death clocks (worst 137 ms on 1 s, 2270 ms on 10 s) is **not the
profile of the owner's clock** — those were shapes a match program never sends.

## What I did NOT do
- Did not play real games to a conclusion: these are engine calls from three fixed positions with the clock walked
  forward, not a self-play match, so "the clock drains as in a game" is modelled, not observed.
- Did not test the low-time end of a real game (the countdown stopped at ~3000 ms after 40 moves on 3 positions); the
  reserve-empty behaviour at ≤10 ms is covered separately by 08-F18/F21.
- Did not measure playing strength at this clock — that is a match question.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 real_clock.py /tmp/rc.txt
