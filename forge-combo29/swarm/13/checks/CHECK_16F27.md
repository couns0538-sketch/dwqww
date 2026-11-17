# CHECK of seat 16's S-F27 and S-F29 — seat 13, own build, own harness

## Verdict
**CONFIRMS both, and sharpens S-F27 from "3 distinct finals" to "1"** by removing the clock from the
budget. The mechanism seat 16 proposed is supported: with a fixed **node** budget instead of a clock, the
convergence is exact.

| | seat 16's measurement | my measurement |
|---|---|---|
| 10 games from ONE start | 3 distinct finals (7 of 10 identical) | **1 distinct final — all 10 identical** |
| 10 games from 10 different starts | 10 distinct finals | **10 distinct finals** |
| distinct move sequences, same start | not stated as 1 | **1** |
| distinct move sequences, varied starts | 10 | **10** |

Seat 16 attributed their 3-vs-1 residue to *"millisecond clock drift occasionally changing the depth
reached"*. My run used `go nodes 4000` rather than a clock, so that drift cannot occur — and the result
collapsed to a single distinct game. **That is direct support for their proposed mechanism**, obtained by
removing the suspected cause rather than by arguing about it.

## Method (deliberately different from theirs, so a shared bug cannot produce a shared answer)
- **Budget: fixed nodes (4,000 per move)**, not the clock — this is the key difference and it is what makes
  the mechanism testable.
- 40 plies per game, both sides searched with the same budget.
- **One fresh process per game**, so no transposition/history state can carry between games.
- Two arms: (a) 10 games from startpos; (b) 10 games from the first 10 G positions (real engine-game
  positions).
- Final positions compared on **pieces + side to move + castling + en passant** (the repetition key), with
  move counters ignored — the same rule the engine uses, and the rule I got wrong once already in this run.
- Settings: canonical PC20 from `lib/settings.py` (asserted 22 entries), Threads 1, Hash 16.

## Why this matters (and it is the practical half)
If ten self-play games from one start produce **one** game, then a self-play data set built by running many
games from a single starting position contains **one** game repeated — no matter how many games you run, or
how much compute you spend. Variety has to come from the starts:

| arm | distinct games out of 10 |
|---|---|
| one start | **1** |
| ten different starts | **10** |

That is a data-generation rule, not an engine defect: the engine is *supposed* to be deterministic at
Threads 1 with a fixed budget. Seat 16's S-F29 reached the same conclusion; my run strengthens it by showing
the same-start case is even more degenerate than they measured once the clock is out of the picture.

## Limits, stated
- **Ten games, 40 plies, 4,000 nodes.** A short and shallow budget; longer games could find divergence
  through repetition or fifty-move interactions, though with determinism at Threads 1 the logic says they
  would not.
- **Fixed-node budget only.** I did not test whether a fixed *depth* budget behaves the same, nor whether
  `ucinewgame` between games inside one process would introduce variation.
- **Final positions only.** Two games could theoretically reach the same final position by different move
  orders; I checked the move sequences too and they were identical in the same-start arm, so that is covered
  here, but it is worth stating that the final-position count alone would not have shown it.
- Not a statement about game *quality* — only about duplication.

## Beyond the finding
The "3 distinct" in seat 16's run is itself evidence *for* their drift explanation: they saw variety where
there should be none, and the variety came from a time-based budget. My fixed-node run removes it. So the
two results together are stronger than either alone: **same start + fixed budget = exactly one game; same
start + clock = a small number of games; varied starts = all different.**

## Reproduce
```
cd forge-combo29/swarm/13/checks
python3 check_16f27.py ~/b/pc/forge G_all.fens /tmp/sp 10 40 4000
```
Raw: `out_16f27/selfplay.json` (20 games with start, final position, and full move list).
