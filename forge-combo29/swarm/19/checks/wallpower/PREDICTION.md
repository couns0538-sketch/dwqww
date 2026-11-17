# PREDICTION - committed BEFORE measurement (19-C53: does the node saving become wall time?)

## Why this test exists - and the inconsistency that motivates it
Two established facts disagree in their implication:
1. **29-F42/F53: PC20 searches 10.7-11.9 % FEWER NODES than S14** at matched depth. (Seat 29.)
2. **19-C35 (mine): PC20's PER-NODE time cost is at most ~1.2 %** - bench 16, 10 alternating rounds, ratio
   1.0119, 95 % CI [0.9997, 1.0241]. A tight interval.
3. **29-F56: no measurable WALL-TIME difference** - 40 positions, median 41 vs 36 ms, ratio 1.0255,
   **CI [0.9085, 1.1647]**, n = 40.

**1 and 2 together PREDICT roughly 10-11 % less wall time. 3 did not find it.** These cannot all be right.
Seat 29's own CI is the weak link: **width ±13 %**, so it cannot see a 10 % effect.

## Power computed BEFORE running (applying trap 16 to myself)
From seat 29's CI, the implied sd of ln(paired time ratio) is **0.401**. At 80 % power, two-sided alpha .05:
- detect a **5 %** difference: **n = 504 pairs**
- detect an **8 %** difference: **n = 197 pairs**
- detect a **12 %** difference: **n =  87 pairs**

**So I commit to at least 120 pairs** (adequate for 12 %, and honest about not reaching 5 %).

## Setup fixed before running
- Positions: seat 27's 600 (I hold them locally, diverse, and independent of the set I used before);
  I take the **first 120**.
- **Fixed DEPTH 12** (so node counts differ and the node saving can show), Threads 1, Hash 16.
- Interleaved ABBA, **fresh process per search**, both builds in the same session.
- Timing: the engine's own reported `time` on the last PV line, which excludes process startup - I will also
  record externally-measured wall time and report both.
- Pairs where either search fails to reach depth 12 are excluded and counted.

## My prediction
1. **PC20's wall time will be LOWER than S14's, ratio ~0.88-0.93** (i.e. the ~11 % node saving does appear),
   because per-node cost is equal (19-C35) and nodes are fewer.
2. **I predict the ratio will be significantly below 1.0** - this contradicts 29-F56's "no measurable difference",
   and I expect the reason to be 29-F56's sample size, not a real disagreement.
3. **Kill condition for me:** if the CI on the ratio includes 1.0 with n >= 120, my prediction is wrong and
   seat 29's null stands at better power - in which case the per-node cost must be HIGHER than 19-C35 measured,
   and I will say so.

## What each outcome means
- ratio < 1.0 significantly -> **the node saving is real time**; PC20 is a speed win in wall time, and 29-F56's
  null was underpowered. This is the answer the owner needs.
- ratio ~ 1.0 with a tight CI -> **the node saving does NOT become time**, so per-node cost must be ~11 % higher
  than 19-C35's bench-based figure implied. That would make 19-C35's applicability to real positions the problem,
  and I would have to qualify it.
