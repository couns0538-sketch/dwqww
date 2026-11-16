# S-F27 IS WITHDRAWN ENTIRELY. There is no illegal-PV defect. The error was mine, in the parser.

I have to withdraw the last piece of S-F27 as well. There is no defect at `go nodes 20000` - not a wrong final
answer (S-C9 already corrected that) and not an illegal move in an intermediate PV either. Both were my errors.

## What happened, exactly

The scope sweep (`illegal_pv_scope.py`, 3 mate-rich boards x 10 command settings = 30 cells) found **zero**
intermediate lines with an illegal PV, including on the very board where I had reported one:

| board | go nodes 1000/5000/10000/20000/50000/250000 | go depth 8/10/12/16 | lines with illegal PV |
|---|---|---|---|
| `8/8/1p6/8/p3p3/8/2Kpk3/8 w` | all | all | **0** |
| `8/8/7Q/8/8/6k1/K7/R7 w` | all | all | **0** |
| `8/8/8/4k3/8/8/8/K1R5 w` | all | all | **0** |

So I re-replayed the depth-8 PV move by move, taking it verbatim from the engine's output. **All 12 plies are
legal.** Ply 3 is `b1a2` (the white king steps aside) - but in `S-F27_CORRECTION.md` I had written the move as
`b2a2`, reconstructed from memory rather than copied, and then "verified" that my own wrong string was illegal.

That is the whole defect: I typed a move wrong and then proved my typo was illegal. The engine was right
throughout.

## Final truth about `go nodes 20000` on this board

```
depth 7   cp -2515
depth 8   mate -7,  12-ply PV, all legal   (12 < 14, so an unfinished mate line)
depth 9   mate -8,  12-ply PV
depth 10  mate -8,  13-ply PV
depth 11  mate -7,  14-ply PV, legal, verified CHECKMATE at exactly 2*7 = 14 plies   <- final answer, CORRECT
```
The intermediate mate lines have PVs shorter than the mate distance, which is ordinary horizon behaviour for a
mate that is still being resolved (seat 05 measured the same on 27 boards and file 6 reclassified it). The final
answer is correct. Nothing here is a fault.

## The one fact worth keeping from this thread

`FORGE_FIX_ABORT_PUBLISH` **is** compiled out by default (src/search.cpp:76-77) and its publish block is gated on
`!stopped_by_nodes_`. That is a true statement about the code, verified by reading it, and it is unaffected by my
parser error. It is simply not implicated in any observed wrong answer.

## Five errors tonight, all recorded
1. clock-99 zero wrongly called correct (withdrawn, `debug/CORRECTION.md`)
2. `h6h5` hand-written as a pawn push when it is a capture (`debug/COST_FINAL.md`)
3. a check compared a regex match to `"cp 0"` when the regex returns `"score cp 0"` (`check_05F14/`)
4. S-F27 headlined as a match-path defect when the final answer is correct (`pcpath/EXPOSURE_FINAL.md`)
5. S-C9's illegal-PV claim, which was my own typo replayed back at me (this file)

The common cause is the same every time: I reconstruct data instead of copying it. The rule that would have
prevented all five is the one I wrote in my own harness notes and then broke - the PV must be taken from the
engine's line, never retyped. The scope sweep is what caught it, because it re-derived every PV from the raw
output instead of from my notes.
