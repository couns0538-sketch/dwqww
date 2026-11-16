# CHECK of seat 04's 04-F10 — score and move nondeterminism above Threads 1 — seat 08

**This is a threading check, so Threads 4 is the SUBJECT and Threads 1 is the CONTROL.** The swarm's Threads-1 rule
does not apply to the Threads-4 arm, and every number is labelled by arm.

## Verdict: the SCORE claim CONFIRMS strongly; the MOVE claim CONFIRMS on my second position and does NOT reproduce
## on their own board. So their sentence is right in substance and over-stated in one particular.

Their claim:
> 04-F10: "On an ORDINARY middlegame position from set G (`1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1`),
> PC r15 under PC20, `go depth 12`, Threads 4, ten fresh processes: **9 distinct scores** in 10 runs ... **and two
> different bestmoves — `g7g6` in 7 runs, `e5e4` in 3**. Threads 1 under the same settings: `-293` in 5/5 runs,
> 31,779 nodes every time."

My harness is my own, TEN fresh processes per arm, two positions, PC r15 under PC20, depth 12, Hash 16.

| position | arm | distinct scores | distinct bestmoves | nodes range |
|---|---|---|---|---|
| their board `1r6/…/R1R5 b` | **Threads 1 (control)** | **1 of 10** (cp −293) | **1** (g7g6) | 31,779 .. 31,779 |
| their board `1r6/…/R1R5 b` | **Threads 4 (subject)** | **10 of 10** — cp −266, −270, −282, −287, −291, −296, −298, −301, −303, −314 | **1** (g7g6) | 81,244 .. 181,492 |
| my second middlegame `r1bqk2r/…/R1B1K2R w` | **Threads 1 (control)** | **1 of 10** (cp 43) | **1** (e1g1) | 38,996 .. 38,996 |
| my second middlegame `r1bqk2r/…/R1B1K2R w` | **Threads 4 (subject)** | **7 of 10** — cp 38, 39, 41, 44, 46, 47, 49 | **2** (c1f4 ×4, e1g1 ×6) | 49,893 .. 108,580 |

### What reproduces exactly
- **Threads 1 is perfectly reproducible** on both boards: one score, one move, one node count, ten runs out of ten.
  My control reproduces their `-293` and `31,779` **exactly** — the same score and the same node count they quote.
  That is a strong sign my harness and build match theirs.
- **The score nondeterminism is real and larger than they said**: 10 distinct scores in 10 runs (they saw 9).
  The node count at Threads 4 spreads over 81,244–181,492 against a constant 31,779 at Threads 1 — a 2.6x–5.7x
  spread in work for the same search.

### What does NOT reproduce
On **their own board** the bestmove was `g7g6` in **all ten** Threads-4 runs. They reported `g7g6` in 7 and `e5e4`
in 3. I cannot reproduce the move variation on that position with ten runs, so their specific "two different
bestmoves on this board" is not confirmed by me — it may need more runs to hit, or their three `e5e4` runs came
from a different arm or a different build, or it is a low-probability event I missed.

### But the move claim is TRUE in general
On my **second** ordinary middlegame the move varied: `c1f4` in 4 runs and `e1g1` in 6, with 7 distinct scores.
So the substantive claim — *above Threads 1 the engine can play a different move depending on the run* — is
**CONFIRMED**, just not on the position they illustrated it with.

## Controls (enforced — a failure aborts, it never prints a verdict)
- Threads 1 must be reproducible in **score and move** on each board, else a Threads-4 spread could not be
  attributed to threading: satisfied on both (1 score / 1 move in 10 runs each).
- every run must reach depth 12 on both arms: satisfied.
- every score must parse: satisfied (no `None`).

## The consequence, stated plainly
The earlier swarm line "move choice is currently trustworthy and scores are not" (from seat 04's Threads-4 result on
one lost position) **does not hold in general**. On an ordinary middlegame the move varies between `c1f4` and
`e1g1` at Threads 4. `c1f4` and `e1g1` are both plausible developing moves and the scores differ by ~6 cp, so this is
not a blunder — but it means **any Threads-4 result is not reproducible in move or score**, and a match run at
Threads 4 cannot be replayed. Threads 1 is the only reproducible arm, which is exactly why the swarm rule exists.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_04f10.py /tmp/o04f10.txt

Raw output committed as `check_04f10.txt`.

---

## CORRECTION to the "does NOT reproduce" section above — my sample size, not their claim

The section above says their `e5e4` did not reproduce because I saw `g7g6` in 10 of 10 Threads-4 runs. That
conclusion was **wrong**, and twenty more runs show it. Committed batch with per-run data in
`move_distribution.txt`:

| bestmove | count in this 20-run batch | share |
|---|---|---|
| g7g6 | 16 | 80 % |
| **e5e4** | **3** | **15 %** |
| **f6d7** | **1** | **5 %** |

**Three distinct moves in twenty runs**, 16 distinct scores, nodes 53,433–175,349. An earlier batch of twenty I ran
showed `g7g6` 18 / `e5e4` 2; the batch before that was my original ten, all `g7g6`. So across 50 Threads-4 runs on
this one board the move distribution is roughly 44 / 5 / 1 with three different moves seen.

The minority moves are **5–15 % events**, and my original ten runs had roughly a 20–35 % chance of missing them
entirely. That is exactly what happened.

**04-F10 is CONFIRMED IN FULL**: score nondeterminism AND move variation on an ordinary middlegame at Threads 4.
The wording of my own 08-C7 ("their example board is not") is withdrawn — the board is fine, my sample was too
small. Their 7/3 split and my 16/3/1 are draws from the same distribution.

**The general lesson, applied from here on:** when the question is the SPREAD, ten runs is not enough. Twenty runs
minimum, and the per-run data must be committed so a reader can see each draw rather than a summary I typed.

**A second correction, in the same spirit.** An earlier version of this paragraph said a `f5e6` had appeared. It had
not — that move came from a run whose output I printed but never committed, and it does not appear in any committed
batch. The committed batches contain `g7g6`, `e5e4` and `f6d7` only.
