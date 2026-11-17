# seat 20 — job 70: hardening the own-8MB candidate — MultiPV 2/8 and the saturation test both hold

S-C43 passed at MultiPV 3 on 20 positions. Two gaps remained, both flagged as the likeliest places to break. Both
now measured. Candidate = own 8 MB alternate table at Hash 2048, against the **healthy** reference (same build,
Hash 16), `go wtime 5000`, Threads 1.

## MultiPV 2 and 8

| MultiPV | line comparisons | median \|diff\| | max \|diff\| | depth reference vs candidate |
|---|---|---|---|---|
| **2** | 16 | **0 cp** | **40 cp** | [16,14,13,14,14,17,16,13] vs [14,14,13,14,14,17,16,13] |
| **3** (S-C43) | 60 | **0 cp** | **73 cp** | median 14 vs 14 |
| **8** | 64 | **0 cp** | **30 cp** | [13,12,11,12,12,15,12,11] vs [13,11,11,12,12,15,12,11] |

**MultiPV 8 is the best case (max 30 cp over 64 comparisons), not the worst** — the opposite of my guess: with 8 lines
each alternate line searches a shallower tree anyway, so a smaller table costs them less.

## The saturation test (does 8 MB fill up with more time?)

`hashfull` of the alternate table is not exposed, so I used drift as the proxy: if 8 MB saturated, the candidate would
drift **away** from the reference as the clock grew.

| clock | max \|diff\| across all lines |
|---|---|
| 5,000 ms | 47 cp |
| **20,000 ms (4×)** | **58 cp** |

Drift grew 47 → 58 cp for a 4× longer search — **no saturation signature** on these positions, and depth stayed in
band (5 s: 14→14, 15→15, 13→13, 14→14, 14→15; 20 s: 20→17, 17→18, 17→17, 20→19, 15→15).

## What this adds up to

Across **three MultiPV settings and two clock lengths**, the candidate reproduces the healthy reference's alternate
lines with **median 0 cp** and a **worst case of 73 cp** (MultiPV 3), while restoring main-line depth from 1 to 13–15
at Hash 2048. Both original caveats are now measured rather than open:
- **MultiPV 2/8:** hold, and 8 is the best case.
- **Saturation at longer clocks:** no drift signature at 4× the clock.

## Still open, stated rather than implied

- **Long games / deep endgames are not covered.** 20 seconds is not a 40-move game, and a table that holds at depth 20
  may not at depth 35. That is the honest boundary of this evidence.
- **Bit-identical reproduction is still not achieved** (up to 73 cp), so **the tolerance question to the owner stands
  unchanged** — this job strengthens the case for accepting a tolerance; it does not settle it.
- G-set positions, built-in net, Threads 1.
