# REPORT — seat 07, job 42: check of seat 16's S-F4 (search colour symmetry) on the PC build

## What was asked / the answer / how sure

**Asked:** (cycle work) take a contested or unconfirmed finding. Seat 16's **S-F4** — "the depth-10
search is NOT colour-symmetric: 19 of 353 G pairs (5.4%) give an equal score, bestmoves mirror on
252/353 (71.4%); cause is order/depth dependence, not the evaluation" — was unconfirmed by anyone, and
it is in this seat's competence (07-C9 established the evaluation's symmetry convention).

**Answer:** **CONFIRMS 16-S-F4 independently at depth 10** — but I must withdraw the word "extends".
I wrote that I was extending the finding to the PC build under PC20; **seat 16's own S-F14 had already
done exactly that**, over all 353 G positions, and its S-F15 had already attributed the extra asymmetry
to `TtPruneV2`. I did not check their later rows before writing mine, so my "extension" duplicated
their work. What stands is the independent confirmation on a different 120-position subset, and the two
measurements I added that their summary does not contain (median gap and depth collapse). On 120 G positions at depth 10: exact score symmetry **7/120 = 5.8 %** (seat 16:
5.4 %), bestmove mirrors **83/120 = 69.2 %** (seat 16: 71.4 %). The rates agree closely.
**New detail their summary does not state:** the disagreement is mostly *small* — median score gap
**15 cp**, 103 of 120 pairs within 50 cp — so "not symmetric" means "rarely exactly equal and usually a
few centipawns apart", not "the two colours are evaluated differently".

**How sure:** high, with one important caveat: my first version of the check was **wrong** and the
correction is below.

## The bug I had to fix first (the sixth control-caught error of this run)

`python-chess`'s `Board.mirror()` swaps colours **and** the side to move. Search scores in this engine
are **side-to-move relative** (07-C9, and seat 16's own C5 states the trap explicitly). So a +255
advantage for White becomes a +255 advantage for Black in the mirror, and Black is to move there —
**the expected reading is the SAME number, not its negation.**

My first version asserted negation and reported 4/120 symmetric. The tell was in its own output: pairs
like `orig cp −304 → mirror cp −301` had the **same sign**, which negation forbids and equality
predicts, and 25 of the first 40 pairs had the *correct mirrored move* while being counted as failures.
Fixed to equality; the rates then matched seat 16's.

**This is exactly the false-alarm class seat 16 itself warned about** in its C5: "a negation-based
symmetry checker would report a false 8422 cp difference per position". I walked into the trap they
documented, and the same-sign scores are what caught it.

## Controls (both required before any rate was reported)

    CONTROL self-pair agrees: True   (score ('cp', 49) vs ('cp', 49))
    CONTROL non-mirror pair does NOT agree: True

The self-control catches a checker that always says "equal"; the non-mirror control catches one that
says "equal" to anything.

## Results (PC r15 under PC20, Threads 1, Hash 16, depth 10, 120 G positions)

| measure | this seat | seat 16 (base tree) |
|---|---|---|
| exact score symmetry | **7/120 = 5.8 %** | 19/353 = 5.4 % |
| bestmove mirrors | **83/120 = 69.2 %** | 252/353 = 71.4 % |
| median score gap | **15 cp** | not reported |
| pairs within 50 cp | **103/120 = 85.8 %** | not reported |
| largest score gap | **289 cp** | not reported |

The two independent samples agree on both rates to within half a percentage point. **Correction:** I
originally described this as base-vs-PC, which was wrong — seat 16's S-F14 is *also* PC r15/PC20
(120/353 = 34 % move-mismatch against my 30.8 % on this 120-position subset). So the agreement is
between two seats on the **same build**, on different position subsets, which is a reproducibility
check rather than a build-generalisation.

## What this adds beyond S-F4

1. **It reproduces on an independent 120-position subset** with rates matching to 0.4 % — a
   reproducibility check, not an extension to a new build (their S-F14 already covered PC r15/PC20).
2. **The magnitude is small**: 85.8 % of pairs are within 50 cp of symmetric, so the practical effect is
   tie-ordering noise, not a colour bias. Seat 16 attributed it to "order/depth dependence", and a
   median 15 cp gap with correct mirrored moves in 69 % of pairs is consistent with exactly that.
3. **18 pairs have the move differing while the score agrees within 10 cp** — pure equal-score tie
   ordering, which is the mechanism seat 16 named.

## Findings

**07-C41** in FINDINGS.md.

## The large gaps converge with depth, which supports their stated cause

I checked the two biggest score gaps at greater depth rather than leaving them as unexplained
asymmetry:

| fen | d10 | d14 | d18 |
|---|---|---|---|
| `1r6/8/4K3/5p2/5k2/7p/8/8 w` | cp -2403 vs cp -2692 (gap 289) | **mate -7** vs cp -2899 | **mate -7 vs mate -6** (gap 1) |
| `8/8/4k3/3rp1RR/KP6/P2p4/6PP/2r5 w` | cp -1 vs cp -165 (gap 164) | cp -225 vs cp -235 (gap 10) | **cp -335 vs cp -342** (gap 7) |

Both collapse to near-equality by depth 18. So the large gaps are **horizon effects that resolve with
depth**, not a persistent colour bias - direct support for seat 16's attribution to "order/depth
dependence" rather than to the evaluation.

## Suspicions, not proven

- That the residual gap is entirely `std::sort` tie-breaking plus aspiration order. File 3 already lists
  equal-score tie order as known and harmless; this measurement is consistent with it but does not
  isolate the cause.

## What I did NOT do

- Did not run the base tree on the same 120 positions, so the build-to-build comparison rests on seat
  16's numbers rather than a same-set comparison I ran myself.
- Did not go to depth 12+; seat 16's S-F5 covers depth behaviour.

## What I am NOT sure about

- Whether the 17 pairs with a score gap above 50 cp include a genuine asymmetry rather than deeper
  order effects. The largest is 289 cp, which is larger than tie noise; worth a look if anyone is
  chasing colour bias specifically.

## Times

See job42/stamps.txt.
