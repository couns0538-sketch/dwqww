# The owner's REAL match path under MultiPV — and a second, separate MultiPV defect

FABLE_TO_swarm_6 names what the PC actually does: PC build, PC20, Threads 1, Hash 16, `go softnodes 2000`
(self-play), `go nodes` 20000/50000/250000 (matches), clock 6 s + 0.06 (strength matches), positions from real
games. The question set for me: **do those commands use MultiPV at all, and what is the safe setting?**

## first, the direct answer: PC20 does not set MultiPV
The 22 option names PC20 sends contain **no MultiPV**, and the engine advertises `MultiPV ... default 1`. So on a
fresh process the owner's path runs at **MultiPV 1**, which is the safe setting — the S-F7 collapse needs
MultiPV > 1 and cannot reach it. The risk is only a GUI that leaves a value behind in a long-lived process.

## but measuring it turned up a SECOND MultiPV defect, independent of S-F7
`match_path.py` — PC20, Threads 1, Hash 16, OwnBook false, 3 runs per cell, three real game positions, the
owner's five commands, at MultiPV default / 2 / 4 / 8. Median of 3 runs (`raw_rows.txt`):

| command | MPV default | MPV 2 | MPV 4 | MPV 8 |
|---|---|---|---|---|
| `go softnodes 2000` | d7 / 3278 / 3 ms | d3 / 2412 / 12 ms | d2 / 3049 / 14 ms | **d1** / 8000 / 19 ms |
| `go nodes 20000` | d9 / 15298 / 13 ms | d8 / 10978 / 24 ms | d7 / 3278 / 35 ms | **d3** / 1010 / 30 ms |
| `go nodes 50000` | d12 / 42519 / 30 ms | d10 / 22041 / 42 ms | d8 / 21380 / 51 ms | **d5** / 6988 / 66 ms |
| `go nodes 250000` | d15 / 191905 / 146 ms | d14 / 112880 / 162 ms | d12 / 74501 / 173 ms | **d10** / 35999 / 192 ms |
| `go wtime 6000 btime 6000 winc 60 binc 60` | d19 / 683500 / 392 ms | d16 / 436198 / 436 ms | d12 / 149584 / 214 ms | **d10** / 130338 / 241 ms |

**A node-budget search at MultiPV 8 reaches 3-6 plies less depth than at MultiPV 1, and the wall time barely
moves.** That is a different mechanism from S-F7: there is no large Hash here (Hash 16 throughout), so nothing is
being cleared expensively. The budget is being SPLIT across the eight PV lines.

Traced at `go nodes 20000`, MultiPV 8 on the game_mid2 board:

```
MultiPV 1  depth 9: nodes 11998, one line
MultiPV 8  depth 6, eight lines: nodes 1078 / 2310 / 3942 / 4804 / 6161 / 7717 / ... (cumulative per line)
```

Eight lines are emitted and the node total is consumed producing all eight, so the PRIMARY line only reaches
depth 6 where the single-line search reached depth 9. On a fixed node budget, MultiPV buys breadth at the direct
cost of the depth of the line that gets played.

## S-F9 — a fixed NODE budget is diluted by MultiPV, unlike the large-Hash case
`go nodes N` (and `go softnodes N`) at MultiPV M spends the same N nodes on M lines, so the first line reaches
far less depth; measured 3-6 plies less at M=8 across N = 20000 / 50000 / 250000 and on the clock. Present on the
PC build under PC20 with Threads 1 and Hash 16, so it is NOT the S-F7 table-clear defect. **Not a defect in the
"wrong move" sense** — it is what a node budget means — but it is a trap for anyone benchmarking or matching with
MultiPV left above 1: the engine silently plays a 3-6 ply shallower search for the same "20000 nodes".

## the safe setting, in file 6's own terms
- **Matches (`go nodes 20000/50000/250000`) and strength matches (clock 6 s + 0.06): MultiPV 1.** PC20 does not
  set it and the default is 1, so the owner's path is safe as long as the GUI does not change it.
- **Self-play (`go softnodes 2000`): MultiPV 1.** At MultiPV 8 that command reached **depth 1** — the 2,000-node
  budget cannot support eight lines at all, so the training label would come from a one-ply search.
- **The rule for any harness the owner builds**: if you set `MultiPV > 1`, you must also raise `nodes` roughly
  in proportion to M to keep the first line's depth, AND keep `Hash` at 16-64 MB (S-F7). Both knobs are unsafe
  with MultiPV; Hash 16 + MultiPV 1 is the configuration every measured command above is fastest and deepest at.

## determinism note, stated because it is a caveat not a finding
Every cell was deterministic across 3 runs EXCEPT one: `go wtime 6000 btime 6000 winc 60 binc 60`, MultiPV
default, board game_mid2 (det=False). That is a CLOCKED search, where the stop point is wall time and therefore
not reproducible by nature — file 6's own rule says a multi-thread defect needs a spread test, and seat 04's
finding covers score spread at threads > 1. This is Threads 1, so the variant is clock jitter, not a thread
issue; I record it rather than hide it.

---

# IS THE DILUTION PROPORTIONAL TO MultiPV? — measured, and the answer is more specific

`dilution.py` — `go nodes 20000`, PC20, Threads 1, Hash 16, one game position, MultiPV 1 / 2 / 4 / 8, 3 runs per
cell, all cells deterministic. Raw `dilution.json`.

Numbers read straight off the engine's own lines: at a given depth each `info ... multipv K ... nodes V` line
carries V cumulative for line K, so line 1's V is the primary line's own cost and the LAST line's V is the whole
iteration's total.

| MultiPV | depths with a COMPLETE line set | final depth | primary line nodes | share of N | 1/M | share / (1/M) |
|---|---|---|---|---|---|---|
| 1 | — | 11 | 19832 | 0.992 | 1.000 | 0.99 |
| 2 | — | 10 | 9155 | 0.458 | 0.500 | 0.92 |
| 4 | 1-7 | 8 | 2595 | 0.130 | 0.250 | **0.52** |
| 8 | 1-6 | 7 | 2671 | 0.134 | 0.125 | 1.07 |

A naive reading of this table says "MultiPV 4 is worse than 1/M and MultiPV 8 is fine", which is nonsense. The
reason is visible in the per-depth line counts:

```
MultiPV 4: depths 1-7 emit all 4 lines; depth 8 emits only 3  (lines 1,2,3)
MultiPV 8: depths 1-6 emit all 8 lines; depth 7 emits only 2  (lines 1,2)
```

**The budget does not divide by M. It is spent line by line, per depth, and when N runs out it stops in the
MIDDLE of an iteration.** So the "primary line nodes" I measured at the final depth is a partially-completed
iteration's cost, not a share. That is why the ratios look irregular: they are measuring where the guillotine fell,
not a division.

## the real answer to the question asked
The dilution is **NOT** proportional to MultiPV, and it is not "worse than 1/M" either — that framing assumes the
budget is divided, and it is not. What actually happens:

**Each depth costs about M times as much as at MultiPV 1, so the number of COMPLETE depths falls roughly like
log: MultiPV 1 reached depth 11 on 20,000 nodes, MultiPV 4 completed depth 7, MultiPV 8 completed depth 6.** After
the budget is exhausted the engine stops part-way through the next iteration's line list, which is why the final
emitted depth has an incomplete set and why its node numbers wander.

## what that means for the guidance (and it makes the rule simpler, not more complex)
The rule asked for is confirmed and does not need a proportionality caveat: **a fixed node budget and MultiPV above
1 are incompatible by construction, because the budget bounds the whole ITERATION over all lines, so every extra
line multiplies the cost of a depth.** The practical consequences:

- **MultiPV 1 gives the deepest search for a given `nodes`.** 20,000 nodes -> depth 11. That is the owner's match
  and self-play configuration.
- **MultiPV 4 on the same budget reaches depth 7**, four plies shallower, and **does not even finish its last
  iteration** (3 of 4 lines emitted).
- **MultiPV 8 reaches depth 6**, and its last iteration emits 2 of 8 lines — so a GUI reading `multipv 3..8` at
  the final depth would be reading lines that were never produced at that depth at all.

That last point is the practical trap: at MultiPV 8 with a tight budget the engine can stop with only the FIRST
TWO of the eight lines for the depth it reports, so a GUI that expects eight lines at the deepest depth sees six
stale ones.

## S-F10 — a node budget cuts an iteration mid-line-set, so the final depth can emit FEWER lines than MultiPV
`go nodes 20000`, MultiPV 8: depths 1-6 emit all 8 lines, depth 7 emits **2** (`multipv 1` and `multipv 2`), and
that incomplete depth is the one reported. MultiPV 4 the same at depth 8 (3 of 4). Not a wrong-move defect, but a
real UCI-surface consequence: the last reported depth is not a complete MultiPV set.
