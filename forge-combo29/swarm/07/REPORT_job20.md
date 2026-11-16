# REPORT — seat 07, job 20: increment-heavy clock plans, and a share worth a human's judgement

## What was asked / the answer / how sure

**Asked:** finish the area-7 read; job19's clock-plan arithmetic raised a question about
increment-heavy time controls that only a real clock game can answer.

**Answer:** the plan **never loses on time** in five increment-heavy controls (160 plies), but it is
**aggressive**: with `movestogo 40`, a 1000 ms clock and a 1000 ms increment it will spend up to
**79.6 %** of the remaining clock on one move (average 36.6 %). I am reporting that as a
behavioural observation for Opus to judge, **not** as a fault, because the increment refunds the
time and no control lost on time.

**How sure:** high on the measurement (real decrementing clock, real increment, per-move wall times in
job20/raw/). Deliberately *not* claiming it is wrong — I have no evidence the policy is unintentional,
and the header documents the increment term.

## Honesty numbers

Base build pins unchanged (job0/raw/summary.txt: 312866 / 862329 / 3024920 / 4865609). No engine
source changed; this job measures behaviour only.

## The arithmetic, from the code

include/forge/clock_plan.hpp, movestogo branch:

    soft = available / (mtg + 1) + increment * 3 / 4
    hard = std::min(available * 4 / 5, soft * 4)

For `wtime 1000 btime 1000 winc 1000 binc 1000 movestogo 40`, with the default 10 ms Move Overhead:
available = 990, so soft = 990/41 + 1000·3/4 = **24 + 750 = 774**, hard = min(792, 3096) = **792**.

That is 78 % of the usable clock for one move out of forty. It is bounded (`hard ≤ available`), and
the increment returns 1000 ms afterwards, so it is not obviously wrong — it is aggressive.

## Result

    inc_eq_clock_mtg40     plies  40  max share of clock  0.796  average  0.366  losses 0
    inc_eq_clock_sudden    plies  30  max share of clock  0.599  average  0.271  losses 0
    inc_gt_clock           plies  30  max share of clock  0.598  average  0.344  losses 0
    inc_half_clock_mtg40   plies  40  max share of clock  0.494  average  0.184  losses 0
    inc_tiny_clock         plies  20  max share of clock  0.582  average  0.341  losses 0

    RESULT: no loss on time in any increment-heavy control; shares reported above

Per-move tables (ply, remaining clock, wall time, share, lost): job20/raw/<control>.txt.

## Why I am not filing this as a finding

Three reasons, stated so a reader can disagree with me:

1. `hard ≤ available` holds in every case I checked (420 grid cases in job19 plus these games), so the
   engine cannot exceed its own clock from this arithmetic alone.
2. The increment is refunded **after** the move; spending 774 ms of a 990 ms clock with a 1000 ms
   increment leaves the clock higher than it started.
3. The term is explicitly in the code with a documented meaning (`increment * 3 / 4` in the movestogo
   branch, `increment * increment_percent / 100` in the sudden-death branch), so it looks intended.

What I *can* say is that a 0.8 share of the clock on one move is the kind of policy that shows up as
time-trouble losses in fast games against strong opponents, and Opus is better placed than I am to
judge whether that is the intent.

## Findings

**07-C17** in FINDINGS.md — clean result plus the recorded share.

## Suspicions, not proven

- Whether the increment term should be capped relative to `available`. Not proven either way.
- `Move Overhead` default 10 ms is subtracted once per move; at 50 ms clocks that is already 20 % of
  the budget, which is why `inc_tiny_clock` shows a 0.582 peak share.

## What I did NOT do

- Did not run these as games against an opponent, so I cannot say whether the aggressive policy wins
  or loses games — only that it does not lose on time.
- Did not vary `TmSoftDivisor` / `TmIncrementPercent` tunables.

## What I am NOT sure about

- Whether a real GUI's measured clock differs from my model (I decrement by measured wall time, which
  is a fair model of a GUI that starts the clock at `go`).

## Times

See job20/stamps.txt.
