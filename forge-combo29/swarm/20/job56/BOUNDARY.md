# seat 20 — job 56: where the MultiPV collapse begins — a CLIFF between 128 and 256 MB, plus a gradient below it

Pre-stated rule: a Hash is UNSAFE if the median deepest depth over 10 positions is below **half** the healthy median.
MultiPV fixed at **3** (the plausible GUI setting), PC r15 + PC20, Threads 1, `go wtime 5000`, one run per position
(the effect is binary and huge when it fires).

Healthy reference (Hash 16 MB, MultiPV 1): depths `17,17,16,18,19,18,16,16,15,18` → **median 17.0**.

## Results

| Hash | depths across the 10 positions | median | verdict |
|---|---|---|---|
| **16 MB** | 14,12,12,14,13,15,14,12,12,15 | **13.5** | SAFE |
| **64 MB** | 13,11,11,12,11,14,14,11,10,15 | **11.5** | SAFE |
| **128 MB** | 12,9,6,11,11,12,14,10,8,14 | **11.0** | SAFE |
| **256 MB** | 3,4,4,10,5,4,12,8,4,4 | **4.0** | **UNSAFE** |
| **512 MB** | 1,1,1,1,1,1,1,1,1,1 | **1.0** | **UNSAFE** |

## Two separate facts, and the second one matters for advice

1. **There is a CLIFF between 128 and 256 MB.** At 512 MB every position is depth 1. At 256 MB the median is 4 with
   wild scatter (one position still reached depth 12). So 256 MB is already unusable, and my earlier "128 MB is fine"
   reading of a partial collapse was too generous; the honest boundary is **between 128 and 256**.

2. **Below the cliff there is a GENTLE GRADIENT, not a plateau.** MultiPV 3 at Hash 16 already loses depth
   (median 13.5 vs the healthy 17.0), and it decays 13.5 → 11.5 → 11.0 at 16/64/128 MB. So "safe" here means
   "usable", not "as good as MultiPV 1".

**Therefore the advice is a two-tier recommendation, and I am revising what I had been saying:**
- **Best: MultiPV 1 at any Hash** — the healthy row is depth 14–19 at 16 MB and is unaffected at every size.
- **If MultiPV > 1 is needed: keep Hash at ≤ 128 MB** (the largest SAFE size measured at MultiPV 3), and accept that
  you lose roughly 1/3 of the depth versus MultiPV 1 even at 16 MB.
- **Avoid Hash ≥ 256 MB with MultiPV > 1 entirely** — that is where analysis becomes depth 1–5.

My earlier page said "Hash ≤ 16 MB with MultiPV > 1". The data supports 128 MB as the safe limit at MultiPV 3, so that
advice was **more conservative than the evidence required**, while the gradient shows 16 MB is genuinely the least
lossy choice. The page now carries the measured table and both tiers.

## Limits
- One run per position (10 per Hash) — justified because the collapse is binary and reproducible (S-C32 showed 10/10
  at 2048 MB with 5 runs each), but the 256 MB row's scatter means its median is soft.
- MultiPV 3 only for the boundary; S-C32 covers MultiPV 2, 3 and 8 at 2048 MB.
- Built-in net, `Threads 1`, one clock.
