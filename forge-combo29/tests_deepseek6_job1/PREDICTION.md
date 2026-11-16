# PREDICTION — deepseek6, job 1

Written before Part 0's first measuring run and before any of Part 1. Never edited after this commit.

## The prediction (the only content this commit is allowed)

**I predict that 3 of the 35 settings will equal S14 in nodes on all 200 positions of O at BOTH ends of their
step, and I name them:**

1. **`QsSeeMargin`** (40, step 6, runs at 34 and 46) — Opus's own finding explains it: `board.cpp:24` gives
   `SeeValue{0, 100, 300, 300, 500, 900, 0}`, so every SEE result is a multiple of 100 and every margin in
   0..99 compares identically. 34, 40 and 46 are all in that band.
2. **`CaptureFutilityMultiplier`** (250, step 25, runs at 225 and 275) — the block is gated by
   `CaptureFutilityBase > 0` and that option is not in S14, so it holds its table default of 0 and the block
   never runs. Opus states this; I predict it holds on my tree too.
3. **`CaptureFutilityDepth`** (6, step 1, runs at 5 and 7) — the same gate, the same reason.

**The number I predict is 3, and the range that kills it is: fewer than 2 or more than 4.** I allow 2 to 4
because a fourth no-op could exist that I have not reasoned about, and I would rather state the tolerance than
pretend to certainty.

## What would make me doubt the run rather than the tree

- If `QsSeeMargin` differs, then either the SEE lattice is not multiples of 100 in this build or my reading of
  the margin's use is wrong; that is a finding about the engine, not about the harness.
- If the two `CaptureFutility*` settings differ, then `CaptureFutilityBase` is not 0 in S14 on my build — which I
  will check by reading its `uci` line before believing anything else.
- The three controls the job gives me (QsSeeMargin 0, 99, 100) are the harness check and were run BEFORE this
  commit is measured; if one of them had differed I would have stopped the job, as the job says.

## What this prediction does NOT cover

- Any G-side result (the job gives no known answers on G and asks for none).
- Part 3 (a second, further move for the settings that tie on BOTH sets). I do not predict its outcome, and I may
  not reach it inside the budget.
