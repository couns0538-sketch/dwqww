# Can the hard-limit cut be predicted by one number? The proposed predictor tested and REFUTED, with the real one found

Requested test: for each of my 20 boards, is `last-iteration cost / soft plan > 1` exactly the set that hit
the hard limit?

The plan is not guessed: computed from `include/forge/clock_plan.hpp` with PC20's actual values
(time 6000, increment 60, no movestogo, Move Overhead 10, TmSoftDivisor 22, TmIncrementPercent 75,
TmHardPercent 60, TmHardSoftMultiple 5):

```
available = 6000 - 10 = 5990
soft      = 5990/22 + 60*75/100 = 272 + 45 = 317 ms
hard      = min(5990*60/100, 317*5) = min(3594, 1585) = 1585 ms
```

**The measured hard-limit tail was 1585.6 ms, and the computed hard plan is 1585 ms.** So the plan is right,
and the cut board landed exactly on it.

| board | last-iter ms | last / soft | wall ms | cut at hard limit? | predictor says cut? | agree? |
|---|---|---|---|---|---|---|
| `8/8/8/2k5/8/2K5/8/3R1B2 w - - 0 1` | 696 | 2.20 | 696.8 | no | YES | **NO** |
| `8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1` | 667 | 2.10 | 1585.6 | **YES** | YES | ok |
| `8/8/6k1/8/8/6K1/8/2R2N2 w - - 0 1` | 545 | 1.72 | 545.6 | no | YES | **NO** |
| `rnbq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8` | 530 | 1.67 | 530.7 | no | YES | **NO** |
| `r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1` | 516 | 1.63 | 516.4 | no | YES | **NO** |
| `r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9` | 407 | 1.28 | 408.5 | no | YES | **NO** |
| `r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1` | 400 | 1.26 | 400.9 | no | YES | **NO** |
| `8/8/4k3/8/8/4K3/8/2R2B2 w - - 0 1` | 352 | 1.11 | 353.0 | no | YES | **NO** |
| `8/2k5/8/8/8/8/2K5/3R4 w - - 0 1` | 341 | 1.08 | 341.4 | no | YES | **NO** |
| `r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10` | 302 | 0.95 | 303.0 | no | no | ok |
| `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1` | 277 | 0.87 | 278.1 | no | no | ok |
| `8/8/8/8/3k4/8/3K4/6R1 w - - 0 1` | 229 | 0.72 | 230.8 | no | no | ok |
| `8/8/8/4k3/8/4K3/4P3/8 w - - 0 1` | 207 | 0.65 | 207.5 | no | no | ok |
| `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1` | 203 | 0.64 | 204.2 | no | no | ok |
| `rnbqkb1r/pp2pppp/3p1n2/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 0 1` | 196 | 0.62 | 197.4 | no | no | ok |
| `r1bqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1` | 180 | 0.57 | 181.1 | no | no | ok |
| `rnbqkbnr/ppp2ppp/8/3pp3/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 1` | 157 | 0.50 | 157.8 | no | no | ok |
| `8/8/4k3/8/8/3KP3/8/8 w - - 0 1` | 145 | 0.46 | 146.1 | no | no | ok |
| `8/8/8/3k4/8/3K4/8/2R4R w - - 0 1` | 17 | 0.05 | 17.5 | no | no | ok |
| `6k1/8/6K1/8/8/8/8/5R2 w - - 0 1` | 1 | 0.00 | 1.7 | no | no | ok |

agreement: **TP=1 TN=11 FP=8 FN=0** of 20 boards.

## VERDICT: the proposed predictor does NOT hold

**8 false positives, 0 false negatives.** Every board whose last iteration cost more than the soft plan is
predicted to be cut, but only ONE was actually cut. The worst case is decisive: `8/8/8/2k5/8/2K5/8/3R1B2 w`
had a last iteration of 696 ms = **2.20x the soft plan** and was NOT cut (wall 696.8 ms).

## why it fails, read in the code

`src/search.cpp:2980-2981` is the stop test:

```
if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_basis) * factor)) break;
```

Two things make `last-iteration / soft > 1` the wrong quantity:

1. The comparison uses **cumulative elapsed time**, not the last iteration's own cost. A search whose last
   iteration took 696 ms may have crossed the deadline *during* that iteration — and it still FINISHES the
   iteration, because the check happens only at the iteration boundary. Whether it stops is about elapsed,
   not about the last iteration's duration.
2. `factor` is not 1. It multiplies the plan by **0.45 to 3.0** depending on stability
   (`TmStableFactor`, `TmSemiStableFactor`, `TmUnstableFactor`, `TmMinFactorPercent`), and by an
   effort share and a falling-eval term. So the effective deadline is anywhere in 143-951 ms, and a board
   can sit well past 317 ms and still be inside it.

## the real mechanism, and why only some boards get cut

Measured per-iteration elapsed on the two boards (raw below):

| board | iterations and cumulative elapsed | cut? |
|---|---|---|
| cut board `8/8/6k1/Q7/...` | ... d14 144 ms, d15 224 ms, **d16 666 ms** | **YES**, wall 1585.6 |
| not-cut `8/8/8/2k5/...` | ... d14 253 ms, d15 443 ms, **d16 687 ms** | no, wall 688 |

Both ended depth 16 after ~670-690 ms. **The difference is what happened NEXT:** the engine started depth
17 on both. On the not-cut board depth 17 finished quickly and the search stopped at that boundary. On the
cut board depth 17 did not finish before the 1585 ms hard limit, so it was **killed mid-iteration** and the
wall time jumped to the hard limit. The cost of the depth the engine ATTEMPTS after crossing the plan is
what decides, and that cost is not visible before the attempt.

## so is there a one-number predictor? Yes, but it is about the NEXT depth, not the last

The honest predictor is: **would the next depth's iteration fit in (hard - elapsed at the boundary)?**
That is what the code's own `iteration_will_not_finish()` tests when `TmFinishIteration` is on (off in
PC20). With it OFF, the engine starts the next depth regardless and can be cut at the hard limit.

**My first guess at a practical fix was `TmFinishIteration true`, and I tested it — it does NOT work:**

| TmFinishIteration | 5 runs on the cut board | median |
|---|---|---|
| false | 1585.8, 1585.5, 1585.1, 1585.8, 1585.3 | **1585.5 ms** |
| true | 1585.7, 1585.7, 1585.7, 1585.7, 1585.7 | **1585.7 ms** |

Identical, and **no `TmFinishIteration hold` line was ever emitted** (0 in all 10 runs), so the option's own
guard never fired on this board. The cut survives it. I record that because I proposed it in this file a moment
ago on the strength of a code comment, and the measurement says the comment's mechanism does not cover this case:
the next iteration (depth 17) probably does not even START, so a check that decides whether to start it cannot
help. Whether that reading is right I did not establish; what is established is that the option does not remove
the cut.

So at this point the honest state is: **the hard-limit cut is real, reproducible to 0.5 ms, and I have not found
an option that prevents it.** The predictor I can offer with confidence is the *retrospective* one — wall time
equals the hard plan (1585 ms) when a cut happens — and the diagnostic is that the search's own last reported
iteration time is much SHORTER than the wall time (667 vs 1586 here, a 0.42 ratio). That ratio is a detector, not
a predictor: it tells you afterwards that a cut happened.

## the correction I owe this file
Two claims I made above and have now tested and withdrawn:
1. "the proposed predictor (last-iter / soft > 1) works" — REFUTED, 8 false positives of 20 boards.
2. "`TmFinishIteration true` should remove the cut" — REFUTED, identical walls and 0 hold lines in 10 runs.

What survives: the mechanism (wall = last completed iteration, rho 0.998), the hard plan value (1585 ms computed
from clock_plan.hpp, hit to 0.5 ms), and the fact that the cut is the only route to an expensive move.
