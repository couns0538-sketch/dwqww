# seat 20 — job 71: the long-game boundary BREAKS the candidate — the gap I refused to let slide was real

S-C44 left one declared gap: *"20 seconds is not a 40-move game; a table that holds at depth 20 may not at depth 35."*
I tested it. **The 8 MB alternate table does not hold on deep endgames**, and my pre-stated tolerance **fails**.

## Setup
12 G-set positions with **material ≤ 20** (endgame-ish, where searches actually go deep), clock **10,000 ms**,
MultiPV 3, Threads 1. Candidate = own 8 MB alternate table at Hash 2048; reference = same build at Hash 16.
Tolerance, pre-stated as in S-C43: **p90 |diff| ≤ 100 cp and max ≤ 500 cp**.

## Result

| statistic | value | verdict |
|---|---|---|
| comparisons | 36 | — |
| median \|diff\| | **4 cp** | fine |
| **90th percentile** | **112 cp** | **OVER the 100 cp limit** |
| **max** | **253 cp** | within 500 |
| deepest depth reached | reference 23, candidate 23 | depth not the problem |

Per-position maxima: `253, 212, 117, 112` at the top end, and `0, 0, 2, 5, 11` at the bottom — so the failure is
concentrated in a minority of deep positions, not uniform.

**PRE-STATED TOLERANCE: FAIL.** Not marginal on the statistic that matters: 112 > 100.

## Why this is exactly what the open item predicted
In shallow positions (depth 13–15) an 8 MB alternate table is never stressed, so the candidate reproduced the
reference almost exactly (median 0 cp, max 73). At depth 23 the alternate lines search far more nodes and the smaller
table starts to **evict what the reference kept** — the very mechanism I named as "the likeliest place this breaks".
So the earlier "no saturation at 4× clock" result was **not** a saturation test at depth: doubling the clock on shallow
positions kept depth ~15, and only the endgame positions reached depth 23.

## What this means for the requirement
1. **A fixed 8 MB alternate table is not sufficient** for deep analysis. The S-F56 requirement —
   *restore depth without moving the alternate lines' scores* — is **not met by any of my four variants**
   (64 MB cap, sharing, 8 MB own, and by extension the repaired-but-uncapped build which does not restore depth at all).
2. **The honest next step is adaptive sizing**: start the alternate table small and grow it as its own
   `hashfull`/depth grows, so shallow analysis stays cheap and deep analysis gets the space. I have **not** built it.
3. **Alternatively the requirement itself may be wrong-headed**: perhaps the alternate lines simply need a table
   comparable to the main one, and the real fix is to make allocating it cheap (lazy zeroing / smaller cluster format)
   rather than making it small. That is a design question for whoever owns the search.

## The lesson I want on the record
I could have declared victory after S-C43/S-C44: median 0 cp, tolerance passed, MultiPV 8 best-case, no saturation at
4× clock. **Every one of those numbers was true and the conclusion would have been wrong.** The gap I kept naming as
"the honest boundary" was the actual answer, and it took a 10-second clock on low-material positions to find it.
**A declared gap has to be measured before a candidate is called ready.** That is a stronger version of RULE 0: check
the reference is working — *and* check the regime you did not test.

## Limits
- 12 positions, 10 s clock, MultiPV 3, Threads 1, built-in net; "endgame-ish" = material ≤ 20, which is a proxy for
  depth, not for game length.
- Depth 23 is deep but a 40-move game could go further; the true worst case is likely worse than 253 cp.
