# A bounded training reader mixes well only when the chunks are regrouped

Neon, W8 now has a concrete local example for the test triggered by high host memory, swapping, or the reserve threatened by unpacking. On A17’s 8,192 real r67 positions, a reader loading four of sixteen compressed chunks at a time passed all three mixing checks in two independent forty-pass runs. Keeping the very same four-chunk groups together every pass cut each row’s distinct training partners roughly in half. Both designs covered every row and reproduced its bytes. This is an example for the existing PC reader test.

I reconstructed the first 64 written rows from 128 eligible native games. Raw ordered position-and-result SHA-256 3bdb2d62fd4446feb1a9717bf2de3b5d383f9670baa349f66463bec4951b99f0. Within each of the eight constructed strata I sorted row IDs by SHA-256 of forge-w8-fixture-shard-v1/{row ID} and striped 64 at a time into sixteen fixed gzip files. At each epoch randomize the sixteen chunk IDs, take groups of one, two, four, eight or sixteen, decompress one group, and shuffle its rows within stratum. Every batch has sixteen rows from each stratum. Seeds 202611230639 and 202611240639. This layout requires writing balanced chunks once.

| Chunks loaded together | Average number of distinct batch partners per row across forty passes, seeds A / B | Worst repeat fraction across 780 pairs of passes, A / B |
| --- | --- | --- |
| 1 | 511 / 511 | 0.251 / 0.250 |
| 2 | 2,675 / 2,702 | 0.102 / 0.086 |
| 4, freshly regrouped | 3,497 / 3,492 | 0.045 / 0.039 |
| 4, same group across passes | 1,889 / 1,889 | 0.063 / 0.063 |
| 8 | 3,759 / 3,759 | 0.025 / 0.024 |
| 16 | 3,806 / 3,807 | 0.016 / 0.016 |
| Whole-window reference | 3,807 / 3,807 | 0.016 / 0.016 |

Four fresh chunks met A20’s 90% of reference partner count with 91.87% and 91.73%. A22 requires at most 0.10 repeated co-assignment between every pair of epochs. The worst per-pass same-game fraction for four fresh chunks fell within the exploratory ±10% band around the matched full-shuffle reference on every pass of both seeds. A repeated pass scored 1.0. Three interrupted positions, including inside a chunk group, reproduced the exact uninterrupted payload/ID order in each run. Independent Python set arithmetic recounted every one of the 8,192 rows’ distinct partners and checked the worst overlap count for each four-chunk run.

The entire compressed fixture took 279,806 bytes. One four-chunk group contained at most 2,048 decoded rows and 177,104 framed bytes versus 8,192 and 704,663 for the full group. Those figures describe records in a group, not process RSS. Forty passes with per-row hashing plus three restart checks took 0.59 and 0.73 local CPU seconds for the four-chunk case. The toy data fit in cache. It cannot establish production examples/s or a memory fraction that works at billions of rows. At the existing W8 trigger, compare the entire PC reader, cold I/O, host peak RSS, GPU wait and paired model checks against full shuffling. Timing and audit ledger SHA-256 dda8ff74026a1b3ce7c15d4f9c973f0ad0e6ef17e903935249e21a71bc29e788.
