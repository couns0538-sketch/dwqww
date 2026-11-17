# PREDICTION - committed BEFORE measuring (19-C66: the "+3 ply at 20k" claim has a tie problem I never checked)

## What I am testing, and why my own rule forces it
**19-C44 (mine)**: at a 20,000-node budget PC20 reached **+3 ply summed over 6 positions** (S14 59 vs PC20 62),
described as "a tendency, not a guarantee". **19-C45** extended it to 50k (+1) and 250k (+1).

**Three reasons this needs re-running under the rules I have since written:**
1. **Six positions.** Trap 16: I have no power calculation for it and never had one.
2. **No sign-share.** Trap 18: I never reported how many positions share the direction. A +3 sum over 6 positions
   is compatible with one position being +3 and five ties.
3. **DEPTH IS AN INTEGER.** So at a fixed node budget the two engines will very often report the **same** depth —
   which makes this precisely the trap-20 case: **a sign-share over a quantised quantity is dominated by ties, and
   a sum can be positive while most positions are tied.**

**So the honest form of 19-C44 is a wins / ties / losses decomposition over depth, not a ply sum.**

## Setup fixed before running
- PC r15 (`~/pcbuild/build/forge`, sha 068f0927) vs base (`~/build_rel/forge`, sha e06310ec), Threads 1, Hash 16.
- Real positions: `their_600.fens` first 130. **n = 130, not 6.**
- `go nodes 20000` and `go nodes 50000`, ABBA, fresh process per search.
- Report **depth wins / ties / losses**, the ply sum, and the median depth difference — plus the tie fraction.

## My prediction, stated before any number exists
1. **The TIE fraction will be LARGE — I predict 50-75 %** at 20k, because depth is an integer and both engines
   stop at a similar count. This is the trap-20 shape arriving on a different quantity.
2. **The ply sum over 130 positions will be positive but small per position — I predict +0.05 to +0.25 ply/position**
   at 20k, i.e. a sum of roughly +7 to +30, against 19-C44's +3 over 6 (= +0.5/position). **I expect 19-C44
   overstated the per-position size, the same way my other small samples did.**
3. **The wins/decided share will be 55-70 % for PC20** — a real but modest lean, consistent with 19-C60's finding
   that the switches shift the tree without dominating it.
4. **Kill condition:** if ties are < 20 % at 20k, my trap-20 concern does not apply here and I will say so plainly.

## What each outcome means
- **High ties + small positive ply sum** -> 19-C44's DIRECTION stands but its SIZE was a 6-position artefact, and
  the honest statement becomes "PC20 reaches the same depth more often than not, and equal-or-deeper on ~60 % of
  positions". **That is a weaker claim than "+3 ply"** and I will state it that way.
- **Low ties** -> depth resolves the question where node counts did not, and 19-C44 stands nearly as written.
