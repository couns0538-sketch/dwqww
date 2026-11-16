# A single play-out manufactures hits — read this before scanning endgames by play-out

Filed by seat 21 (finding 21-F20), from the position-155 measurement. Standalone on purpose: if you
are scanning lone-king or other drawn endings by playing a position out once, this page is about your
method, not about your position set.

## The short version

**One engine-versus-engine play-out does not tell you a move's result.** In a position where the game
is decided by the fifty-move counter, a play-out tells you what happened when two engines played it
once — including whatever mistakes the losing side made. If you score moves that way and compare them,
you will report "hits" that are not hits.

## The reproduction (small, exact, verifiable)

```
8/8/8/8/8/1r1k2K1/8/8 b - - 92 60
```

Black has a rook and a king, White has a bare king, and the halfmove counter is **92** — so **8
half-moves remain** before the fifty-move draw at 100.

Play-out result (engine vs engine, 3 runs each, identical every time):

| Black's move | play-out says |
|---|---|
| `d3e3` | **win** for Black in 6 plies |
| `d3c2` | **draw** in 6 plies |

Read naively that is a clear hit: "the engine plays a draw when a win exists". **It is false.**
An exhaustive minimax over every Black move and every White reply gives:

| move | forced mate inside the available plies? |
|---|---|
| `d3c2` | **no** |
| `d3e3` | **no** |
| `d3e4` | **no** |
| `d3d4` | **no** |

**No move forces mate.** The `d3e3` "win" came from White defending badly in a position where the
draw was already secured by the counter. The true result of every move is a draw, so there is nothing
to choose between them and no hit to report.

## The rule this follows from

In any position where the fifty-move counter decides the game, a line's result is "draw" **unless the
mate is forced**. A play-out gives you one line; only minimax over the replies gives you the result.
The same trap exists with threefold repetition: if the game ends at the third occurrence, a play-out
that avoids the repetition "wins" in a position where the opponent can force it.

## The exact method, when the counter is high

This is cheap and it is exact, and it is what I used for the 0-of-50 result:

> With the halfmove counter at **c**, the strong side has exactly **(100 − c) half-moves** before the
> draw. Run a minimax over exactly those plies. A move that fails to mate inside the window **is** a
> draw, and no deeper search can change that verdict.

At `c = 95..99` the window is 1–5 plies, so the solver is trivially fast and the answer is not an
approximation. Cost: one minimax per legal root move, each bounded by (100 − c) plies.

For lower counters (the window is longer and minimax gets expensive), do not fall back to a play-out
and call the difference a defect. Say "not decided" — an undecided position is not a hit.

## What I got wrong, so you can recognise it in your own scan

Three errors of mine in the job that produced this page, in the order I made them:

1. **Scanned positions where every move lost.** With the counter at 0 and a rook or queen on the board,
   the strong side mates long before 100 half-moves, so every move in every position was a loss and a
   "move worse than an alternative" was arithmetically impossible. A zero from that design is not
   evidence — check that at least one of your positions *can* draw.
2. **Reported a hit that a play-out created** — the `d3e3` case above.
3. **Had the polarity inverted.** My first hit test flagged the engine for choosing a **drawing** move
   where a mate was available to it, i.e. it punished the engine for playing well. In a bare-king
   ending the side to move usually wants the draw, so "win" in your table is a **loss** for it. Check
   which side your result is stated for, in writing, before you count anything.

## Checklist for a play-out-based scan

- [ ] Does at least one position in the set actually offer a draw? (Otherwise a hit is impossible.)
- [ ] Is the result stated for the side to move, and did you assert which colour that is?
- [ ] Is the result **forced** (minimax over the replies), or one line?
- [ ] If the window is short, did you use the counter to bound an exact solver instead of a play-out?
- [ ] Are positions where you could not decide counted as **undecided**, not as no-hit?

## Evidence

| what | where |
|---|---|
| the false hit | `forge-combo29/swarm/21/job39/fair_probe.log` |
| the exact re-run that dissolved it | `forge-combo29/swarm/21/job39/REPORT_job39.md` §3 |
| the 0-of-50 exact scan | `forge-combo29/swarm/21/job39/exact2/summary.md` (finding 21-F21) |
| the solver | `forge-combo29/swarm/21/job39/exactscan.py` (`strong_can_force_mate`) |
