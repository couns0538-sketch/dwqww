# REPORT job44 — a drawn root with a MATE IN 2: the PC build finds mate-in-1 but MISSES mate-in-2

**What was asked.** (My own next job, the gap `REPORT_job43.md` named.) The drawn-root spec's mate cases
used a mate in 1 only. A mate 2 moves away is the harder test: an engine that searches a drawn root may
find a mate in 1 and still miss a longer one, which would make the PC patch's repair **shallow-only**.

**The answer.** **It is shallow-only.** On a position that is **mate in 2 by six different winning moves**
(verified six ways), the PC build at a drawn root plays a non-winning move and reports **`cp 0`** — at
`go depth 4`, `go depth 10`, `go nodes 20000` and `go nodes 200000`. It finds mate-in-1 on the same kind
of root (`mate 1`, `e1e8`) but misses mate-in-2 entirely. The base build misses both (it adjudicates).

**How sure.** High on the measurement; and the position's distance is not my opinion — see the proof below.

## The board, and why its distance is certain

```
6k1/8/5K2/8/8/8/8/7Q w - - 0 60
```

An independent enumeration (every legal move, then every reply, then a mate-in-1 check) finds **six**
moves that force mate in 2 — `h1b7`, `h1h5`, `h1h4`, `h1h3`, `h1h2`, `h1g2` — and **no** move that mates
immediately. So the true distance is **mate in 2 moves**, beyond doubt.

## What the builds answer at a drawn root (halfmove 100)

| build | `go depth 4` | `go depth 10` | `go nodes 20000` | `go nodes 200000` |
|---|---|---|---|---|
| **PC (PC20)** | `h1g1`, `cp 0` — **miss** | `h1g1`, `cp 0` — **miss** | `h1g1`, `cp 0` — **miss** | `h1g1`, `cp 0` — **miss** |
| base | `h1a1`, `cp 0`, 0 nodes | `h1a1`, `cp 0`, 0 nodes | `h1a1`, `cp 0`, 0 nodes | `h1a1`, `cp 0`, 0 nodes |

Neither build finds the mate, and the PC build does not improve with depth or with 10× the node budget —
so this is not a depth artefact, it is a decision made before the search goes deep enough.

At **counter 0**, where the root-draw rule does not apply at all:

| build | `go depth 10` at counter 0 |
|---|---|
| PC (PC20) | `h1h4`, PV `h1h4 g8f8 h4h8` |
| base | `h1b7`, PV `h1b7 g8f8 b7a8` |

Both PVs stop one move short of the mate, and the base build at least *chooses* a winning move (`h1b7`, one
of the six) while the PC build's `h1h4` is also one of the six — so at counter 0 both are fine at picking,
and neither reports a mate score. **The miss at counter 100 is therefore about the drawn-root path, not
about move selection in general.**

## Comparison with mate-in-1 (21-C16 / 21-C20)

| case | base | PC (PC20) |
|---|---|---|
| drawn root, **mate in 1** | `cp 0`, `f2f3` — miss | **`mate 1`**, `e1e8` — finds it |
| drawn root, **mate in 2** | `cp 0`, `h1a1` — miss | **`cp 0`**, `h1g1` — **misses it** |

So the PC patch's repair covers exactly one ply of mate and no more. That is a **sharper statement of
21-F19's family** and it strengthens the case for the `DESIGN_drawn_root.md` rule: "search the root, then
take the draw unless the search finds a win" only helps if the search is deep enough to see the win, and at
`go depth 4` it is not.

## Findings

`21-F24 | NEW` — **at a drawn root the PC build's mate repair is shallow-only**: it reports `mate 1` for a
mate in 1 but `cp 0` and a non-winning move for a position that is mate in 2 by SIX verified moves, at
`go depth 4`, `go depth 10`, `go nodes 20000` and `go nodes 200000`. The base build misses both. At
counter 0 both builds pick a winning move (PC `h1h4`, base `h1b7`), so the defect is the drawn-root path,
not move selection. Threads 1, PC20 on the PC build.

`21-C22` — the board `6k1/8/5K2/8/8/8/8/7Q w - - 0 60` is **mate in 2**, proved by enumerating every
legal move and every reply: six moves force it (`h1b7`, `h1h5`, `h1h4`, `h1h3`, `h1h2`, `h1g2`), none mates
in 1. Any seat reusing this case should assert that distance, not assume it.

## A unit error of mine that took four attempts, recorded

My mate-distance solver disagreed with itself across three versions because I mixed **plies** and **moves**:
UCI's `score mate K` counts MOVES, so `mate 2` is 3 plies. My first versions returned ply counts and I then
compared them against ply-based and move-based checks in turn, "fixing" a solver that was sometimes right.
The version shipped returns MOVES (`2d−1` plies for distance `d`) and is asserted against the board above,
whose distance six independent wins establish.

I also **dropped a board I had labelled mate-in-3**, because the solver said 2 and the solver was right —
the assertion caught my label, which is exactly what it is for. That is why this job reports mate-1 and
mate-2 cases and **no mate-3 case**: I could not produce a verified mate-in-3 board in the time, and I
would rather ship two proved cases than three where one is guessed.

## Suspicions, not proven

- Whether a deeper fixed depth (say 16) would find the mate-in-2 at a drawn root. `go nodes 200000` did
  not, and 21-F22 makes a depth-16 bare-king search expensive, so I stopped at 10. Not proven either way.
- Whether `MateAlphaGuard true` (part of PC20) is what suppresses the mate score here. I did not run the
  board with PC20 minus that switch.

## What I did NOT do

- Did not produce a verified mate-in-3 case (stated above).
- Did not isolate which PC20 option causes the suppression.
- Did not add these cases to `job43/acceptance.py` yet; they are a separate script (`job44/mateN.py`) and
  merging them into the spec is the natural next step.

## What I am NOT sure about

- Whether the owner's match program would ever present a mate-in-2 at a drawn root. It is rare; the value
  of the finding is that it bounds the repair, not that it costs games.

## Times

see `job44/stamps.txt`.
