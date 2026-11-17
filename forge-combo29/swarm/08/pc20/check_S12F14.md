# CHECK of seat 12's S-F14 — the one-ply-down draw short-circuit is still open on the PC build — seat 08

Their claim:
> S-F14: "the ONE-PLY-DOWN draw short-circuit is STILL OPEN on the PC build: `6k1/8/5PPP/8/8/8/8/R6K b - - 99 40`
> (black's only two moves both allow Ra8#) answers **cp 0** in **36 nodes** on PC r15, whereas [hm 97/98 differ]."

## Verdict: CONFIRMS — with a clean cliff at halfmove 99

My own harness, `go depth 6`, Threads 1, Hash 16, both builds, the halfmove counter swept:

| build | hm 0 | 96 | 97 | 98 | **99** | 100 |
|---|---|---|---|---|---|---|
| **PC r15 / PC20** | mate −1 | mate −1 | mate −1 | mate −1 | **cp 0 (18 nodes)** | cp 0 (18 nodes) |
| base / S14 | mate −1 | mate −1 | mate −1 | mate −1 | **cp 0 (18 nodes)** | cp 0 (0 nodes) |

**The cliff is at 99 on both builds.** Up to halfmove 98 the engine reports `mate -1` (Black is mated in one);
from 99 it reports `cp 0`. So the short-circuit fires where the counter *will reach* 100 after the move — one ply
down from the root — rather than only at a root whose counter is already ≥ 100. That is exactly seat 12's claim.

| their statement | my measurement |
|---|---|
| PC returns cp 0 at halfmove 99 | **yes, cp 0** |
| "in 36 nodes" | **18 nodes** — mine is `go depth 6`; theirs presumably a different depth. The node *count* differs, the conclusion does not |
| halfmoves 97/98 differ | **yes — both give `mate -1`** |

## The plant, and why it is the right one
The board at halfmove **0 scores `mate -1`**, so the harness demonstrably sees the win on this very position. Without
that, `cp 0` at 99 could have been a board that is not won at all. With it, the cp 0 at 99 is a verdict the engine
reaches *because of the counter*, not because of the position.

The **discriminator** is the 96/97/98 row: three consecutive counters that do NOT give cp 0. That separates "the
counter matters at exactly the boundary" from "this harness returns cp 0 for everything".

## The one difference from their number, stated rather than glossed
They quote 36 nodes; I measure 18. Both are small, and both are consistent with a near-immediate draw verdict; the
difference is depth (`go depth 6` here) and possibly their `searchmoves`-style restriction. **I am confirming the
claim — cp 0 at halfmove 99, not at 98 — and not their node count.**

## Why it matters, and its scope
This is a correctness defect on the PC build: at halfmove 99, with Black's only two moves both allowing `Ra8#`, the
engine scores the position as drawn instead of mated-in-one. Per FABLE_TO_swarm_6 a mate that ends the game is still
a mate, and here the mate is available *before* the 100th half-move completes — so this is not the "correct chess"
case that my own 08-W1 retraction covered. The two are different situations and the difference is exactly the
halfmove arithmetic: there, 15 plies were needed with 9 remaining; here, 1 ply is needed with 1 remaining.

## What I did NOT do
- Did not test other move counts for Black or other mating distances; one board, one mate distance.
- Did not test whether the search returns the mate if given `searchmoves` restricted to the mating line — that is
  seat 21's territory.
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s12f14.py /tmp/s12f14.txt
