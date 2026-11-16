# S-F27 CORRECTED: the defect is an ILLEGAL MOVE IN AN INTERMEDIATE PV, and it is a display fault

I reported S-F27 as "the final answer at `go nodes 20000` is a wrong mate score with a non-mate PV". Reading the
raw output line by line instead of trusting my parser, that is **not right**, and I am correcting it.

## What is actually true (PC r15/PC20, Threads 1, Hash 16, board `8/8/1p6/8/p3p3/8/2Kpk3/8 w`)

`go nodes 20000` emits, in order (3 runs, identical):

```
depth 7  score cp -2515   pv 11 plies
depth 8  score mate -7    pv 12 plies  <- 2 of those plies are ILLEGAL (b2a2 cannot be played), and it is not mate
depth 9  score mate -8    pv 12 plies
depth 10 score mate -8    pv 13 plies
depth 11 score mate -7    pv 14 plies  <- legal and a REAL CHECKMATE at exactly the claimed distance
bestmove c2b1
```

Played out with python-chess:
- depth 8's PV: 12 plies, and the move `b2a2` is **illegal** at that point in the line. So that PV cannot be
  replayed at all.
- depth 11's PV (the LAST line, and the one a GUI uses for the final display): 14 plies, legal throughout, and
  `is_checkmate = True` - exactly right for `mate -7` (2*7 = 14 plies).

## So the corrected finding

1. **The final score and PV are CORRECT** (`mate -7`, 14 plies, real mate). My S-F27 headline was wrong.
2. **The real defect is narrower: an intermediate `info` line carries an ILLEGAL move in its PV.** That breaks any
   consumer that reads PVs as they stream (a GUI drawing the line, a training pipeline that parses every info
   line, a test that validates PVs) - the depth-8 line cannot be replayed.
3. The intermediate line also claims `mate -7` at depth 8 where the finished depth-8 search had no mate (depth 7
   was cp -2515), so that line's score is not the finished-iteration score either. That IS the partial-iteration
   publish the `FORGE_FIX_ABORT_PUBLISH` guard exists to prevent - and the guard is **compiled out by default**
   (`#define FORGE_FIX_ABORT_PUBLISH 0`, src/search.cpp:76-77), with its own comment saying it was measured and
   "is not a repair".

## The rate number (S-F28) needs the same caveat

My S-F28 measured "2 of 14 mate scores wrong at `go nodes 20000`" by taking the LAST mate-scored line. On this
board the last mate line is correct, so the rate was computed over a different board set and I have not re-derived
it with the line-by-line method. Until I do, **S-F28's 14.3% should be read as "14.3% of my sampled boards had at
least one mate-scored info line that fails a play-out", not "14.3% of final answers are wrong".** That distinction
matters and I am not going to let the bigger number stand unqualified.

## Why I am recording this rather than quietly editing

This is the fourth error of the same species tonight: a conclusion that did not match my own evidence. The
pattern is consistent - I trust a parse, then find the raw output says something narrower. The fix that has
worked every time is to read the raw lines and play them out, which is what this file does.
