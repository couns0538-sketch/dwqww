> Owner subsequently authorized continued work. Counts below describe the original eight-hour window only. See SOAK_ALL_REPORT.md and PROGRESS.md for extension results.

# Eight-hour window checkpoint

Scheduled window: 2026-11-14T11:11:32Z to 2026-11-14T19:11:32Z. Last completed native match: 2026-11-14T17:45:34.390Z. Finalization resumed at 2026-11-14T19:14:57.329Z, after the workspace credit limit cleared. This is eight hours of elapsed schedule, not eight hours of uninterrupted testing. No new native workload was started after the scheduled end.

The last pre-interruption push was17:41:29.366UTC. The required10-minute push cadence and15-minute maximum gap were not maintained during the interruption. All completed retained batches are included; missing work is explicit.

| Comparison | Games | Wins | Losses | Draws | Five pair bins (LL,LD,DD-or-WL,DW,WW) |
|---|---:|---:|---:|---:|---|
| Merged vs lock |4000|1094|1177|1729|77,315,1272,286,50|
| ContHist4PlyRead on/off |4000|1152|1126|1722|115,474,797,498,116|
| NonPawnCorrection on/off |1600|454|427|719|31,188,346,193,42|
| LmrDeeperShallower on/off |0|—|—|—|not run|

All completed matches used nodes20000, Threads1, Hash16, OwnBookfalse, UHO paired openings, recover, and no adjudication. Completed runner audits report zero crash markers, illegal-move events, disconnects, stalls, aborted games or structural discrepancies. These are counts, not strength or speed results.

Default pins:312866 /862329 /4865609. Mate-score misses in the120-root,T2/T4,ten-repeat comparison: lock298/2400; merged0/2400. All100000 eligible search positions were compared, but the required equality gate FAILED on8 low-clock positions (10/10 fresh reproductions each);31 additional high-clock differences are retained. Four unchanged option-fixture comparisons fail; the original full KRK sanitizer attempts timed out, with completed split coverage recorded separately. No sanitizer diagnostic was observed in accepted runs; this does not prove race freedom.

Part4 found and recorded a concrete quiet-futility error at src/search.cpp:1398-1401. A forced five-ply mate is skipped inside depth5 because a centipawn estimate is compared with mate alpha. Fault092 contains full trigger/output and2/2 direct trace repetitions. The original mate17 root deadline was not disproved; its PV is truncated by cached-score reuse. Existing r3-23 and private guard experiments did not establish a complete reported-mate repair, so no source fix was applied.

Not done:2400 remaining NonPawn games; all4000 LMR games; broader sampled KRK audit; ten direct repetitions of fault092; a justified, validated <=60-line compile-OFF fix. The single full40x10 ASAN KRK invocations remain incomplete even though equivalent split coverage completed. All expected values remain unchanged.

See [main report](SOAK_ALL_REPORT.md), [faults](faults/), [Part4 follow-up](preparation/part4-origin-followup-results/FOLLOWUP_RESULTS.md), and [independent pruning review](preparation/part4-origin-final-independent-review/PASS9_AND_COUNTERFACTUALS.md).
