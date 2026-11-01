# Second timing experiment — declared before measurements

First experiment is inconclusive: A/A paired median +1.679%, candidate +1.632%,
21/56 runs contaminated. No speed claim or accepted handover follows from it.

The approved plan permits retaining and replacing entire contaminated blocks.
Use that method for experiment 2, with the same frozen lock and c1 executable,
same d20, Threads=1, Hash=16, Idle, logical CPU 2, and no concurrent owned heavy work.

Changes from experiment 1:

- Warm each fresh process with d20 instead of d16, before its timed d20.
- Wait for both logical CPUs 2/3 to sample <20% over three seconds before each block.
- A block is eligible only if ALL FOUR timed runs have CPU/wall >=0.95 and sibling
  utilization <30%. This is the original during-run threshold, unchanged.
- Keep every row and every rejected block with its measured reason. Replace the
  whole block; never retain selected individual runs or use NPS/gain for eligibility.
- Collect exactly four eligible A/A blocks. Require original control criteria:
  absolute median paired bias <=0.75 points and IQR <=3 points. If this fails,
  stop c1 timing (second failure of the same control check), record rejection.
- After passing control, collect ten eligible ABBA blocks (20 alternating pairs).
  Cap each phase at 80 attempted blocks and the original six-hour deadline.
- Report selected quiet-block statistics AND all-attempt statistics, plus rejected
  block count/reasons and first-experiment results. Speed gate remains >=1% paired
  median; no incomplete experiment passes.

This change addresses observed interference, not an unfavorable candidate result.
Independent review is required before running this protocol. No code/binary changes.
