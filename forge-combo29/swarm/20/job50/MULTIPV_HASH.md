# seat 20 — job 50: the MultiPV x Hash collapse CONFIRMED on the PC build, and it changes the MOVE

Independent confirmation of seat 02's S-F7b/S-F7c, which the owner asked me to keep live because it is a strength
collapse in analysis. PC r15, **Threads 1**, `go wtime 5000 btime 5000`, PC20-style options, 3 runs per cell,
fresh process each. Position: `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1`.

| Hash | MultiPV | depths (3 runs) | wall ms | moves | verdict |
|---|---|---|---|---|---|
| 16 | 1 | 17, 17, 17 | 148–151 | `g7g6` | **OK** |
| 16 | 3 | 14, 14, 14 | 270–275 | `g7g6` | OK |
| 16 | 8 | 12, 12, 12 | 331–338 | `g7g6` | OK |
| 256 | 1 | 17, 17, 16 | 106–168 | `g7g6` | **OK** |
| **256** | **3** | **2, 5, 7** | 237–270 | **`f6d7`, `g7g6`** | **COLLAPSED** |
| **256** | **8** | **2, 2, 2** | 260–298 | **`f6d7`** | **COLLAPSED** |
| 2048 | 1 | 16, 16, 16 | 111–115 | `g7g6` | **OK** |
| **2048** | **3** | **1, 1, 1** | 1,125–1,214 | **`b8a8`** | **COLLAPSED** |
| **2048** | **8** | **1, 1, 1** | 1,246–1,315 | **`b8a8`** | **COLLAPSED** |

## Confirmed exactly as they describe
- **MultiPV 1 is safe at every Hash size** (depth 16–17 at 16, 256 and 2048 MB).
- **Hash 16 MB is safe at MultiPV 8** (depth 12).
- **Hash 256 MB is ruined at MultiPV 3** (depth 2–7 against 17).
- **Hash 2048 MB is depth 1 from MultiPV 3 upward**, on all three runs.
- The wall time is the tell: at Hash 2048 the search burns **1.1–1.3 s** to reach depth 1, i.e. it spends the budget
  clearing/initialising rather than searching — matching their "per-extra-line `tt.clear()`" cause.

## Beyond their line: the MOVE changes, so this is a strength loss, not a rendering issue
On the same position the healthy cells all play **`g7g6`**. The collapsed cells play:
- Hash 256 / MultiPV 8 → **`f6d7`** in all 3 runs;
- Hash 2048 / MultiPV 3 and 8 → **`b8a8`** in all 3 runs.

A depth-1 move on a middlegame position is a different, worse move, and it is *reproducibly* worse (3/3 each). So a
user who sets MultiPV 8 with a large Hash does not merely get less analysis depth — they get a **different root
move**, and if that is the engine's analysis output it is a wrong recommendation, not just a shallow one.

## The one cell that is NOT clean, stated plainly
**Hash 256 / MultiPV 3** gave depths 2, 5, 7 across three runs with a move that varied (`f6d7` twice, `g7g6` once).
So that cell is both collapsed AND unstable — worth knowing, because seat 02's table quotes it as a single depth (8).
My reading: it is on the edge, and the honest description is "collapsed and erratic", not "depth 8".

## Practical advice (same as theirs, now independently supported)
- **MultiPV > 1 with a large Hash is unsafe.** Keep Hash ≤ 16 MB when using MultiPV, or keep MultiPV at 1 when
  Hash is large. Neither combination collapses in any cell I measured.
- This affects **analysis**, not the PC's matches (which use MultiPV 1).

## Limits
- One position. Seat 02's grid used a clock too; I matched their `go wtime 5000` form.
- 3 runs per cell; the collapsed cells were unanimous except Hash 256 / MultiPV 3.
- The PC's own net would change node counts, not the mechanism.
- `Threads 1` throughout.
