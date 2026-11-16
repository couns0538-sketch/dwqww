# The counter-100 gap: 7 of 7 cases, base tree misses, PC build finds

File 6 says a `cp 0` at a high halfmove counter is **not** a defect, because the match program ends
the game at the 100th half-move. Its test is: same board at counter 0, `go depth >= 20`, read `mate N`,
defect only if **2N-1 <= 100 - counter** and the real counter still scores `cp 0`.

**That inequality has a hole.** A **pawn move** or a **capture** resets the halfmove clock, so a mate
that uses one lands before the 100th half-move *no matter what the current counter is*. The rule never
asks, so it excuses exactly the mates that are still reachable.

## The seven cases

Each position was checked with python-chess to have **exactly one** mating move, and that move to be a
pawn move or a non-pawn capture. All at **counter 100**, the worst case for the rule. **Threads 1**,
PC build under PC20, base tree under S14, `go depth 8`. Raw: `test7_out.txt`.

| kind | board | only mate | base tree / S14 | PC build / PC20 |
|---|---|---|---|---|
| PAWN | `8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1` | `a7a8q` | `cp 0`, **0 nodes**, `a7a8q` | **`mate 1`**, 265 nodes, `a7a8q` |
| PAWN | `8/P7/k7/P7/2K5/8/8/Q7 w - - 100 1` | `a7a8q` | `cp 0`, **0 nodes**, `a7a8q` | **`mate 1`**, 233 nodes |
| PAWN | `8/P7/k7/P7/2K5/8/8/4Q3 w - - 100 1` | `a7a8q` | `cp 0`, **0 nodes**, `a7a8q` | **`mate 1`**, 257 nodes |
| CAPTURE | `r5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1` | `h1a8` | `cp 0`, **0 nodes**, **`h1g2`** | **`mate 1`**, 145 nodes, `h1a8` |
| CAPTURE | `n5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1` | `h1a8` | `cp 0`, **0 nodes**, **`h1g2`** | **`mate 1`**, 145 nodes |
| CAPTURE | `b5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1` | `h1a8` | `cp 0`, **0 nodes**, **`h1g2`** | **`mate 1`**, 137 nodes |
| CAPTURE | `q5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1` | `h1a8` | `cp 0`, **0 nodes**, **`h1g2`** | **`mate 1`**, 137 nodes |

**Base tree: missed the mate in 7 of 7 (`cp 0`, 0 nodes). PC build: found it in 7 of 7.**

## Why this is worse than "plays the right move for the wrong reason"

In the three **pawn** cases the base tree happens to play the mating move, because 0 nodes means "first
legal move" and the first legal move there is the mate. That is the trap I noted in 15-F12.

In the four **capture** cases it plays **`h1g2`** — a move that is not the mate, not even a capture.
So the base tree does not merely fail to find the mate; **it plays a different, non-winning move** and
reports the position as drawn. That is a lost half-point in a real game, not a cosmetic scoring issue.
This distinction only became visible by testing four capture cases rather than the one pawn case I
started with.

## One-line statement of why the rule misses it

> File 6's test compares `2N-1` against `100 - counter`, but a mating line containing a **capture or a
> pawn move** resets the halfmove clock, so such a mate is reachable even when `2N-1 > 100 - counter`;
> the rule needs the disjunct "**or the mating line contains a capture or pawn move within the
> remaining plies**".

Suggested corrected statement:

> A `cp 0` at counter H is a defect if a forced mate exists whose line **either** ends within
> `100 - H` plies **or** contains a capture or pawn move before the 100th half-move (which resets the
> counter), and the board at counter H still scores `cp 0`.

## Scope, stated

- Both builds, Threads 1, one depth (8) — deep enough for a mate in 1, and the mate is in 1 ply so no
  horizon question arises.
- The PC build is correct in all 7; the base tree is wrong in all 7. So this is a **base-tree-only**
  defect, already repaired on the PC, exactly like 15-F12.
- I did not test mates that need more than one ply before the capture/pawn move; the rule's disjunct
  would then have to consider whether the reset happens *within the remaining plies*, which my
  one-line form already says.
- These seven positions were constructed from a known working geometry, not sampled from games. They
  are minimal demonstrations, not a frequency estimate. I make no claim about how often this arises in
  the owner's games.
