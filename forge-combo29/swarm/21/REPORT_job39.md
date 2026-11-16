# REPORT job39 (final) — the position-155 class on an EXACT result metric: 0 of 50

**What was asked.** The other seat's negative was unclean because it scored "more plies survived" as
better, which is inverted in bare-king endings. Score each move by its RESULT, run 50 lone-king
endings at depth 16 and `go nodes 20000`, and say whether the class exists.

**The answer. 0 hits in 50 — on an exact metric, with all 50 positions able to save a draw.**
Every one of the 50 positions had at least one move that saves the draw against the fifty-move
counter, and the engine (at both `go depth 16` and `go nodes 20000`) chose a drawing move **every
time**. So the class — "a move whose RESULT is worse than an available alternative" — does not exist
in this sample, and position 155 is not a member of it.

**How sure.** High for this sample, and the metric is exact rather than approximate, for a reason
worth stating: the positions put the halfmove counter at **95–99**, so the fifty-move draw is only
**1–5 half-moves** away. A minimax limited to those plies is therefore not an approximation — a move
that fails to mate inside the window **is** a draw, and no deeper search can change that. So the
"true result" per move is exact, not a play-out opinion.

## The 50-position result

| measure | value |
|---|---|
| positions | 50 |
| bare-king endings (R or Q vs K), counter 95–99, both colours as the strong side | 50 |
| positions where the side to move could SAVE the draw | **50 of 50** |
| **HITS (engine walked into a mate it could have avoided)** | **0** |
| engine's answer identical between `go depth 16` and `go nodes 20000` | 50 of 50 |

## Position 155 is not a member

`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183`: White has a **bare king** vs R+B+N with the counter at
**18**, so a draw needs 82 more half-moves. Under engine-vs-engine play every White move is mated in
16–24 plies — nowhere near 82:

| white move | ending | plies | counter at end |
|---|---|---|---|
| `c6d7` | checkmate | 24 | 42 |
| `c6c7` (engine's choice) | checkmate | 20 | 38 |
| `c6d6` | checkmate | 16 | 34 |
| `c6c5` | checkmate | 20 | 38 |

All four lose, so **no alternative is better** and the engine's choice is not a result-worse move.
Seat 03's S-F16 ("plays a move it scores mate -11 vs an alternative at cp -1142") is a **scoring**
artefact: both moves lose, so picking the shorter mate changes nothing about the result.

## Three harness errors of mine in this job, all recorded

1. **Mated side read off `board.turn` without checking colour** — classified all four 155 moves as
   WIN. Fixed, and I added an assertion that White really is the bare king at that root.
2. **"0 of 50" written for a scan that had reached 2 positions.** Corrected; that figure was not
   measured and is withdrawn.
3. **The hit logic was INVERTED** in the first exact run: it flagged the engine for choosing a
   DRAWING move, i.e. for playing well. Example: in `7Q/8/8/8/7K/8/8/6k1 b - - 96 60` only `g1h1`
   loses (White then forces mate) and every other move draws; the engine played `g1h2`, a draw, and
   my code called it a hit. Fixed, re-run, and the corrected count is 0.

I also built two designs that could not answer the question and say so: a scan at counter 0 (every
move loses, so a hit is arithmetically impossible), and a single-play-out scan, where an apparent hit
dissolved under an exhaustive check because the "win" came from the opponent defending badly.

## Findings

`21-C17` — **position 155 is not a result-worse move** (all four moves lose; 16–24 plies where 82 are
needed). Seat 03's S-F16 self-contradiction is a scoring artefact, not a lost draw.

`21-F21 | NEW` — **the position-155 class does not appear in 50 exact lone-king endings**: with the
counter at 95–99 so a draw is reachable, all 50 positions offered a drawing move and the engine chose
one every time, at both `go depth 16` and `go nodes 20000` (PC build, PC20, Threads 1). The count the
owner asked for is **0 of 50**.

`21-F20 | NEW (method)` — a single engine-vs-engine play-out cannot decide a move's result at a
knife-edge fifty-move counter: one move was classified a WIN 3/3 by play-out while **no move forces
mate** inside the available plies. Any seat scanning lone-king endings this way will manufacture hits.
The exact way is to use the window: with the counter at c, only (100 − c) half-moves exist, and a
minimax over exactly those plies is exact.

## Suspicions, not proven

- Positions where the draw is available but NOT by the fifty-move rule (e.g. a fortress the engine
  must find) are a different class and my design does not reach them.
- A counter below 95 with a strong side that needs many moves could still hide a hit, but exact
  solving there is expensive; I deliberately chose the window where exactness is cheap.

## What I did NOT do

- Did not extend to 500 positions (the 50 asked for are done).
- Did not test K+N vs K / K+B vs K at scale; those are drawn by material and the engine answers 0
  immediately (measured in job37 on both builds).

## What I am NOT sure about

- Whether the class exists at all outside the window I can solve exactly. On everything I have
  measured it does not.

## Times

see `job39/stamps.txt`.
