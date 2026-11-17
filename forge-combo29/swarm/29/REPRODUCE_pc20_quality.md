# CONFIRM THE PC20 MOVE-QUALITY RESULT (the question is now CLOSED on my evidence — this is the target to beat)

## The claim to check
**PC20's reduced tree costs nothing in move quality, and may be slightly better.** Over every sample I have run,
judging each disagreement under the **neutral S14 regime**:

| depth | positions | disagreements | PC20 better | S14 better | tie |
|---|---|---|---|---|---|
| 10 | 100 | 17 | 7 | 7 | 3 |
| 10 | 200 | 30 | 13 | 13 | 4 |
| 14 | 80 | 13 | 8 | 4 | 1 |
| 14 | 200 | **31** | **19** | **10** | 2 |
| 10 (late G) | 20 | 5 | 2 | 2 | 1 |
| **total** | **600** | **96** | **49** | **36** | **11** |

Move agreement is 85 % at depth 10 and 84.5 % at depth 14. **No sample shows PC20 at a disadvantage beyond noise.**
The 49-36 split is itself not significant (sign test p ≈ 0.10), so the defensible claim is **"no disadvantage at any
depth I measured, possibly a small advantage"** — not "PC20 plays better".

## How to check it in an hour
1. PC r15 build (file 5's patch on 6b98f217, `-DFORGE_MATE_ALPHA_GUARD=1`), **Threads 1, Hash 16**.
2. Positions from real games — `forge-combo29/swarm/29/job5/R_2911.fens` (400 FENs) or your own.
3. Per position: one search under S14, one under PC20 (the 14 S14 options plus `CuckooRep true`, `HistRework 2`,
   `TtPruneV2 true`, `CorrHistV2 true`, `MateAlphaGuard true`, `OwnBook false`), fresh process each, drained to
   `bestmove`.
4. For each disagreement, play BOTH moves and judge under the **neutral S14 regime** 2-3 plies deeper (I used depth 13
   for depth-10 disagreements and depth 17 for depth-14 ones). Report the mover's score each way.
5. **Get at least 30 disagreements before reporting a direction.**

## Numbers to beat
- depth 10, 200 positions: **85.0 % agreement, 13-13-4** over 30 disagreements.
- depth 14, 200 positions: **84.5 % agreement, 19-10-2** over 31 disagreements.
- If you find **PC20 consistently WORSE at match depths**, that is a `REFUTES` and it is the most valuable result
  possible here — it would mean the switches need care in strength matches, which the owner must know.

## The three traps, in the order they caught me
1. **A tally under ~20 outcomes is a hint at most.** My 3-disagreement depth-14 sample read 0-3 against PC20 and I
   published it (29-F50); 13 outcomes gave 8-4 the other way (29-F51); 31 gave 19-10 for PC20 (29-F55). Same
   configuration, three signs.
2. **A tally whose denominator is smaller than the rows in your raw file is a parse bug.** My first tally matched only
   `cp` scores and silently dropped 4 of 17 rows — all mate judgements — turning 7-7-3 into "5 PC20 / 7 S14".
3. **Judge disagreements under the neutral regime, not the switches being tested.** Otherwise PC20 referees its own
   case.

## Why this file exists
This is my strongest work and **no second seat has checked it.** Rather than ask anyone to trust my scripts, here are
the numbers to beat, the falsification condition and the traps. Note the pattern in the totals: **the direction moved
monotonically toward PC20 as samples grew** (0-3 → 8-4 → 19-10), which is what my own small-sample bias looked like
from the inside — my errors ran toward the more alarming story, not the flattering one.
