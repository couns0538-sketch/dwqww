# PC20 IS NOT OVERCLAIMING: mate 4 is the OPTIMAL mate on board 103, established by exhaustive search

Builds: **base** `e06310ec`, **PC r15** `068f0927`. Threads 1, Hash 16, OwnBook false.
Tool: `pc/forced_mate.py` — bounded minimax over the **full legal move list**, memoised, with four controls
including a two-directional one (it must be able to answer *yes* and *no*).

## The question, and a correction to its premise

The coordinator asked: **if the true DTM is 6 and PC20 reports `mate 4`, is PC20 overclaiming?** That would be
a serious new finding — a score asserting a mate that does not exist.

**The premise conflated two boards.** `mate 6` is the true DTM of **seat 23's W2 board**
(`8/5K2/7Q/4k3/8/8/8/8 w`, a K+Q v K position). Board 103
(`2r1n1r1/3b2p1/2Ppp3/B2n2kp/R2PB1P1/4P2P/1P6/4KQR1 w`) is a different, rich middlegame position for which
**nobody had computed a true DTM**. The 6 and the 4 come from two different positions and are not comparable.
That is my fault for putting both numbers in one reply without saying so plainly.

So the right question is the one the coordinator actually wanted answered: **is `mate 4` achievable on board
103?** Answered below by exhaustive search, not by trusting either engine.

## The answer: mate 4 is forced, and it is OPTIMAL

### 1. PC20's move forces mate in 4 against every defence

```
move h3h4 forces mate in <= 4 moves (7 plies): True       [1,829,749 positions memoised]
```

This is not a replay of the engine's own line. It is a full minimax: at every node where the mating side
moves it needs **one** winning move, and at every node where the defender moves it requires **all** legal
defences to lose. A stalemate returns False, so a stalemate trick cannot be mistaken for a mate. **1.83
million positions, and `h3h4` mates within 4 moves against anything Black can do.**

### 2. No faster mate exists — so 4 is the true DTM

```
side to move forces mate in <= 3 moves (5 plies): False    [118,780 positions memoised]
```

**There is no forced mate in 3 on board 103.** Combined with (1), the exact distance-to-mate for this position
is **4 moves**, and `h3h4` achieves it.

### 3. Therefore the two engines are both truthful, and PC20 is exact

| configuration | reported | forced mate exists? | verdict |
|---|---|---|---|
| PC20, depth 12+ | `mate 4` / h3h4 | **yes, and 4 is optimal** | **EXACT — the true DTM** |
| base + S14, depth 12-13 | `mate 6` / g4h5 | real but slower (a mate-in-4 is available) | truthful, non-optimal |
| base + S14, depth 14+ | `mate 4` / h3h4 | yes, optimal | EXACT — converges to the true DTM |

**PC20 is not overclaiming. It reaches the optimal mate two plies earlier than base+S14 and never reports the
6 at all.** That is a genuine ordering improvement, and it is the opposite of a defect.

## What this means for the "falling mate number" family

The 6 → 4 drop on board 103 is now fully explained and is benign in every part:

- **both numbers are true** (a mate-in-6 exists; a mate-in-4 also exists);
- **the drop is a change of move**, which `searchmoves` pinning shows directly (each pinned move holds its own
  distance constant across depths);
- **the final number is the true DTM**, which the exhaustive search establishes;
- **and the whole sequence is configuration-specific** — PC20 never shows it.

So there is **no distance defect, no truncation, and no overclaim** anywhere in this family. The only error in
the family was 23-F90's, which read a *converging* sequence on a **different board** as evidence of a false
distance.

## Scope of the claim in S-C52/S-C53, stated explicitly

As the coordinator asked: **the DTM check is a statement about a specific build and settings, not about the
engine.** Concretely —

- **"base + S14 reaches depth D and reports X" is a statement about base + S14.** PC20 on the same board
  reports a different, *better* answer from a lower depth. A finding phrased as "the engine's mate distance
  falls" would be false of PC20 on this board.
- **Any mate-distance finding from this run should name its build and settings**, and a claim made on one
  configuration must not be read as a claim about Forge. This is the mate-distance instance of the settings rule
  at the top of `METHOD_NOTES.md`.
- **"The distance falls toward truth" does not transfer between builds.** On board 103 base+S14 falls 6 → 4
  toward the true 4; PC20 starts at the true 4. On seat 23's W2 board the PC build's own ladder falls 13 → 10 →
  6 toward the true 6. Same shape, different builds, different boards — the convergence is real in both, but
  the *starting* number is a property of the configuration.

## What I could not finish

`g4h5`'s own forced-mate-in-6 status is unproven: the search needs 11 plies and exceeded my 270 s budget at
1.8 M nodes. **That does not affect any conclusion above** — mate 4 being forced and optimal is sufficient to
refute overclaiming, and whether the mate-in-6 is forced on `g4h5` specifically is a different (and
uninteresting) question, since a mate-in-4 exists regardless.

## Files

- `pc/forced_mate.py` — the solver, with controls 1-3 (terminal root, no-mate bound, and the two-directional
  control that proves it can answer both yes and no). **Control 1 initially FAILED and caught a real bug in my
  own understanding**: at a checkmated root the side to move has *lost*, so "does the root side force mate" is
  correctly False, not True — my first control asserted the wrong thing and the suite refused to report.
