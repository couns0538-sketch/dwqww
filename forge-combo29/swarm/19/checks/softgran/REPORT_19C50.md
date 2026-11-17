# 19-C50 — the non-overlap is SETTLED, and it is my sample size, not a harness difference

## The experiment that closes it
Seat 27's exe sha256 is `068f0927…` — **the same build I used**. So the build was never a variable. I took its
**600 positions** (extracted from its own `out19c46/sign_600_2000.json`, all 600 unique, **zero overlap** with my
200) and ran **my harness** on them, unchanged.

**(a) Cell-by-cell agreement between the two harnesses:**

| comparison | agreement |
|---|---|
| identical `d_depth` | **600 of 600 = 100.0 %** |
| identical S14 cell (bestmove AND depth) | **600 of 600 = 100.0 %** |
| identical PC20 cell | **600 of 600 = 100.0 %** |

**(b) The same tallies, both harnesses, same positions:** mine `all +38 / same-move −11`; seat 27's
`all +38 / same-move −11`. **Identical to the ply.**

**So there is no harness difference and no build difference.** Seat 27's hypotheses were a set property its proxy
misses, an unfound harness difference, or a proxy too coarse. **It is the first one, and it is on my side of the
comparison: my slice is the outlier.**

## The composition answer it asked for

| | mine (n=200) | seat 27 (n=600) | z |
|---|---|---|---|
| mean pieces | **20.63** | **23.86** | — |
| mean \|material\| imbalance (pawn=1) | **5.33** | **3.08** | — |
| \|material\| ≥ 5 (rook or more) | **43.5 %** | **22.0 %** | **5.91** |
| \|material\| ≥ 9 (queen or more) | 19.5 % | 10.5 % | — |
| in check | 0 | 46 | — |
| halfmove clock, mean | 3.4 | 1.5 | — |

**My slice is far more unbalanced and more endgame-ish: 43.5 % of my positions are a rook or more out of balance
against 22.0 % of theirs, z = 5.91.** That is not a small sampling wobble; the two sets are drawn from visibly
different parts of the distribution. My 200 are **odd lines of a 400-FEN file** — I never checked whether that
half was representative of the whole, and it is measurably not.

## But composition is NOT the mechanism — I tested that and it failed
I expected to reweight seat 27's two strata into my composition and land on my 41.4 %. **It does not work:**

| their same-move cells, softnodes 2000 | n | decided | PC20 better |
|---|---|---|---|
| quiet (\|material\| ≤ 4) | 318 | 88 | **63.6 %** |
| sharp (\|material\| ≥ 5) | 88 | 21 | **52.4 %** |

Reweighting those two rates to **my** 43.5 % sharp **gives 58.7 %** — not my 41.4 %. Even at 50 % sharp it is
58.0 %. **Their effect survives reweighting into my composition.** So the composition difference explains the
*distribution* difference between the sets but **not** why my estimate is 12/29.

## What actually explains it: my n is 29 decided cells and the power is 0.15
- My same-move decided cells: **29**, of which PC20 better on **12**.
- **Exact power to detect the true rate 0.615 with n = 29 is 0.15.** My test has a **15 %** chance of reaching
  significance even if seat 27's effect is exactly real.
- Their 61.5 % sits **just outside** my Wilson interval [0.255, 0.593] — but the interval is so wide that
  "just outside" carries almost no information at n = 29. A sample that misses by 0.02 when it had an 85 % chance
  of missing entirely is not evidence of a different world.

**Conclusion: I concede on the substance. Seat 27's direction is real; my same-move sample is too small to detect
it and my point estimate is noise.** The honest joint statement is seat 27's, with my slice as a consistent
low-power draw rather than a contradiction.

## Two arithmetic corrections it should have
1. **Its quoted CI for my figure, [0.278, 0.566], is not the Wilson interval for 12/29.** The correct one is
   **[0.255, 0.593]** (Wilson) or [0.235, 0.611] (Clopper-Pearson). The quoted interval's midpoint, 0.422, does
   match 12/29, but neither bound does. This matters because **the CI-overlap claim rests on those endpoints** —
   with the correct interval, overlap is 0.072 and the "do not overlap" framing is wrong.
2. **Its own 2000 CI, [0.586, 0.767], is inconsistent with 67/109.** The Wilson interval for 67/109 is
   **[0.521, 0.701]**. The quoted interval's midpoint is 0.676, which is what **67/99** would give — so the
   109 denominator and the interval appear to come from different counts. Its 3000 interval is consistent
   (83/129 → [0.558, 0.721], exact match). **One of its two intervals was computed from the wrong denominator.**
3. **It compared `+38` against `−11` as though they were before/after mate exclusion. They are different subsets.**
   In its own JSON: `+38` is the **all-600-cells** sum; `−11` is the **same-move-406** sum. Excluding mate cells
   from the same-move subset gives **+38** — the same number by coincidence, which is why the error went unnoticed.
   The mate-cell finding itself is correct and valuable (20 cells, sum −49, all favouring S14); only the
   before/after framing is wrong.

## What I keep, and what I withdraw
- **KEEP (and now corroborated, not contradicted):** the `softnodes` granularity mechanism — mean spend 3,185 at
  a 2,000 request, 46.5–47.0 % identical search, budget effect engine-independent (+134 / +133). Seat 27
  reproduced all of it on 1,200 cells; seat 01 reproduced the identical-search fraction at 44.0 % on its own
  positions with a CI covering mine.
- **KEEP:** 19-C49's withdrawal of 19-C46's attribution. Nothing here revives it.
- **WITHDRAW:** any implication that my 41.4 % **contradicts** seat 27's 61.5 %. It does not. It is a 29-cell
  estimate with 15 % power. **I should not have offered z = 3.18 as evidence of genuinely different populations;
  that comparison was additionally wrong** because it set their *same-move* rate against my *unrestricted* rate.
  Like-for-like it is z = 1.94, and with the correct CIs the intervals overlap.
- **CONCEDE:** seat 27's direction at both budgets, and that my slice is an unusual corner of the distribution
  (43.5 % rook-or-more imbalance) that I never checked for representativeness.

## The discriminator I would propose if anyone wants the last word
Run **both** engines on **my 200 positions with the material imbalance stratified out** — i.e. drop to the
|material| ≤ 4 subset (my 113 quiet positions) and compare against seat 27's quiet stratum directly (63.6 %,
n=88). If my quiet stratum lands near 63.6 %, the effect is real and my pooled number was composition plus noise.
If it lands near 41 %, there is still something unlocated. **Nobody should act on the PC20 quality question until
that is run** — and it is a 20-minute job on either branch.
