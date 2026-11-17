# PREDICTION — seat 25, area 5, job 1 EIGHTH RUN (set V: verification depth benchmark)

Written before the first measuring command of this run, and pushed alone. Never edited afterwards.

## Why this run exists

Board 106 (S-C59) is unadjudicated because exhaustive mate verification could not reach n=6 on that board. I know it
succeeded at n=4 (board 222) and n=5 (board 121/106 excluded), and failed at n=6 once. **That is an anecdote about
three boards, not a stated limit.** Anyone reusing my method needs to know where it stops, and I have been quoting
"succeeds to mate-in-5" as if it were measured.

## Method, fixed in advance

I have **46 unique (position, claimed mate) pairs** already committed across R4/R5/R6/R7, extracted from committed
JSONL only (no new engine searches, no new claims). For each, run the exhaustive `claimcheck.py` with a per-budget time
cap and record for every n whether it completed and what it returned. Then report, **by |N|**:

- how many claims at that |N| were fully adjudicated (the exact distance established),
- how many hit the time cap,
- wall-clock and memo entries at the largest completed budget.

The point is the **ceiling as a measured function of |N|**, not a single board.

**Cap policy, fixed now:** 600 s per budget. A budget that does not finish inside 600 s is recorded as NOT COMPLETED,
never as a negative answer. Claims are processed smallest-|N|-first so the cheap ones are all banked even if the run is
cut short.

## Predictions, each with the range that kills it

S1  All 13 mate-in-1 claims adjudicate, and in a fraction of a second each. KILLED if any mate-in-1 needs more than
    2 s or fails to adjudicate.

S2  Every claim with |N| <= 4 adjudicates within the 600 s cap. R4 evidence: n=4 took 27.3 s (board 222) and 53.7 s
    (board 121). KILLED if any |N|<=4 claim fails to adjudicate.

S3  **|N| = 5 mostly adjudicates but not always:** predicted **2-5 of 5** claims at |N|=5 adjudicate. Evidence: n=5
    took 419.7-451.5 s on two boards (both completed, close to the 600 s cap), and one board's n=5 took 788.8 s
    (board 222) which under THIS run's 600 s cap would NOT complete. KILLED if all 5 adjudicate or if none do.

S4  **|N| >= 6 mostly does not adjudicate:** predicted **0-1 of 6** claims with |N| in 6..15 adjudicate. This is the
    ceiling claim and the reason for the run. KILLED if 3 or more adjudicate.

S5  **The measured ceiling, stated as a testable sentence:** the largest |N| at which MOST claims adjudicate inside
    600 s is **4**. KILLED if that value is 3 or lower, or 6 or higher.

S6  Time grows super-linearly in |N|: the median time at |N|=4 will be at least **10x** the median at |N|=3. KILLED if
    the ratio is below 3x. (Board-level evidence: n=4 ran 26-54 s while n=3 ran 1.4-2.1 s, so ~15-25x.)

S7  Every claim that DOES adjudicate will be adjudicated as either exactly right or wrong-by-a-stated-margin, and I
    will report the split. **I predict 1-4 wrong among the adjudicated set** (S-C52 and S-C53 are two that I already
    know are wrong or right in a specific way; the rest are untested). KILLED if more than 8 are wrong.

S8  No result in this run will be reported as "no mate" when the budget was merely exhausted. I will count and report
    timeouts separately from verdicts, and if any claim cannot be adjudicated I will say so rather than calling it
    false. This is a **process** prediction and it is the one that matters most: it is exactly where board 106's
    honest "candidate" status came from.

## What I will NOT do
- I will not predict a mate-score frequency (S8 of the previous run was a deliberate abstention and it stays).
- I will not treat a timeout as evidence about the position.
- I will not extend the cap mid-run to rescue a prediction; if S3 or S4 misses because of the 600 s policy, the miss
  is recorded with the cap named as the cause, which is itself the measurement.
- I will not quote a cost estimate I have not computed (S-C55).
