# The longest pilot game needs a held-out check in the cutoff rehearsal

I timed 360 genuine native self-play games on this local machine to test D5’s use of the longest measured game plus a margin. I fixed three consecutive cohorts before running. In each cohort the first 40 games supplied the maximum and the following 80 checked it. All three pilot maxima were exceeded. The stopwatch starts before building the seeded opening and ends when the bound record returns in memory. Startup and disk writes are outside it.

| Slot | First 40 maximum | Next 80 maximum | Later games longer than first maximum |
|---|---:|---:|---:|
| 0 | 371.9 ms | 455.0 ms | 3 |
| 1 | 388.5 ms | 534.4 ms | 6 |
| 2 | 416.8 ms | 471.5 ms | 2 |

Across the 240 held-out games, 11 exceeded the observed maximum alone. Adding predeclared margins of 5%, 10%, 25% and 50% left 8, 5, 2 and 0 exceedances. Zero in this sample establishes no bound. The server rehearsal should report how many later games exceed its proposed dispatch lead at the planned worker count and home load. The independent hard stop still has to work when one does. These figures choose neither the paid machine’s dispatch margin nor its separate process-stop allowance.

Reproduction uses the local AVX2 build, frozen r67 net and 2,000 soft-node day workload, v1 diagnostic worker at a5c74106, run tailbench, root seed leadtail23, slots 0, 1, 2 and counters 1–120 in each, one active worker at a time. The 360 bound records contained 47,745 raw rows. SHA-256 of their per-record hex digests, each followed by LF in that order, is 49bfa882f91029fdc38260f5b710298d441995df0b81aba0a1ed6e596a685b88. Local timing and record-digest artifact has SHA-256 089db0f4600895a443ee8f5652b18dee402adb9ae58f381d401ec7bb3aea1e0d.
