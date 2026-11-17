# PREDICTION — seat 25, area 5, job 1 SEVENTH RUN (seed 2561, set R7)

Written before the first measuring command of this run, and pushed alone. Never edited afterwards.

## What this run is for: the limitation S-C53 forced on S-C51

S-C54 firmed up the conditional MultiPV rate (53.4% on 58 move-unstable boards vs 10.2% on 342 stable ones). But
board 121 — the second right-length-wrong-mate case — is **stable by that rule**: it keeps `f4e3` at both depths, and
its mate number still moved by 3. So "the search is still changing its mind" operationalised as a **bestmove change**
misses a search that keeps its move while still revising its evaluation. I recorded that limitation in S-C53 rather
than redefining the rule after seeing results. This run tests the remedy it named.

**Two candidate enrichment criteria, to be compared on the same draw:**
- **M (move-unstable):** `bestmove(d12) != bestmove(d16)` — the S-C51/S-C54 rule, 58/400 = 14.5% on R6.
- **S (score-unstable):** `bestmove(d12) == bestmove(d16)` **and** `|score(d12) - score(d16)| >= 50 cp`, both centipawn
  scores. On R6 this selects **143/400 = 35.8%** of boards — from the selection data alone, already computed and
  committed before this prediction was written. Board 121 is in this stratum by construction.

The question: **does the score criterion identify boards where MultiPV matters better than the move criterion does?**
Measured on the same set, with the outcome (MultiPV-1 vs MultiPV-3 disagreement) playing no part in either selection.

## Predictions, each with the range that kills it

S1  All 300 R7 positions measured at depth 12 and 16 (free, MultiPV 1) and at depth 12 under MultiPV 1 and 3.
    KILLED if any cell missing.

S2  The **score stratum** on R7 will be **25-48%** of 300 (75-144 boards). R6 gave 35.8%. KILLED outside
    [15%, 60%]. This is the larger stratum by construction, so it should be reproducible as a planning number.

S3  **The main prediction, and the one I expect to be wrong in an interesting way:** the score stratum's MultiPV
    disagreement rate will be **HIGHER than the move stratum's** on the same draw. Specifically I predict score
    stratum **30-55%** and move stratum **40-65%**, i.e. **the move stratum still wins**. KILLED if the score
    stratum's rate is not below the move stratum's rate. If the score stratum instead BEATS the move stratum, that
    is a better criterion than the one in S-C51 and I will say so plainly even though this prediction then fails.

S4  The two strata will **overlap substantially** — most move-unstable boards are also score-unstable. Predicted
    overlap **60-100%** of the move stratum. KILLED if below 40%. A high overlap is the reason I expect S3 to
    favour the move criterion: the move change is the stronger signal, and the score change mostly picks up boards
    the move criterion already catches.

S5  The stable-and-small-score-change remainder (neither stratum) will have the LOWEST rate: predicted **5-20%**.
    KILLED if above 30%. This is the within-run control.

S6  Every MultiPV disagreement is also a score disagreement: **0 score ties**. KILLED if any. Planted-case control
    repeated (self-vs-self 0/40; three plants caught).

S7  **Mate claims:** I will check whether the score stratum contains any board whose two depths report DIFFERENT
    mate numbers (the board-121 shape) and resolve any found with `claimcheck.py`. On R7, predicted **0-2** such
    boards. KILLED above 4. Given board 121 came from a 400-board set, a ~300-board set should contain about one;
    I am not confident enough to predict more than "0 to 2".

S8  I will NOT predict a mate-score frequency this run. I have now been wrong twice on that quantity in
    opposite directions (39 against a predicted 2-12; 28 against a predicted 40-100). Predicting it a third time
    without a better basis would be guessing with a number attached. I will report the count and say plainly that
    I have no calibrated expectation for it.

## What I will NOT do
- I will not redefine either criterion after seeing the rates.
- I will not present a rate from an enriched stratum as if it were a population rate; every table will carry its
  selection rule and the warning, as S-C54 does.
- I will not resolve a mate claim from its PV. S-C52 and S-C53 each had a legal, right-length, checkmating PV and
  each was wrong.
- I will not quote a cost estimate I have not computed. (S-C55.)
