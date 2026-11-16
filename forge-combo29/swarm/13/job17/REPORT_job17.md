# REPORT_job17 — how the engine allocates its clock (answers S-F10's open question)

## What was asked
Nothing specific. S-F10 measured the engine using only ~4.1 % of the owner's 6 s clock and I recorded it
as a **question, not a defect**. This measures the allocation *function* so the question can be answered
with numbers.

## The answer: allocation is quantised by DEPTH, not proportional to the clock

| `go wtime` (ms) | wall (ms) | fraction of clock | depth | nodes |
|---|---|---|---|---|
| 4,000 | 86 | 2.2 % | 16 | 170,070 |
| 6,000 | 145 | 2.4 % | 17 | 288,912 |
| 6,000 + winc 60 | 159 | 2.7 % | 18 | 314,239 |
| 8,000 | 186 | 2.3 % | 19 | 371,311 |
| **10,000** | **790** | 7.9 % | **23** | 1,520,334 |
| **12,000** | **802** | 6.7 % | **23** | 1,520,334 |
| **15,000** | **793** | 5.3 % | **23** | 1,520,334 |
| **20,000** | **804** | 4.0 % | **23** | 1,520,334 |
| 30,000 | 1,254 | 4.2 % | 25 | 2,374,143 |

Read the middle block carefully: **from 10 s to 20 s the engine spends the same ~800 ms and reaches the
same depth 23, with the identical node count.** It is not scaling its effort with the clock; it is
finishing a depth and then declining to start the next one because that one would overrun. Then at 30 s
the next depth fits and it spends 1,254 ms.

So the fraction used *falls* as the clock grows (7.9 % at 10 s → 4.0 % at 20 s → 4.2 % at 30 s) — the
opposite of what a "use a share of the remaining time" allocator does. The allocation is
**depth-step quantised**, and the steps are large.

## `movestogo` behaves in a way worth knowing

| command | wall | fraction | depth |
|---|---|---|---|
| `wtime 6000` (no movestogo) | 145 | 2.4 % | 17 |
| `wtime 6000 movestogo 20` | 145 | 2.4 % | 17 |
| `wtime 6000 movestogo 40` | 86 | 1.4 % | 16 |
| `wtime 6000 movestogo 80` | 61 | 1.0 % | 15 |
| **`wtime 6000 movestogo 0`** | **1,755** | **29.3 %** | **26** |

`movestogo 0` — which in UCI means "no movestogo given" in some engines and "zero moves left" in others —
produces the **largest** allocation of any cell: 29.3 % of the clock, depth 26. If the owner's match
tooling ever emits `movestogo 0`, the engine will think hard rather than instantly. Worth knowing, and
worth not emitting.

## Repeatability (and the error I made getting here)
Every cell above was repeated; the allocation is reproducible to about ±1 ms and the node counts are
**identical** between repeats (e.g. `wtime 6000` gives 288,912 nodes every time). That matters because
S-F10's single measurements could otherwise have been noise.

**But my first version of this script was mislabelled, and the way it showed up is instructive.** Its
`PC20` list omitted all fourteen S14 settings, so the grid was measuring *PC6* while calling itself
PC20 — and it produced a `wtime 6000` figure of 457 ms with 882,144 nodes, roughly double the true value.
I caught it by bisecting an unexplained 2× difference: a 3-option baseline gave 215 ms, full-PC20 gave
159 ms, and neither matched the grid's 457 ms. Reading my own option list against the PC20 definition
showed the missing fourteen. After the fix the same cell gives 145 ms / 288,912 nodes, reproducibly.

The tell was the same one as in the traps note: **a number that contradicts its neighbours** (allocation
*fraction* rising then falling across a monotonic clock sweep) meant the instrument was wrong, not the
engine. A second lesson: the label in a script is not evidence about what it measured — assert the
option count (now `assert len(PC20) == 22`).

## What this means for S-F10
- S-F10's headline (median ~4 % of a 6 s clock) is **confirmed in magnitude** for this position at PC20
  (2.4–2.7 % here; S-F10's 4.1 % was a median over 80 moves on 4 different positions, so the two are
  consistent).
- S-F10 said the engine "may be leaving strength on the table". This job sharpens that into a specific,
  testable statement: **the allocator is depth-quantised, so from ~10 s to ~20 s of clock the engine runs
  the identical search.** Raising the clock from 10 s to 20 s changes nothing at all on this position.
  Whether that costs strength is still a match question — a fixed-depth-ish search is not necessarily
  worse, it is simply not using the time it is given.

## Findings
- S-F19: clock allocation on the PC build under PC20 (Threads 1, Hash 16) is **depth-step quantised, not
  proportional**: `wtime` 10,000 / 12,000 / 15,000 / 20,000 all give the identical search (depth 23,
  1,520,334 nodes, ~800 ms), while 8,000 gives depth 19 and 30,000 gives depth 25; the fraction of the
  clock used therefore FALLS as the clock grows (7.9 % at 10 s → 4.0 % at 20 s). Also: `movestogo 0`
  yields the largest allocation of any cell (29.3 % of a 6 s clock, depth 26), versus 2.4 % with
  movestogo omitted. Reproducible to ±1 ms with identical node counts across repeats.
  Reproduce: `cd forge-combo29/swarm/13/job17 && python3 timealloc.py ~/b/pc/forge /tmp/ta`.

## Suspicions, not proven
- The depth step at ~10 s may be exactly where depth 23 crosses the soft limit on this position; a
  different position would step at different clocks. I tested one middlegame position for the sweep plus
  one tactical position at a single setting (285 ms, 4.8 %, so a different allocation — consistent with
  quantisation, not with a fixed share).
- Whether the quantisation costs match strength. Not measured; a match would settle it, and another seat
  has specced one.

## What I did NOT do
- No match, no strength claim.
- Did not map the quantisation over many positions to find how the step points vary.
- Did not test `movestogo` values other than 0/20/40/80.

## What I am NOT sure about
- One position drives the sweep, so the specific depths (17/19/23/25) are position-specific; the *shape*
  (equal searches across a wide clock range) is what I claim.
- My own mislabelled first run is recorded above; anyone reading `out/` or `out2/` should know those are
  PC6 data mislabelled as PC20, and `out3/` plus the repeat runs are the corrected PC20 data.

## Files
`timealloc.py` (now asserts PC20 has 22 entries), `out3/timealloc.json` (corrected PC20 grid),
`out/` and `out2/` (the mislabelled PC6 runs, kept deliberately), `stamps.txt`.

## Last command output

```
$ ls
out
out2
out3
REPORT_job17.md
stamps.txt
timealloc.py
```
