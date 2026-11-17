All 40 release diagnostics completed before quit with legal returned moves, valid-range scores, normal exits and no diagnostics. Each comparison contains five runs per thread count. In all four comparisons, every Threads 2 reported node count exceeded every Threads 1 count. This is an observed difference in search work on these endings; no engine change was made.

| Position | Target depth | Threads 1 nodes (5 runs) | Threads 2 nodes (5 runs) |
|---|---:|---:|---:|
| Case 4 | 9 | 10,121 | 992,145–3,684,319 |
| Case 4 | 12 | 58,553 | 3,600,466–16,711,738 |
| Case 10 | 9 | 9,596 | 594,403–1,426,601 |
| Case 10 | 12 | 41,173 | 18,248,572–35,892,370 |

Case 4: `8/8/3k4/8/6P1/1Q3K2/8/8 b - - 0 54`, HindsightDepth=false and MateAlphaGuard=false. Case 10: `8/B2P4/2K5/P7/8/5k2/8/8 b - - 0 73`, both options true. Every search used Hash 16, OwnBook=false, UseNNUE=true and MultiPV=1 on the same frozen release binary. Both members of each thread comparison used the same options and exact full move history. Each depth got its own fresh process and ucinewgame; depth 12 inherited no depth-9 TT.

The two fresh Threads 2 TSan depth-9 diagnostics also completed normally and legally, with no sanitizer report: case 4 reported 2,804,280 nodes, 16,638 ms on its final info line and 16,647.6 ms observed response; case 10 reported 865,389 nodes, 7,320 ms on its final info line and 7,325.47 ms observed response. These are two individual observations, one per case. Case 4 exceeded the old 15-second allowance even with fresh state; neither run recreates the original warm-state experiment.

Source facts at d9a8587df8ad4d0ff1231632cb1ac72b590c04bf:

- `forge-combo29/src/search.cpp:25` defaults FORGE_BARE_KING_MATE_FIX to 1; the pinned release compile flags do not override it.
- Lines 1628–1632 require multiple workers and either side having only its king. Both recorded FENs satisfy the material predicate.
- The resulting bare_king_mode excludes razoring at 1640, reverse futility at 1646, null-move pruning at 1651, shallow move-loop pruning at 1798–1799 and late-move reduction at 1948–1949, subject to each surrounding guard.
- Reported info nodes are sampled at 2190 and printed at 2202; total_nodes at 1212–1219 includes the worker's local count plus other workers' published counts. These are the final exact-info snapshots, not an independently counted post-join total.

This is a concrete thread-dependent search-policy mechanism consistent with the larger node counts. The diagnostics did not trace the guard, disable it, or isolate its contribution from other multi-thread search behavior, so they do not prove that this guard alone caused the difference. The T2 scores and moves also varied across repeats; printed mate scores were not independently proven by this legality check. No speed, Elo or strength conclusion follows from these counts.

The original two 15-second warm-session failures remain failed with zero credit. Full move-history replay reconstructs board/repetition history, not the old TT and search histories. These 42 diagnostic searches receive zero soak credit and do not establish recurrence or nonrecurrence in the original warm state. No automatic classification as only sanitizer overhead is justified.

All 42 saved audits, their logger/native outputs and source/build inputs were independently hash-checked. Exact per-run arrays, reported times, full histories' input pins and source excerpts are in EVIDENCE.txt. Review performed only reads and scratch-report writes: no engines, Git or root-state changes.
