# Does the lost 10 s ply cost anything? The answer is NO — the ply is cosmetic, and the switch set changes moves at EQUAL depth

Direct answer to the question in S-F27. **Reported agreement rate: 75.0 % (12/16).** And the control that
makes that number meaningful says the ply is not what causes disagreement.

## The number asked for

40 positions, PC20's clock run at `wtime 10000` vs base's move at fixed `go depth 20`, restricted to the
16 positions where PC20's clock run ended shallower than base's:

| measurement | agreement | n |
|---|---|---|
| **A1 PC20-clock move vs base's depth-20 move (the question)** | **75.0 %** | **12/16** |
| A2 CONTROL base-clock move vs base's depth-20 move, SAME positions | 87.5 % | 14/16 |
| A3 PC20-clock vs base-clock (both at their own stop) | 81.2 % | 13/16 |
| A4 PC20-clock vs PC20's own depth-20 move | 75.0 % | 12/16 |

## Why that number does NOT show a strength problem with the ply

**The decisive row is the one at equal fixed depth:**

| measurement | agreement | n |
|---|---|---|
| **A5 PC20 at depth 20 vs base at depth 20 (ALL 40 positions, equal depth)** | **72.5 %** | **29/40** |
| A6 PC20 at depth 19 vs base at depth 19 (ALL 40 positions, equal depth) | 80.0 % | 32/40 |

The two builds disagree on **27.5 % of moves at identical fixed depth 20**. That is MORE disagreement than
A1's 25 %, on a larger sample. So removing the depth difference entirely does not restore agreement: **the
switch set changes which move is played at equal depth, and the lost ply contributes nothing measurable on
top of that.** If the ply were the cause, A5 would be near 100 % and A1 would be the low one. The opposite
is observed.

A2 supports the same reading from the other side: even the BASE build's own clock-stopped move disagrees
with its own depth-20 move 12.5 % of the time. A clock stop at this budget is not a depth-20 search for
either build.

## What this means for priority

- **The ply is cosmetic** in the sense that matters for this thread: it is not the cause of any move
  difference between the builds.
- **The real question is a different one, and it is not a ply question:** PC20's switch set selects
  different moves from base at the same fixed depth in 11 of 40 positions. Whether that set is STRONGER or
  WEAKER cannot be answered from move agreement at all — it needs games. A 27.5 % change in chosen move at
  equal depth is a large change and is exactly the kind of thing a match is for.
- Therefore the priority of this thread shifts: the 10 s ply thread can be closed as a note (S-F27 +
  this file), and the open item is **"the PC20 switch set plays different moves than base at equal depth;
  run a match"**, which is not something I can resolve with the tools I have.

## Honest limits

1. **Agreement is not strength.** Two engines can disagree on 27.5 % of moves with the switch set being
   better, worse, or equal. I did not measure strength and this file does not claim any.
2. **The differing moves are not near-equal by eval.** Spot-checking six of the eleven depth-20
   disagreements on the base build, scoring each move's resulting position: `276 vs 1279`, `0 vs 23`,
   `-3015 vs -3737`, `43 vs 19`, `-351 vs -308`, `533 vs 718`. Two of these are large gaps (the 276-vs-1279
   and 533-vs-718 pairs), which means the two builds are not merely tie-breaking differently — but a
   deeper re-search would be needed to say which move is right, so I am not calling anyone's move wrong.
3. **Sample size.** 16 shallow positions for A1/A2/A4 and 40 for A5/A6. The A1-vs-A2 difference (75.0 vs
   87.5) rests on 2 positions and is NOT significant on its own; I lean on A5's 40 positions instead.
4. **One bug I hit and fixed while doing this:** my first attempt to spot-check scores used
   `printf '...\ngo depth 20\nquit\n' | forge`, which is the quit-during-search trap (fifth time in my
   work: job1/README_HARNESS_BUG.md, CHECK_27f2.md, verify_wall_BROKEN_quit_race.txt, CHECK_21f2.md, and
   here). It printed zero `info depth` lines and I caught it before using any number from it. All reported
   numbers come from `ply_cost.py`, which waits for `bestmove`; I verified separately that a depth-20
   search there does complete (20 info lines, 6,737,915 nodes).

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 ply_cost.py ~/build/base-release/forge ~/build/r15-pc/forge /tmp/ply 40
```
Raw: `out_ply/ply_cost.tsv`, `ply_cost.log`.
