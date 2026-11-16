# Does the clock mode diverge from the node mode? NO — the apparent divergence was EFFORT, not mode

The question: the owner's clock (`go movetime`) is a third mode nobody had compared against `go nodes` on
ambiguous positions. If they diverge, mixing match data (`go nodes`) with strength data (the clock) is unsafe
move-for-move.

## first pass: a divergence appeared, and it was confounded
I calibrated `go nodes 50000` against several movetimes on a neutral board, chose the closest (50 ms), and compared
on the six ambiguous positions from S-C10. **1 of 6 differed** (`gap9`: `f1d3` under nodes, `f1b5` under clock) —
but the median clock-mode node count was **1.74x** the node mode's, so the comparison was NOT at matched effort and
the divergence could not be attributed to the mode. I report that rather than claiming the finding.

## the isolating test on the one diverging board
`r2qk2r/ppp1bppp/2n1bn2/3p4/3P4/2N1BN2/PPPB1PPP/R2QKB1R w KQkq - 0 8`

| command | bestmove | nodes | depth |
|---|---|---|---|
| `go nodes 28417` | f1d3 | 28417 | 12 |
| `go nodes 30000` | f1d3 | 28417 | 12 |
| `go nodes 50000` | f1d3 | 28417 | 12 |
| `go nodes 66000` | f1d3 | 28417 | 12 |
| `go movetime 30` | f1d3 | 28417 | 12 |
| `go movetime 40` | f1d3 | 28417 | 12 |
| **`go movetime 50`** | **f1b5** | **66246** | **13** |
| `go depth 13` | f1b5 | 66246 | 13 |
| **`go nodes 67000`** | **f1b5** | **66246** | **13** |
| `go nodes 70000` | f1b5 | 66246 | 13 |

**Read the bottom three rows: `go depth 13`, `go nodes 67000` and `go movetime 50` all give `f1b5` at 66,246
nodes and depth 13.** The clock mode and the node mode agree perfectly once they reach the same depth. The earlier
"divergence" was the node budget simply stopping one ply earlier (depth 12 vs 13) on a position where the two
candidate moves are 9 cp apart.

So: **the clock mode and the node mode do NOT diverge at matched effort; the difference was the number of plies
searched.** `go nodes 50000` exhausted its budget during depth 12 (28,417 nodes reported — it never reached the
2-ply-deep total), while `go movetime 50` had time to finish depth 13.

## this is the same lesson as S-F10, from the other direction
S-F10 established that a nominal node budget is not a fixed effort: the search stops at an iteration boundary.
Here the consequence is sharper — **`go nodes 50000` and `go movetime 50` are not "the same effort" on a given
board, and the gap between them is a whole iteration, which is exactly enough to change the move when two moves are
within 9 cp.** The right way to compare the modes is to match the DEPTH they reach, not the nominal limit.

## verdict
- **No mode-level divergence between the clock and the node mode** was found: at depth 13 all three commands
  (`depth`, `nodes`, `movetime`) return the same move on the board that looked like a counter-example.
- The one apparent disagreement in my first pass was a **depth difference of one ply**, caused by the node budget
  being an iteration-boundary stop.
- **Practical rule for the owner, and it is reassuring:** mixing clock play and node-budgeted matches is safer than
  mixing `go nodes` with `go softnodes` (which genuinely differ, S-C10/S-C12), because the clock and node modes
  agree whenever they reach the same depth. What must NOT be compared is results at different depths.

## scope
Six ambiguous positions, one round per mode, plus the depth-matched isolation on the single counter-example. I did
not build a large sample, so this establishes the mechanism and the rule, not a per-position rate.
