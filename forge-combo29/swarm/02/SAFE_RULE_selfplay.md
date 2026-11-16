# The safe rule for the owner's self-play and matches, in file 6's own terms

File 6 names what the PC does: PC build, **PC20**, **Threads 1**, **Hash 16**, `go softnodes 2000` (self-play),
`go nodes` 20000/50000/250000 (matches), clock `6 s + 0.06` (strength matches), positions from real games.

## the rule
**MultiPV 1, always — a fixed node budget and multiple PV lines are incompatible by construction.**

Why, in one line each:
- `go softnodes N` and `go nodes N` bound the WHOLE iteration across all M lines, so every extra line multiplies
  what a depth costs and the search reaches fewer plies for the same N. Measured on 20,000 nodes: MultiPV 1 ->
  **depth 11**, MultiPV 4 -> **depth 7**, MultiPV 8 -> **depth 6**. (S-F9)
- At MultiPV 8 the budget ran out MID-ITERATION: depths 1-6 emitted all 8 lines, depth 7 emitted only **2**, and
  depth 7 is the one reported. So a self-play label taken at MultiPV 8 can be a **depth-6-or-7 search**, and on
  `softnodes 2000` it was **depth 1**. (S-F10, and the softnodes line below)

| command | MultiPV 1 (the owner's path) | MultiPV 8 |
|---|---|---|
| `go softnodes 2000` (self-play) | depth 7 | **depth 1** |
| `go nodes 20000` (match) | depth 9-11 | depth 3-7 |
| `go nodes 50000` | depth 12 | depth 5 |
| `go nodes 250000` | depth 15 | depth 10 |
| clock 6 s + 0.06 (strength) | depth 19 | depth 10 |

## you are already safe, and this is why
**PC20 does not set MultiPV.** The 22 option names it sends contain no MultiPV, and the engine advertises
`MultiPV ... default 1`. So every command above runs at **MultiPV 1** on a fresh process, which is the deepest and
the safest configuration, and neither S-F7 (the large-Hash table-clear collapse) nor S-F9/S-F10 (budget dilution)
can reach the owner's path.

**The one way this breaks is a GUI leaving a value behind.** MultiPV is a per-process option: a GUI that sets it
for an analysis pane and then starts a match in the SAME engine process carries it into the match. That is the only
exposure, and it needs no engine change to avoid — send `setoption name MultiPV value 1` before any match or
self-play run, or start a fresh process per game.

## the two knobs, side by side
| knob | safe for the owner's path | why |
|---|---|---|
| **MultiPV** | **must be 1** | a node budget is spent across all lines, so M > 1 costs depth directly (S-F9), and can truncate the reported depth's line set (S-F10) |
| **Hash** | **16-64 MB is fine, and any size is fine at MultiPV 1** | Hash size alone costs nothing (2-3 ms across 16..2048 MB); the S-F7 collapse needs MultiPV > 1 AND a large Hash together |
| **Threads** | **1** (the PC plays one) | scores above Threads 1 are not reproducible (seat 04, and file 6's own rule) |

So the complete safe configuration, stated as the owner would send it:

```
setoption name Threads value 1
setoption name Hash value 16
setoption name MultiPV value 1        # explicit, even though it is the default
<the 22 PC20 options>
```

Everything else in PC20 is safe: I tested all 22 options plus MultiPV at min/max/min-1/max+1/word/none on the PC
build (603 cases, job3_pc) and found 0 crashes, 0 sanitizer lines, 0 illegal moves, 0 refused values other than the
intended `invalid value` answers.
