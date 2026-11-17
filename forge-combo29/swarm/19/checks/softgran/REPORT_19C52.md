# 19-C52 — I proposed a discriminator that cannot discriminate. The thread closes on power, not on data.

## The run
Same stratification on both sides: `|white_material − black_material| ≤ 4` (pawn 1, N/B 3, R 5, Q 9), same-move
restriction both sides, `softnodes 2000`.

| set | stratum | same-move cells | decided | PC20 better | 95 % CI |
|---|---|---|---|---|---|
| mine (200) | ALL | 176 | 29 | 12 = **41.4 %** | [0.255, 0.593] |
| mine (200) | **QUIET \|mat\| ≤ 4** | 103 | **14** | 7 = **50.0 %** | **[0.268, 0.732]** |
| seat 27 (600) | ALL | 406 | 109 | 67 = 61.5 % | [0.521, 0.701] |
| seat 27 (600) | **QUIET \|mat\| ≤ 4** | 318 | **88** | 56 = **63.6 %** | [0.532, 0.729] |

## What it shows, honestly: nothing decisive
**My quiet subset gives 7 of 14 — exactly 50 %, the maximally uninformative value.** Its interval
**[0.268, 0.732] contains both 41.4 % and 63.6 %.** It is consistent with my pooled figure, with seat 27's quiet
stratum, and with a coin.

**The power is the point.** At n = 14 decided cells:
- exact power to detect the true rate **0.414 is 0.033**
- exact power to detect the true rate **0.636 is 0.069**

**My proposed discriminator had a 3–7 % chance of answering the question it was designed for.** I named it as
"the last separator" without computing its power first, which is precisely the error I have been documenting for
several jobs — **I proposed an instrument and asserted it would separate two hypotheses without checking that it
could.** That is the same class as the vacuous test in 19-C47 (trap 12b) and the same class as seat 27's
sub-one-ply band: the sample has to be able to show the effect before a null means anything.

**The honest resolution: the quiet subset does NOT resolve it, and no further run on 200 positions will.** To
separate 41 % from 64 % at 80 % power needs roughly **48 decided cells in the quiet stratum**. My 200 positions
yield 14 decided quiet cells; I would need on the order of **600–700 quiet positions** to get there — which is
what seat 27 already has.

## So the thread closes where it was before this run
- **No harness difference** (19-C50: 600/600 cell agreement on its positions).
- **My slice is unrepresentative** in material balance (43.5 % vs 22.0 % sharp, z = 5.91).
- **My pooled 41.4 % rests on 29 decided cells with 0.15 power**; the quiet subset rests on 14 with 0.07.
- **Seat 27's 63.6 % on 88 decided cells is the only figure here with the power to support a direction.**
- **I concede the direction**, as stated in 19-C50. Nothing in this run changes that; it simply fails to add
  evidence either way, and I will not dress a 7/14 as support for anything.

## The transferable lesson, which is worth more than the result
**A discriminator is a hypothesis test, and it needs its power computed before it is announced as decisive.**
I wrote "run this and it closes the thread" when the correct statement was "run this; if you get 40+ decided
cells it can close the thread". **The tell I should have used: my quiet stratum had 103 same-move cells but the
decided subset was 14 — an 86 % tie rate.** When ties dominate, the effective n is the decided count, not the
row count, and quoting the row count as the sample size is trap 9's "committed is not currently used" in
statistical clothing.

**Correction to my own proposal:** the discriminator needs **quiet positions that actually produce disagreements**,
which means positions near the depth boundary rather than merely balanced ones. Balance was the wrong lever; the
depth-boundary rate is the one that sets the decided count.
