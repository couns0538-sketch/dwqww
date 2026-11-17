# Sanitizer batch wall-time review

Snapshot: 2026-11-15T02:28:20.131Z

- Command start/end bound a batch process, including startup, protocol and shutdown overhead; they do not measure CPU time or search-only time.
- Union counts overlapping finalized batch intervals once. Sums are batch-duration sums, never CPU time.
- Elapsed window runs from first observed batch start to explicit report as-of. Gaps are unaccounted by these intervals; no blocked or missing time is credited as testing.
- Accepted/failed classification uses retained recorded audit status and command metadata hashes. Unrecorded successful exits remain unreviewed. Failed observations remain timed but are not clean coverage.
- Preliminary Step1 is separate and excluded from every final total. Declared but unrun protocols contribute zero.
- Final protocol discovery includes softnodes*-batches directories plus explicit --final-dir paths; rerun after new protocols are added.

| Scope | Batches accepted / failed / unreviewed / invalid | Elapsed window s | Batch union s | Sum of batch durations s | Unaccounted s |
|---|---:|---:|---:|---:|---:|
| softnodes-batches | 0 / 1 / 0 / 0 | 5376.608 | 22.310 | 22.310 | 5354.298 |
| softnodes-depth64-batches | 0 / 0 / 0 / 0 | — | 0.000 | 0.000 | — |
| softnodes-depth64-v2-batches | 0 / 0 / 0 / 0 | — | 0.000 | 0.000 | — |
| softnodes-extended-batches | 2 / 2 / 0 / 0 | 1389.370 | 192.800 | 377.752 | 1196.570 |
| Final protocols combined | 2 / 3 / 0 / 0 | 5376.608 | 215.110 | 400.062 | 5161.498 |
| Preliminary Step1 (separate) | 4 / 0 / 0 / 0 | 9578.102 | 753.413 | 753.413 | 8824.689 |

| Final batch | Recorded result | UTC start | UTC end | Duration s |
|---|---|---|---|---:|
| paired-softnodes-asan-off-t1-n2000-d0 | failed | 2026-11-15T00:58:43.523Z | 2026-11-15T00:59:05.833Z | 22.310 |
| extended-c01-paired-softnodes-asan-off-t1-n2000-d0 | accepted | 2026-11-15T02:05:10.761Z | 2026-11-15T02:08:14.867Z | 184.106 |
| extended-c01-paired-softnodes-asan-off-t2-n2000-d0 | failed | 2026-11-15T02:09:56.038Z | 2026-11-15T02:10:00.146Z | 4.108 |
| extended-c01-paired-softnodes-asan-on-t1-n2000-d0 | accepted | 2026-11-15T02:05:12.036Z | 2026-11-15T02:08:19.453Z | 187.417 |
| extended-c01-paired-softnodes-asan-on-t2-n2000-d0 | failed | 2026-11-15T02:09:57.467Z | 2026-11-15T02:09:59.588Z | 2.121 |

Final combined gaps (no credited batch interval):

- 2026-11-15T00:59:05.833Z to 2026-11-15T02:05:10.761Z: 3964.928 seconds.
- 2026-11-15T02:08:19.453Z to 2026-11-15T02:09:56.038Z: 96.585 seconds.
- 2026-11-15T02:10:00.146Z to 2026-11-15T02:28:20.131Z: 1099.985 seconds.

Metadata issues: 0. Full interval lists, per-status unions and input hashes are in the JSON output.

