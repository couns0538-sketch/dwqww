# REPORT_job7 — the PC's real search path: `go nodes` at the three match budgets

## What was asked
The coordinator's job 2: the PC path per FABLE file 6, with my own limit stated — 12 positions from G
rather than the owner's match games. File 6's path is: PC build, PC20, Threads 1, Hash 16,
`go softnodes 2000`, `go nodes` 20000 / 50000 / 250000, clock 6 s + 0.06 s, positions from real games.

softnodes was job 5. This job covers **`go nodes`** at all three match budgets plus 2,000.

**LIMIT, stated up front:** my positions are 12 from the **G set** (positions from engine games),
**not the owner's own match games**, which I do not have. This is "real-game-like", not "his games".
The clock (6 s + 0.06 s) was not exercised — these are node budgets, which is what his matches use for
the node-mode games.

## The answer
**48 runs, 12 positions × 4 budgets, all clean on the properties I can test:**

| property | result |
|---|---|
| deterministic (each run repeated in a separate fresh process) | **48/48 identical** — depth, nodes, cp/mate, bestmove |
| `go nodes N` respects its budget (hard cap) | **48/48** — never spent more than N; worst case was 96 nodes *under* |
| bestmove legal in its position | **48/48** (control shows an illegal move is caught) |

That is the opposite of `go softnodes` (job 5), and it is the expected design difference: softnodes
stops at the end of the depth it is in and overshoots badly, while `go nodes` is a hard limit and
truncates. **So for match play the node budget is honest; for self-play the softnodes budget is not.**

## Depth bought per budget (the useful engineering number)

| N | depths across the 12 positions | median | spread | score types |
|---|---|---|---|---|
| 2,000 | 6,7,6,5,6,7,5,7,5,6,6,7 | 6 | 2 | all cp |
| 20,000 | 11,10,9,9,11,12,8,12,9,10,9,10 | 10 | 4 | all cp |
| 50,000 | 12,12,10,12,13,13,10,13,11,13,12,13 | 12 | 3 | all cp |
| 250,000 | 16,17,16,14,17,16,15,16,17,15,15,17 | 16 | 3 | all cp |

Budget utilisation (nodes spent / N): median 0.68 at N=2,000 rising to **0.83 at N=250,000**, with a
maximum of 0.98–0.99. So the budget is well used but never exceeded, and the *fraction* used rises
with N — at small budgets the engine often stops well short because it finishes a depth early.

## One thing I checked rather than assumed
Position 7's score moves sharply at the top budget: cp −257 / −256 / −284 at the three lower budgets,
then **cp −1364 at 250,000**. A 1,000-centipawn jump that appears only at the deepest search is
exactly the shape of a bug, so I verified the principal variation instead of reporting it:

```
g5h5 e5f6 g3g4 f5f4 h5h6 f4f3 g4g5 f6f5 h6g7 f3f2 g7f7 f2f1q g5g6 ...
```
Every ply is legal in python-chess, and the line ends with black promoting to a queen on f1. The
position `8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1` is a king-and-pawns ending where black's f-pawn
runs; the deeper search is **discovering a real promotion**, i.e. the shallower scores were optimistic.
That is correct search behaviour, not a defect, and I am recording the verification rather than the
alarm.

## How sure
High for the three zeros: `CONTROL_PCPATH.md` shows the same comparison functions flag a 1-node
difference, a 1-depth difference, a 1-centipawn difference, a different bestmove, a mate-vs-cp change
and a planted illegal move, while not flagging identical runs or a legal move.

## Settings and build
PC r15, sha256 `068f0927...`, `-DFORGE_MATE_ALPHA_GUARD=1`. PC20 in full (Threads 1, Hash 16, S14 +
the six), `isready`/`readyok` after every `setoption`, every option name validated against the exe's
own `uci` list, fresh process per search, `quit` only after `bestmove`.

## Findings
- S-F9: on the PC's real path (PC r15, PC20, Threads 1, Hash 16) `go nodes N` is **fully
  deterministic** (48/48 across separate fresh processes) and **respects its budget as a hard cap**
  (48/48; worst case 96 nodes under N), with a legal bestmove every time. Median depth bought:
  6 at N=2,000, 10 at 20,000, 12 at 50,000, 16 at 250,000; budget utilisation rises from 0.68 to 0.83.
  Reproduce: `cd forge-combo29/swarm/13/job7 && python3 control_pcpath.py && python3 pcpath.py
  ~/b/pc/forge realgame12.fens /tmp/pp 2000,20000,50000,250000`.
  **This contrasts with S-F7**: the softnodes budget is not a cap (up to 164 % past it), the node
  budget is.

## Suspicions, not proven
- The rising budget utilisation with N suggests the engine's node counting and its depth-quantised
  stopping interact such that small budgets are "wasted" (stopping at 29 % of a 2,000 budget in one
  case). For self-play that means the effective sample budget varies more than the nominal one. I
  have not measured whether that matters for training data quality.

## What I did NOT do
- The 6 s + 0.06 s clock mode (a different search-limit path; file 6 lists it separately and it is
  another area's ground).
- Matches or strength measurement.
- The owner's own match positions — **my stated limit**: these are 12 G positions.

## What I am NOT sure about
- 12 positions × 4 budgets establishes determinism and budget discipline convincingly (48 runs, no
  mismatch), but it is a small sample for the *depth-per-budget* table; the medians are indicative,
  the spread shows real variation between positions.
- All 12 positions scored cp, none mate, so the mate-score path at these budgets is untested here.

## Times
See `stamps.txt`.

## Last command output

```
$ ls
CONTROL_PCPATH.md
control_pcpath.py
out
pcpath.py
realgame12.fens
REPORT_job7.md
stamps.txt
```
