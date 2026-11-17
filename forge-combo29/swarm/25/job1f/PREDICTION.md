# PREDICTION — seat 25, area 5, job 1 SIXTH RUN (seed 2551, set R6, 400 positions)

Written before the first measuring command of this run, and pushed alone. Never edited afterwards.

## What this run is for

S-C51 established that the MultiPV disagreement rate is conditional: **53.3% (16/30)** on boards where depth 12 and
depth 16 chose different best moves, and **14.1% (31/220)** where they did not, with non-overlapping Wilson intervals.
The weak point, which I named in that row, is that the unstable stratum is only **30 boards** and its interval is
[36.1%, 69.8%] - wide enough that the exact rate could be anything from "a bit more common" to "twice as common".

So this run's single job is to **firm up the unstable-stratum rate on a set that is larger and selected for that
property on purpose**, rather than accepting whatever 30 boards a random draw happened to yield.

**Method, fixed in advance:**
1. Draw 400 fresh positions (seed 2551), measure bestmove at depth 12 and at depth 16 as a FREE search (MultiPV 1).
2. Define the unstable set as those where the two moves differ. Select it entirely by this criterion - no peeking at
   the MultiPV result before selecting.
3. On the unstable set, measure MultiPV 1 vs MultiPV 3 at depth 12 and compute the disagreement rate.
4. On the stable set, do the same, as the within-run control from a single draw.

Because the selection rule uses only the d12-vs-d16 move comparison, and the outcome measured is the MultiPV
disagreement, the two are independent measurements of the same board - so the rate is not inflated by selection.

## Predictions, each with the range that kills it

S1  All 400 positions measured at both depths and both MultiPV settings. KILLED if any cell is missing.

S2  The unstable stratum on R6 will be **12-30% of 400 boards** (48-120 boards). R4 gave 30/250 = 12.0%. KILLED if
    below 8% (32 boards) or above 40% (160 boards). A very high unstable fraction would mean my "hard" definition
    catches most positions and stops being a stratum.

S3  **The main prediction: the unstable-stratum MultiPV disagreement rate on R6 will land inside 35-70%**, i.e. it
    will CONFIRM S-C51's 53.3% rather than merely fail to contradict it. KILLED if it lands below 25% or above 80%.
    With 48-120 unstable boards, a 35-70% band is a real test at this sample size rather than an unfalsifiable one.

S4  The stable-stratum rate on R6 will land inside **8-25%**, consistent with 14.1%. KILLED if above 35%.

S5  The unstable rate will EXCEED the stable rate by a clear margin: the two Wilson 95% intervals will not overlap.
    This is the same claim as S-C51 but now on a set where the unstable arm is selected to be large, so an overlap
    here would genuinely weaken S-C51 rather than being a small-sample artifact. KILLED if the intervals overlap.

S6  Every MultiPV disagreement is also a score disagreement: **0 score ties** among differing bestmoves. KILLED if
    any differing bestmove has an equal top-line score. Planted-case control repeated (self-vs-self on 40 boards must
    give 0; three planted corruptions must all be caught).

S7  Mate scores are not rare, per the S5 kill of the previous run: predicted **40-100** top-line mate scores across
    the 1600 searches (400 boards x 2 depths x 2 settings). KILLED if below 20 or above 160. This prediction exists
    because I was wrong about the previous one by 3x and want a record of whether the corrected expectation holds.

S8  Any board where the two settings report DIFFERENT mate numbers will be resolved with `claimcheck.py`, and I
    predict **at most 3** such boards. KILLED if more than 6. Where one occurs I resolve it exhaustively or state
    it unresolved - no guessed verdicts.

## What I will NOT do
- I will not widen the predicted bands after seeing the data.
- I will not resolve a mate claim by inspecting its PV. S-C52 proved a right-length PV ending in checkmate can still
  be the wrong distance; only exhaustive search or a completed budget counts.
- I will not report a rate from the unstable set without also reporting the stable set from the same draw.
