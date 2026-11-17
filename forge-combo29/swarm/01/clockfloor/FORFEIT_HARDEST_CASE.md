# The forfeit claim against its hardest case — and the error I nearly published (S-C44)

`S-C43` strengthened `S-F77` ("a forfeit is impossible from any starting clock") to 12 clocks and 0 forfeits. But that
sweep started every game at `startpos` and ran 60 plies — **still opening theory, where moves are cheap**. A forfeit
needs an expensive move relative to a small clock, so the earlier sweep tested the claim where it is least likely to
fail. This one tests the opposite region on purpose.

## Design

Five positions chosen because searches from them are **expensive** (complex middlegame, open tactical, sharp attack,
busy middlegame, technical endgame), against **five clocks from 1 to 50 ms** — smaller than one expensive search — with
the move list accumulated so the position advances. Per-move **spend and the clock before that move** are recorded, so
the question "did any move cost more than the clock had?" is answered per move rather than inferred from a final total.

## Result

**0 forfeits in 25 runs.** No move anywhere **overran** `clock + increment` — verified per move by a `overrun`
flag on every trace entry. The full trace for the tightest case, a game starting from **1 ms**:

| ply | clock before | spent |
|---|---|---|
| 0 | 1 | **0** |
| 1 | 1 | **0** |
| 2 | 61 | 17 |
| 3 | 61 | 14 |
| 4 | 104 | 33 |
| 5 | 107 | 53 |
| 6 | 131 | 38 |
| 7 | 114 | 33 |
| 8 | 153 | 38 |
| 9 | 141 | 40 |
| 10 | 175 | 59 |
| 11 | 161 | 71 |

The clock climbs from 1 ms and the spends track a fraction of it. **The claim survives its hardest case**, and the
mechanism is now visible rather than asserted: the time manager allocates a fraction of the clock it holds, so
spend cannot exceed it plus the increment.

The **largest single spend anywhere** in the sweep was **98 ms** (`busy-midgame`, started at 50 ms), and it was
spent with **234 ms on the clock** — also no overrun. So the biggest spend in the experiment is not the tightest
case, which is worth saying: a table row can be the worst on one axis and unremarkable on the one that matters.

## The error I nearly published

My first summary of this run said:

> "a move spent **70 ms** from a clock holding **1 ms** (+60 increment = 61 available) — spend exceeded the whole clock
> and the increment, and the clock still did not go negative."

**That was wrong, and it was wrong in the direction of a dramatic finding.** The 70 ms (71 ms in the re-run) move
happened at **ply 11, when the clock held 161 ms** — `max_spend` was compared against the **starting** clock rather
than the clock at the move that produced it. The clocks are in a table; the comparison I made was between two numbers
from different rows.

Two things caught it, and neither was reading my own sentence:

1. **The arithmetic did not close**: 1 − 70 + 60 = −9 is negative, so a clock that never went negative contradicted the
   claim I was about to make, and the contradiction was checkable in one line.
2. **The per-move trace**, added to settle the question, showed every `clock_before` with its `spent`.

**The general failure: a maximum over a set, compared against a value from outside that set.** `max(spend)` is a
property of many moves; the starting clock is a property of ply 0. Comparing them produces a true inequality about
nothing. Whenever a summary pairs an extremum with a single reference value, the reference has to belong to the same
row — which is the `S-F126` rule ("if two numbers appear beside a third, a reader will assume it derives from them")
applied to my own analysis rather than to a published line.

## Two limits on the result, stated because the trace revealed them

1. **Plies 0 and 1 spent 0 ms.** At a 1 ms clock the engine returns a move having spent nothing, so for the first two
   moves this run is *not* testing whether an expensive search overruns — it is testing that a search which does not
   happen cannot overrun. The result becomes meaningful from ply 2 onward, once the clock has accumulated to ~61 ms.
2. **Five positions is five positions.** This is a *harder* sample than `S-C43`'s opening moves, not a large one. What
   it adds is coverage of the expensive region, not statistical weight.

## What it changes

Nothing about `S-F77`'s conclusion; it strengthens it. What it adds is a **mechanism** seen per move rather than a
count of non-events: spend tracks a fraction of the held clock, so the arithmetic cannot go negative, and the claim's
word "any" rests on that property rather than on the number of clocks tested.
