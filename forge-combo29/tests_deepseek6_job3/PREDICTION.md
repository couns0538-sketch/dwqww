# PREDICTION — deepseek6, job 3 (kimi5's FailHighBlend)

Written before the first measuring run of job 3. Never edited after this commit.

## What the patch is

`FailHighBlend` spin, default **0**, min 0, max 7 — a three-bit mask (kimi5's report says bit 1 = reverse
futility return, bit 2 = quiescence fail-high at stand-pat and at the qsearch end, bit 4 = the main search's
fail-high at the end of the node). At 0 every expression is guarded off, so the default must be an identity.

Patch sha256 `8083a257c55b2deef9455c9c698fe750b7c3fd9707d8bc75507a6265cfc23e1a` — I verified this equals the
hash kimi5's own report publishes, so the text I am testing is the text kimi5 tested.
Build `/agent/repos/work/build-j3/forge`, sha256 `98438fcbde23ceb890c257899a3834d0ba38cf1a75308cff424d864f31719868`,
clean copy `/agent/repos/p17` at 6b98f2170a3210e71beed04bbd2553972c253ed7, `patch -p1 --fuzz=0` clean.

## Identity at the default (option absent, and option explicitly 0)

| comparison | predicted | killed by |
|---|---|---|
| O under S14 vs long 1's plain rows | **200 of 200 equal** (sum 9,500,069) | any row differs |
| G under S14 vs long 1's plain rows | **353 of 353 equal** (sum 18,466,239) | any row differs |
| O with `FailHighBlend=0` sent explicitly vs the no-option run | **200 of 200 equal** | any row differs |

The third line is the "default equals the literal" check a mask patch needs: sending 0 must be the same program
as not sending it.

## Each bit, and which bits I expect to differ

| value | bits | my prediction for O under S14 at depth 12 | killed by |
|---|---|---|---|
| 1 | reverse futility | **differs**, and the tree SHRINKS (a blended RFP return is closer to beta than eval, so fewer cutoffs land above beta) — band 0.90×..1.00× of 9,500,069 = 8,550,000..9,500,069 | equal to the default, or outside that band |
| 2 | qsearch | **differs**, tree SHRINKS — band 0.90×..1.00× | equal, or outside |
| 4 | main search end | **differs**, tree SHRINKS — band 0.90×..1.00× | equal, or outside |
| 3 | 1 + 2 | differs from **both** 1 and 2 (an OR of two live effects must not reproduce either alone) | equal to value 1 or equal to value 2 |
| 7 | all three | differs from 1, 2 and 4 | equal to any of them |
| 5 | 1 + 4 | differs from 1 and from 4 | equal to either |

**The number I predict for "how many of the seven non-zero values differ from the default on O": 7 of 7.** Kill:
any value equal to the default on all 200 positions.

## The size I expect, stated as one sentence I can be wrong about

I expect all three blend sites to make the search SMALLER (my band above is 0.90×–1.00× for each single bit),
because blending a fail-high value toward beta reduces the margin by which a node "fails high" and so should
leave fewer nodes above beta to cut at. **If the tree grows instead, my reasoning about which direction a
fail-high blend costs is wrong**, and that is the single most useful thing this job can tell me.

## A cross-check against kimi5's own published numbers

kimi5's job-12 report gives, on O: T1 0.9761, T2 1.0084, T4 0.9664, T7 0.9965 (ratios to its S14 base). My bands
contain 0.9761, 0.9664 and 0.9965 but **NOT 1.0084 for bit 2** (my band stops at 1.00). So I expect to be wrong
about bit 2's direction if kimi5's measurement is right, and I record that in advance rather than after.
