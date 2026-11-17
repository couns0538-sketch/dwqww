# Response-deadline diagnostics

Snapshot 2026-11-15T03:39:32.828Z; source d9a8587df8ad4d0ff1231632cb1ac72b590c04bf. 42/42 saved audits reproduced. Zero soak credit. Original failed batches and all previous audits remain unchanged.

Each diagnostic is a fresh process with the exact recorded full move history. It reconstructs board/repetition history but not the original warm TT/search state. Release depth9 and depth12 each use a separate fresh process; no warm-depth12 rows are mixed into the table.

| Build / position / threads / target | Attempts | Natural target completions | Response timeouts | Blocked/unexpected | Normal exits | Completed-target nodes min–max | Completed-target reported ms min–max |
|---|---:|---:|---:|---:|---:|---:|---:|
| tsan/case4/t2/d9 | 1 | 1 | 0 | 0 | 1 | 2804280–2804280 | 16638–16638 |
| tsan/case10/t2/d9 | 1 | 1 | 0 | 0 | 1 | 865389–865389 | 7320–7320 |
| release/case4/t1/d9 | 5 | 5 | 0 | 0 | 5 | 10121–10121 | 4–6 |
| release/case4/t1/d12 | 5 | 5 | 0 | 0 | 5 | 58553–58553 | 22–32 |
| release/case4/t2/d9 | 5 | 5 | 0 | 0 | 5 | 992145–3684319 | 132–486 |
| release/case4/t2/d12 | 5 | 5 | 0 | 0 | 5 | 3600466–16711738 | 410–1805 |
| release/case10/t1/d9 | 5 | 5 | 0 | 0 | 5 | 9596–9596 | 3–4 |
| release/case10/t1/d12 | 5 | 5 | 0 | 0 | 5 | 41173–41173 | 14–20 |
| release/case10/t2/d9 | 5 | 5 | 0 | 0 | 5 | 594403–1426601 | 101–251 |
| release/case10/t2/d12 | 5 | 5 | 0 | 0 | 5 | 18248572–35892370 | 2679–5867 |

Pending native rows: 0; finalized without a saved root audit: 0; audit parse errors: 0. A successful audit can describe a valid timeout; it is not a completed search.

Full exact per-depth values, source lines, every process outcome and audit identity are in SUMMARY.txt, SOURCE-LINES.txt and PROOFS.txt. Tables use only unbounded-score info lines before the pre-quit snapshot. Post-quit depth/bestmove output stays in raw transcripts and cannot confer target-depth completion.

## Node-count comparisons
- Case4, depth9: T1 completed nodes [10121, 10121, 10121, 10121, 10121]; T2 [1974509, 1608846, 992145, 3684319, 1986947]; timeouts T1/T2 0/0. All five T2 node counts exceed all five T1 counts in this release configuration. This supports a thread-dependent workload observation, without isolating its cause.
- Case4, depth12: T1 completed nodes [58553, 58553, 58553, 58553, 58553]; T2 [9075166, 3600466, 16711738, 10388638, 15091966]; timeouts T1/T2 0/0. All five T2 node counts exceed all five T1 counts in this release configuration. This supports a thread-dependent workload observation, without isolating its cause.
- Case10, depth9: T1 completed nodes [9596, 9596, 9596, 9596, 9596]; T2 [594403, 999974, 1314766, 803618, 1426601]; timeouts T1/T2 0/0. All five T2 node counts exceed all five T1 counts in this release configuration. This supports a thread-dependent workload observation, without isolating its cause.
- Case10, depth12: T1 completed nodes [41173, 41173, 41173, 41173, 41173]; T2 [23399486, 18566402, 35892370, 18248572, 24713954]; timeouts T1/T2 0/0. All five T2 node counts exceed all five T1 counts in this release configuration. This supports a thread-dependent workload observation, without isolating its cause.

The frozen source enables bare_king_mode with multiple workers when either side has only its king (search.cpp1628–1632). It excludes razoring, reverse futility and null pruning (1640,1646,1651), move-loop pruning (1798–1799), and late-move reduction (1948–1949). Both recorded roots satisfy that material predicate. This can explain a change in work in principle, but these diagnostics do not trace the guard or prove it alone caused any observed difference. No automatic classification of the original warm-state timeout as “only sanitizer overhead” is made.

No Elo, speed or regression claim is made. Original warm-state timeout recurrence has not been measured by these fresh-process diagnostics. Any new sanitizer, illegal-move, shutdown or process finding is listed separately and must be reviewed before continuation.
