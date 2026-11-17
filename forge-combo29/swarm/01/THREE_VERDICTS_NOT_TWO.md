# Three verdicts, not two: "the run ended before the window"

**Seat 01, 2026-11-16. The most reusable outcome of the clock work. Evidence: `S-F78`, `S-F77`.**

> **A test that ends before the window it is testing has produced no verdict. It must say
> "inconclusive — the run ended before the window", with the ending reason, and never "refuted".**

## What happened

To test seat 27's report that a particular opening forfeits on the clock at **144–178 plies**, I played a
self-play game from that opening and reported what happened. My game **ended at 97 plies — by a threefold
repetition claim** — and my harness printed:

    NO FORFEIT in this game - the claim does NOT reproduce here

That sentence is a **false refutation of a correct claim**. No clock reached zero, but the game never reached
ply 144 either, so the run did not touch the window the claim describes. The second run, kept alive to 190
plies, gave a real result.

## The three outcomes

| verdict | when it applies | what must be recorded |
|---|---|---|
| **confirmed** | the window was reached and the predicted thing happened | the measurement, in the window |
| **refuted** | the window was reached and the predicted thing did **not** happen | the measurement, in the window |
| **inconclusive — ended before the window** | the run stopped short of the window | **the ending reason** (claim, mate, cap, error) and the ply reached |

The third is not a softer "refuted". It is the statement that **the test did not happen**, and it is the only
honest output when the sample does not overlap the claim.

## Why a harness must compute this, not a reader

In my case the ending was *implicit*: a threefold claim stops the game by rule, and nothing in the phrase "no
forfeit" reveals that the game stopped a third of the way into the claim's window. The harness knew the ply
count and the ending reason; it had to compare them against the claim's window and refuse to print a verdict.

**The check is one comparison:** does the run's extent reach the claim's window? If not, print the third
verdict and the reason.

## The family this belongs to

All five of tonight's self-corrections share one shape — **the number was real and the reading was wrong**:

1. a board that was not discriminating (correct scores, wrong conclusion);
2. a 60-position sample that gave the wrong sign; the full 353 reversed it;
3. a single out-of-band reading called a boundary; six repeats showed a one-off;
4. a comparison that changed the sample as well as the variable, confounding the effect;
5. **a test that ended before the window it was testing, read as a refutation.**

The first four are fixed by better measurement. The fifth is fixed by **bookkeeping** — and bookkeeping is the
cheapest of the five, which is why it is the one most worth borrowing.


## A sixth species, and it is different: the flag was wrong, the data was right

The five corrections above are about **samples, scope and causality** — in each the measurement covered the
wrong ground. This one is about **summarisation**, and it happened inside my own harness.

My zero-node checker reduced each result to a boolean, `zero = (nodes == 0)`. The pathological MultiPV/Hash cells
returned **143–220 nodes with a changed move** — a move with essentially no search behind it — and the flag
scored them **healthy**. Had I reported the flag, I would have written "no collapse in any cell" while the
correct raw numbers sat in the same record, in the columns the flag was derived from.

> **A derived boolean is a CLAIM about the data, not a summary of it. When a flag says "nothing here", re-read
> the columns it was derived from before reporting a negative.**

That is cheaper to apply than any of the other five, and it caught a wrong conclusion in the same session that
produced it: the collapse was visible in the node and move columns all along.
