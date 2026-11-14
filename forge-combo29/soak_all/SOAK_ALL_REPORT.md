# Eight-hour combined Forge integration and soak

Start: 2026-11-14T11:11:32Z. Scheduled end: 2026-11-14T19:11:32Z. Report snapshot: 2026-11-14T13:14:11.465Z.

Elapsed at snapshot: 122.66 minutes; current phase: 2C; recorded pushes: 20. Cloud VM only. Counts and measurements do not support an Elo, strength or speed conclusion.

Base: `fca0fb40c7e66fdf01e36f4b95ceb179ffee2fca`; merged source: `f27b1971e459581ad4c85b7015f6af83bbfd4af6`; unchanged lock: `16833ecc03b425586f91f4c8834dea8807bf4c22`. [Source provenance](../INTEGRATION_ALL.md), [progress](PROGRESS.md), [raw batches](batches/), [test matrix](TEST_MATRIX.md).

Recorded default pins: bench11 = 312,866; bench13 = 862,329; perft5 = 4,865,609.

## Phase summary

| Phase | Conditions | Recorded completed work | Status |
| --- | --- | --- | --- |
| Part 1 | Release, ASAN+UBSAN and TSan builds; existing tests and fixed node/perft pins. | 3 engine builds; 58 test checks; 5 nonzero checks; 0 sanitizer reports | Complete with four stale fixture comparisons and one incomplete full ASan attempt; reduced retry passed |
| 2A preparation | Retain all 40 supplied KRK roots; select generated KQK/KBBK using lock T1 positive exact mate scores. | 2,000 completed units; 2,442 trials; 402 selected generated; 0 faults | Complete: 40 KRK, 40 KQK and 40 KBBK roots frozen |
| 2A | 40 KRK + 40 KQK + 40 KBBK; lock and merged; T2/T4; depth 14; ten cold-state trials per group. | 480 completed units; 4,800 trials; 298 mate score misses; 55 original t12 criterion flags; 298 faults | Complete: merged 0/2,400 and lock 298/2,400 mate-score misses |
| 2B | 200 fixed-seed legal bare-king positions; lock and merged; depth 12; reported T1/T2 conditions. | 800 completed units; 800 trials; 0 faults | Complete: 800 depth-12 searches on 200 roots, both builds at Threads 1/2; no fault |
| 2C | Fixed corpus comparison; completed eligible positions and exclusions tracked separately. | 66,074 positions; 506 excluded; 7 differences low clock; 16 differences high clock; 7 fault positions | Running |
| 2D | Sanitizer self-play; inspect each batch for its exact node/depth/thread limits. | 194 games; 27,831 searches; 0 faults | Running |
| 2E | ThreadSanitizer runs; exact thread and search conditions remain in batch evidence. | No completed counts recorded | Pending; no completed counts recorded |
| 2F | ASAN+UBSAN self-play with all three new options enabled; exact limits remain in batch evidence. | No completed counts recorded | Pending; no completed counts recorded |
| 2G | t23 mate/fifty-move suites; unchanged expectations and complete test outputs retained. | No completed counts recorded | Pending; no completed counts recorded |
| 3-default | Merged defaults (candidate) versus unchanged lock (baseline). | No completed counts recorded | Pending; no completed counts recorded |
| 3-ContHist4PlyRead | Merged with only ContHist4PlyRead enabled versus merged with all three new options disabled. | No completed counts recorded | Pending; no completed counts recorded |
| 3-NonPawnCorrection | Merged with only NonPawnCorrection enabled versus merged with all three new options disabled. | No completed counts recorded | Pending; no completed counts recorded |
| 3-LmrDeeperShallower | Merged with only LmrDeeperShallower enabled versus merged with all three new options disabled. | No completed counts recorded | Pending; no completed counts recorded |
| Part4 | Mate-bound/PV investigation and optional sampled KRK audit; exact DTM checks, no universal correctness claim. | 4 uninstrumented searches; 1 instrumented searches; 1 independent known roots; 0 false bounds demonstrated | Known-root investigation complete; optional broader sampled audit pending |
| 2KRKsplit | Isolated unchanged existing ASAN KRK split retry 2/2: same deterministic40 roots,5 fresh-clear trials each,Threads2 Hash16 depth14; separate100 T1 checks | 2 tests completed; 200 t1 runs; 0 t1 misses; 400 main runs; 0 main misses; 0 no mate score; 0 non mating move; 0 sanitizer reports | Complete: two unchanged40x5 invocations; 0/400 main misses,0/200 T1 misses, no sanitizer report |

Counts below use committed state totals. A dash means unavailable or not applicable, never an inferred zero. Fault categories can overlap.

## Mate observations

| Build | Threads | Material | Trials | Mate-score misses | KRK criterion failures | Lost forced mate | Mate-bound failures | Faults | Shutdown faults | Unexpected exits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lock | 2 | KRK | 400 | 48 | 29 | 0 | 0 | 48 | 0 | 0 |
| lock | 2 | KQK | 400 | 53 | — | — | — | 53 | 0 | 0 |
| lock | 2 | KBBK | 400 | 62 | — | — | — | 62 | 0 | 0 |
| lock | 4 | KRK | 400 | 47 | 26 | 0 | 0 | 47 | 0 | 0 |
| lock | 4 | KQK | 400 | 38 | — | — | — | 38 | 0 | 0 |
| lock | 4 | KBBK | 400 | 50 | — | — | — | 50 | 0 | 0 |
| merged | 2 | KRK | 400 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| merged | 2 | KQK | 400 | 0 | — | — | — | 0 | 0 | 0 |
| merged | 2 | KBBK | 400 | 0 | — | — | — | 0 | 0 | 0 |
| merged | 4 | KRK | 400 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| merged | 4 | KQK | 400 | 0 | — | — | — | 0 | 0 | 0 |
| merged | 4 | KBBK | 400 | 0 | — | — | — | 0 | 0 | 0 |

A mate-score miss includes missing, nonpositive or bounded mate scores. The KRK criterion also flags a legal winning move whose exact DTM exceeds the claimed mate bound, or requested depth when no positive mate score is returned. “Lost forced mate” is the separate drawing-move condition. These columns must not be added together.

KRK uses the retained exact t12 retrograde algorithm with shared board/attack primitives, fresh halfmove-zero roots and no history-dependent draw model. KQK/KBBK roots were selected by a lock T1 positive exact mate score; the merged result never filtered selection. KQK/KBBK have no independent mate oracle. Ten recorded trials are ten group observations, not ten additional reproductions after a separate baseline. An incomplete PV is not a proof of false mate.

## Depth-12 measurements

| Build | Threads | Material | Trials | Reached depth | Early mate stop | Other unfinished depth | Reported nodes | Engine ms | Wall ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lock | 1 | KRK | 67 | 67 | 0 | 0 | 1,869,484 | 638 | 688.882 |
| lock | 1 | KQK | 67 | 67 | 0 | 0 | 3,533,102 | 1,219 | 1,267.47 |
| lock | 1 | KBBK | 66 | 66 | 0 | 0 | 1,841,473 | 735 | 783.357 |
| lock | 2 | KRK | 67 | 67 | 0 | 0 | 2,695,918 | 515 | 574.081 |
| lock | 2 | KQK | 67 | 67 | 0 | 0 | 5,187,922 | 1,002 | 1,053.52 |
| lock | 2 | KBBK | 66 | 66 | 0 | 0 | 2,653,500 | 565 | 625.698 |
| merged | 1 | KRK | 67 | 67 | 0 | 0 | 1,869,484 | 634 | 688.152 |
| merged | 1 | KQK | 67 | 67 | 0 | 0 | 3,533,102 | 1,237 | 1,287 |
| merged | 1 | KBBK | 66 | 66 | 0 | 0 | 1,841,473 | 715 | 761.291 |
| merged | 2 | KRK | 67 | 67 | 0 | 0 | 66,446,330 | 7,802 | 7,858.46 |
| merged | 2 | KQK | 67 | 67 | 0 | 0 | 372,545,627 | 37,728 | 37,789.9 |
| merged | 2 | KBBK | 66 | 66 | 0 | 0 | 271,756,563 | 35,409 | 35,470 |

These are sums of observed measurements under the listed conditions. Early mate stops are separate from reaching depth 12; wall time and engine-reported time differ. No speed conclusion is drawn.

## Match counts

All W–L–D and pair bins are from the candidate’s perspective. Default mode compares merged defaults with the lock. Each option mode compares the merged executable with only that option enabled against the merged executable with all three options disabled. Modes are kept separate.

Recorded match configuration: 20,000 nodes per move, Threads 1, Hash 16, OwnBook false, color-swapped pairs, UHO openings and `-recover`; exact commands, seeds, options and process results remain in batch artifacts. Pending rows describe planned conditions only.

| Mode | Games | Wins | Losses | Draws | Status |
| --- | --- | --- | --- | --- | --- |
| default | — | — | — | — | Pending; no completed counts recorded |
| ContHist4PlyRead | — | — | — | — | Pending; no completed counts recorded |
| NonPawnCorrection | — | — | — | — | Pending; no completed counts recorded |
| LmrDeeperShallower | — | — | — | — | Pending; no completed counts recorded |

| Mode | LL | LD | DD or WL | DW | WW | Complete pairs | Incomplete pairs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| default | — | — | — | — | — | — | — |
| ContHist4PlyRead | — | — | — | — | — | — | — |
| NonPawnCorrection | — | — | — | — | — | — | — |
| LmrDeeperShallower | — | — | — | — | — | — | — |

Pair bins correspond to candidate scores 0, ½, 1, 1½ and 2 across a color-swapped pair. The middle bin combines two draws with one win and one loss. Scored abnormal games remain in W–L–D and complete pair bins.

| Mode | Illegal events / games | Disconnect games | Stall games | Aborted games | Abnormal terminations | Crash markers | Audit errors |
| --- | --- | --- | --- | --- | --- | --- | --- |
| default | — / — | — | — | — | — | — | — |
| ContHist4PlyRead | — / — | — | — | — | — | — | — |
| NonPawnCorrection | — / — | — | — | — | — | — | — |
| LmrDeeperShallower | — / — | — | — | — | — | — | — |

A crash can appear as a disconnect. Log markers are occurrences, not additional distinct game failures; abnormal categories overlap. A completed match is not necessarily a passed audit. Failed or interrupted attempts retain their raw scored results below and must not be silently treated as successful batches.

## Existing tests and limitations

Existing test/check records: 61; nonzero checks: 6; reported sanitizer diagnostics: 0. The [test matrix](TEST_MATRIX.md) and raw outputs distinguish fixture mismatches, timeouts and engine failures. A nonzero fixture comparison is not automatically an engine crash.

Recorded KRK coverage: release T1 100, release T2 400, ASAN T1 100, ASAN T2 40. The original full ASAN 40×10 attempt timed out without completed counts; reduced successful coverage does not convert that attempt into a pass.

The unchanged t16 options/clamp fixtures omit newly advertised options. Their exact-output mismatches and repeated clean process exits remain recorded separately. Clock-fixture timings use documented observation guards, not exact scheduler guarantees. TSan findings and runtime limitations must be read from the recorded test outputs; building TSan alone is not evidence of a clean run.

Completed-unit totals exclude partial work; interrupted cleanup diagnostics remain evidence even when excluded from a completed frequency denominator. In particular, inspect partial records’ interrupted-trial and shutdown fields. For untraced self-play batches, searches/moves/games can be self-reported counters rather than independently enumerated raw observations. Sanitizer occurrences can repeat in mirrored logs and are not counts of distinct bugs.

<details>
<summary>Recorded notes and exceptions (preserved)</summary>

- Release and ASan/UBSan t16 options/clamp exact-output comparisons fail because their unchanged expected fixtures omit MultiPV, NnueFile, ContHist4PlyRead, NonPawnCorrection and LmrDeeperShallower advertisements. Both engine runs and search/OwnBook protocol checkers exit 0 with no sanitizer report. Raw diffs are retained; expectations are not edited.
- Full ASan/UBSan KRK40x10 attempt timed out at440seconds under concurrent sanitizer load; no completed results were printed and no pass is claimed. A bounded reduced retry follows.
- Checkpoint cadence exception: the interval from push at11:31:06.960Z to11:43:42.673Z was12min35.713sec, exceeding the requested10min target. Subsequent batch launches force a checkpoint when the preceding push is more than60sec old to bound the next interval.
- Part4 reproduction: required UseNNUE=false; both builds report mate17/25568nodes/b3f3 with15-ply PV. Independent KRK oracle confirms selectedmove forcesmatein17plies (within reported33-plybound). Scratch trace proves mate-valuedTT qsearch return with emptyPV. No falsebound demonstrated; no productionfix/switch added. Full report and exactline references in mate_pv_investigation.md.
- Phase2A complete: merged0/400 misses in each material/thread cell; lock Threads2/4 KRK48/47,KQK53/38,KBBK62/50 per400. All4800 returned moves legal; exact KRK oracle finds no loss of forced mate and no reported-bound violation.55 original-t12 criterion flags are slower winning moves beyond depth14 when no mate score was reported, not drawing moves.
- Initial2D batch did not enable per-search trace:194games/27831searches are driver self-reported with internal per-search legality/score checks and summary invariants; only final trigger is retained. Subsequent self-play batches enable full trace.
- The isolated unchanged ASan/UBSan40x10 KRK retry also timed out after435seconds with no sanitizer diagnostic and buffered test output unavailable. It contributes zero completed trials. Two40x5 invocations are planned to complete ten fresh-clear trials perroot within command limits; original timeouts remain recorded.
- Phase2B: all800 searches reacheddepth12 with legalmoves and clean exits. Threads1 move,score,bound,nodecount andcompleteddepth match exactly onall200roots; raw measurements retained in bare_king_depth12_measurements.txt.
- Both bounded ASan KRK40x5 invocations passed on the identical binary and deterministic roots: combined400 T2 trials and200 T1 references, zero misses or sanitizer reports. Original40x10 attempts remain incomplete.
- Required depth9 equality failed at halfmove76: FEN5k2/8/7p/1K5P/8/8/8/7q w - - 76 136. Both builds return b5c4 cp-1689 and the samePV; merged31749nodes versus lock32435. Initial pair plus10fresh reproductions differ. Recorded asfault084; source diagnosis pending, production unchanged.

These notes retain their original recording context; subsequent retry coverage is stated separately.

</details>

## Incomplete attempts and retries

| Attempt | Seed | Completed work retained | Partial work excluded | Resume cursor | Retry | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| [2A #1](batches/2A-0001.txt) | 8473201 | 287 completed units; 2,870 trials; 182 faults | 1 incomplete units; 1 partial trials excluded; 0 partial faults excluded | 287 | Attempt 2 recorded as retry; completion not inferred | driver retained partial work separately |
| [2A #2](batches/2A-0002.txt) | 8473201 | 116 completed units; 1,160 trials; 65 faults | 1 incomplete units; 6 partial trials excluded; 0 partial faults excluded | 403 | Attempt 3 recorded as retry; completion not inferred | driver retained partial work separately |
| [2KRKfull #1](batches/2KRKfull-0001.evidence/manifest.txt) | not_applicable | None recorded | See raw partial evidence | — | Attempt 2KRKsplit #1 and #2 (coverage split into5+5; originalsingleinvocation remains incomplete) recorded as retry; completion not inferred | expected exactly one actual config line; expected exactly one Threads-1 result; expected exactly one main SUMMARY; actual config does not match 40 10 2 16 14 1; incomplete or invalid T1 checks; incomplete or inconsistent main counts; test did not terminate normally within the budget |
| [2C #1](batches/2C-0001.txt) | 4754000 | 16,865 records completed; 16,750 positions | See raw partial evidence | — | Attempt 2 recorded as retry; completion not inferred | driver retained partial work separately |
| [2C #2](batches/2C-0002.txt) | 4754000 | 16,907 records completed; 16,775 positions | See raw partial evidence | — | Attempt 3 recorded as retry; completion not inferred | driver retained partial work separately |
| [2C #3](batches/2C-0003.txt) | 4754000 | 16,274 records completed; 16,139 positions | See raw partial evidence | — | Attempt 4 recorded as retry; completion not inferred | driver retained partial work separately |
| [2C #4](batches/2C-0004.txt) | 4754000 | 16,534 records completed; 16,410 positions | See raw partial evidence | — | Retry not recorded | driver retained partial work separately |

A retry link records a later attempt; it does not imply that every partial unit has completed. Retained completed units are already included once in phase totals.

## Findings and evidence audit

90 numbered files: 1 fixture; 89 soak.

<details>
<summary>Numbered findings and evidence</summary>

| File | Classification | Finding |
| --- | --- | --- |
| [001.txt](faults/001.txt) | fixture | t16 options/clamp stale expected advertisements:10/10 each fixture/build;40 clean engine exits, no sanitizer diagnostics |
| [002.txt](faults/002.txt) | soak | Endgame lock-t2-KRK KRK-000004; 6/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [003.txt](faults/003.txt) | soak | Endgame lock-t4-KRK KRK-000004; 6/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [004.txt](faults/004.txt) | soak | Endgame lock-t2-KRK KRK-000009; 7/10 mate-score misses, 0 illegal, 1 KRK nonmating, 0 mate-bound failures |
| [005.txt](faults/005.txt) | soak | Endgame lock-t4-KRK KRK-000009; 7/10 mate-score misses, 0 illegal, 3 KRK nonmating, 0 mate-bound failures |
| [006.txt](faults/006.txt) | soak | Endgame lock-t2-KRK KRK-000012; 5/10 mate-score misses, 0 illegal, 5 KRK nonmating, 0 mate-bound failures |
| [007.txt](faults/007.txt) | soak | Endgame lock-t4-KRK KRK-000012; 5/10 mate-score misses, 0 illegal, 5 KRK nonmating, 0 mate-bound failures |
| [008.txt](faults/008.txt) | soak | Endgame lock-t2-KRK KRK-000013; 5/10 mate-score misses, 0 illegal, 5 KRK nonmating, 0 mate-bound failures |
| [009.txt](faults/009.txt) | soak | Endgame lock-t4-KRK KRK-000013; 6/10 mate-score misses, 0 illegal, 6 KRK nonmating, 0 mate-bound failures |
| [010.txt](faults/010.txt) | soak | Endgame lock-t2-KRK KRK-000015; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [011.txt](faults/011.txt) | soak | Endgame lock-t4-KRK KRK-000015; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [012.txt](faults/012.txt) | soak | Endgame lock-t2-KRK KRK-000017; 1/10 mate-score misses, 0 illegal, 1 KRK nonmating, 0 mate-bound failures |
| [013.txt](faults/013.txt) | soak | Endgame lock-t4-KRK KRK-000019; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [014.txt](faults/014.txt) | soak | Endgame lock-t2-KRK KRK-000022; 4/10 mate-score misses, 0 illegal, 4 KRK nonmating, 0 mate-bound failures |
| [015.txt](faults/015.txt) | soak | Endgame lock-t4-KRK KRK-000022; 5/10 mate-score misses, 0 illegal, 5 KRK nonmating, 0 mate-bound failures |
| [016.txt](faults/016.txt) | soak | Endgame lock-t2-KRK KRK-000026; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [017.txt](faults/017.txt) | soak | Endgame lock-t4-KRK KRK-000026; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [018.txt](faults/018.txt) | soak | Endgame lock-t2-KRK KRK-000027; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [019.txt](faults/019.txt) | soak | Endgame lock-t4-KRK KRK-000027; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [020.txt](faults/020.txt) | soak | Endgame lock-t2-KRK KRK-000028; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [021.txt](faults/021.txt) | soak | Endgame lock-t4-KRK KRK-000028; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [022.txt](faults/022.txt) | soak | Endgame lock-t2-KRK KRK-000029; 5/10 mate-score misses, 0 illegal, 5 KRK nonmating, 0 mate-bound failures |
| [023.txt](faults/023.txt) | soak | Endgame lock-t4-KRK KRK-000029; 3/10 mate-score misses, 0 illegal, 3 KRK nonmating, 0 mate-bound failures |
| [024.txt](faults/024.txt) | soak | Endgame lock-t2-KRK KRK-000035; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [025.txt](faults/025.txt) | soak | Endgame lock-t4-KRK KRK-000035; 2/10 mate-score misses, 0 illegal, 1 KRK nonmating, 0 mate-bound failures |
| [026.txt](faults/026.txt) | soak | Endgame lock-t2-KRK KRK-000036; 8/10 mate-score misses, 0 illegal, 8 KRK nonmating, 0 mate-bound failures |
| [027.txt](faults/027.txt) | soak | Endgame lock-t4-KRK KRK-000036; 3/10 mate-score misses, 0 illegal, 3 KRK nonmating, 0 mate-bound failures |
| [028.txt](faults/028.txt) | soak | Endgame lock-t2-KQK KQK-000006; 8/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [029.txt](faults/029.txt) | soak | Endgame lock-t4-KQK KQK-000006; 6/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [030.txt](faults/030.txt) | soak | Endgame lock-t4-KQK KQK-000022; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [031.txt](faults/031.txt) | soak | Endgame lock-t2-KQK KQK-000024; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [032.txt](faults/032.txt) | soak | Endgame lock-t2-KQK KQK-000040; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [033.txt](faults/033.txt) | soak | Endgame lock-t4-KQK KQK-000040; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [034.txt](faults/034.txt) | soak | Endgame lock-t2-KQK KQK-000044; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [035.txt](faults/035.txt) | soak | Endgame lock-t4-KQK KQK-000044; 4/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [036.txt](faults/036.txt) | soak | Endgame lock-t2-KQK KQK-000046; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [037.txt](faults/037.txt) | soak | Endgame lock-t2-KQK KQK-000048; 4/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [038.txt](faults/038.txt) | soak | Endgame lock-t4-KQK KQK-000048; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [039.txt](faults/039.txt) | soak | Endgame lock-t4-KQK KQK-000066; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [040.txt](faults/040.txt) | soak | Endgame lock-t2-KQK KQK-000088; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [041.txt](faults/041.txt) | soak | Endgame lock-t2-KQK KQK-000094; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [042.txt](faults/042.txt) | soak | Endgame lock-t2-KBBK KBBK-000103; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [043.txt](faults/043.txt) | soak | Endgame lock-t4-KBBK KBBK-000103; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [044.txt](faults/044.txt) | soak | Endgame lock-t2-KBBK KBBK-000137; 7/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [045.txt](faults/045.txt) | soak | Endgame lock-t4-KBBK KBBK-000137; 8/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [046.txt](faults/046.txt) | soak | Endgame lock-t2-KQK KQK-000138; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [047.txt](faults/047.txt) | soak | Endgame lock-t2-KQK KQK-000140; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [048.txt](faults/048.txt) | soak | Endgame lock-t4-KQK KQK-000140; 4/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [049.txt](faults/049.txt) | soak | Endgame lock-t2-KQK KQK-000142; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [050.txt](faults/050.txt) | soak | Endgame lock-t2-KQK KQK-000148; 9/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [051.txt](faults/051.txt) | soak | Endgame lock-t4-KQK KQK-000148; 7/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [052.txt](faults/052.txt) | soak | Endgame lock-t2-KQK KQK-000156; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [053.txt](faults/053.txt) | soak | Endgame lock-t4-KQK KQK-000156; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [054.txt](faults/054.txt) | soak | Endgame lock-t2-KQK KQK-000166; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [055.txt](faults/055.txt) | soak | Endgame lock-t4-KQK KQK-000166; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [056.txt](faults/056.txt) | soak | Endgame lock-t2-KQK KQK-000172; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [057.txt](faults/057.txt) | soak | Endgame lock-t2-KQK KQK-000184; 4/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [058.txt](faults/058.txt) | soak | Endgame lock-t4-KQK KQK-000184; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [059.txt](faults/059.txt) | soak | Endgame lock-t2-KQK KQK-000194; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [060.txt](faults/060.txt) | soak | Endgame lock-t4-KQK KQK-000194; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [061.txt](faults/061.txt) | soak | Endgame lock-t2-KQK KQK-000196; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [062.txt](faults/062.txt) | soak | Endgame lock-t4-KQK KQK-000196; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [063.txt](faults/063.txt) | soak | Endgame lock-t2-KBBK KBBK-000369; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [064.txt](faults/064.txt) | soak | Endgame lock-t2-KBBK KBBK-000441; 6/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [065.txt](faults/065.txt) | soak | Endgame lock-t4-KBBK KBBK-000441; 6/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [066.txt](faults/066.txt) | soak | Endgame lock-t2-KBBK KBBK-000473; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [067.txt](faults/067.txt) | soak | Endgame lock-t2-KBBK KBBK-000533; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [068.txt](faults/068.txt) | soak | Endgame lock-t4-KBBK KBBK-000533; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [069.txt](faults/069.txt) | soak | Endgame lock-t2-KBBK KBBK-000801; 8/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [070.txt](faults/070.txt) | soak | Endgame lock-t4-KBBK KBBK-000801; 6/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [071.txt](faults/071.txt) | soak | Endgame lock-t2-KBBK KBBK-000955; 7/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [072.txt](faults/072.txt) | soak | Endgame lock-t4-KBBK KBBK-000955; 4/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [073.txt](faults/073.txt) | soak | Endgame lock-t2-KBBK KBBK-001203; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [074.txt](faults/074.txt) | soak | Endgame lock-t4-KBBK KBBK-001203; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [075.txt](faults/075.txt) | soak | Endgame lock-t2-KBBK KBBK-001401; 1/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [076.txt](faults/076.txt) | soak | Endgame lock-t4-KBBK KBBK-001401; 2/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [077.txt](faults/077.txt) | soak | Endgame lock-t2-KBBK KBBK-001577; 7/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [078.txt](faults/078.txt) | soak | Endgame lock-t4-KBBK KBBK-001577; 10/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [079.txt](faults/079.txt) | soak | Endgame lock-t2-KBBK KBBK-001601; 7/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [080.txt](faults/080.txt) | soak | Endgame lock-t4-KBBK KBBK-001601; 6/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [081.txt](faults/081.txt) | soak | Endgame lock-t2-KBBK KBBK-001615; 7/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [082.txt](faults/082.txt) | soak | Endgame lock-t4-KBBK KBBK-001615; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [083.txt](faults/083.txt) | soak | Endgame lock-t2-KBBK KBBK-001735; 3/10 mate-score misses, 0 illegal, 0 KRK nonmating, 0 mate-bound failures |
| [084.txt](faults/084.txt) | soak | Comparison fault at required-equality root; 10/10 additional fault pairs |
| [085.txt](faults/085.txt) | soak | Comparison fault at required-equality root; 10/10 additional fault pairs |
| [086.txt](faults/086.txt) | soak | Comparison fault at required-equality root; 10/10 additional fault pairs |
| [087.txt](faults/087.txt) | soak | Comparison fault at required-equality root; 10/10 additional fault pairs |
| [088.txt](faults/088.txt) | soak | Comparison fault at required-equality root; 10/10 additional fault pairs |
| [089.txt](faults/089.txt) | soak | Comparison fault at required-equality root; 10/10 additional fault pairs |
| [090.txt](faults/090.txt) | soak | Comparison fault at required-equality root; 10/10 additional fault pairs |

</details>

Optional audit snapshot: 2026-11-14T13:14:02.952Z; state SHA256 `15a437f4e587e307ecb113e13186aee4d8cdc1c47d04a46efe1c30022e32354c`; apply mode true; reported errors 0, warnings 2. This snapshot is not assumed to verify later state or active work. [Full audit](preparation/latest-audit.txt).

| Audited batch | Raw verification | Partial safety observations | Sanitizer occurrences |
| --- | --- | --- | --- |
| 2D:1 | Limited; see audit | 0 | 0 |
| 2Aprep:1 | Raw records inspected; see audit issues | 0 | 0 |
| 2Aprep:2 | Raw records inspected; see audit issues | 0 | 0 |
| 2A:1 | Raw records inspected; see audit issues | 0 | 0 |
| 2A:2 | Raw records inspected; see audit issues | 0 | 0 |
| 2A:3 | Raw records inspected; see audit issues | 0 | 0 |
| 2KRKfull:1 | Raw records inspected; see audit issues | 0 | 0 |
| 2B:1 | Raw records inspected; see audit issues | 0 | 0 |
| 2KRKsplit:1 | Raw records inspected; see audit issues | 0 | 0 |
| 2KRKsplit:2 | Raw records inspected; see audit issues | 0 | 0 |
| 2C:1 | Raw records inspected; see audit issues | 0 | 0 |
| 2C:2 | Raw records inspected; see audit issues | 0 | 0 |
| 2C:3 | Raw records inspected; see audit issues | 0 | 0 |
| 2C:4 | Raw records inspected; see audit issues | 0 | 0 |

<details>
<summary>Audit issues and limits</summary>

- warning: 2D:1 lacks --trace: search/move/game counts are self-reported, with SUMMARY invariants and emitted FAULT rows checked; no per-search replay enumeration available
- warning: 2KRKfull:1 incomplete existing-test invocation; zero completed coverage; native budget expired; incomplete status alone is not an engine fault
- Frequencies come only from complete raw recorded trial groups. Partial safety evidence has no completed reproduction frequency.
- No engine is executed by this auditor. Missing ten-run reproduction groups remain pending.
- Sanitizer marker locations are evidence occurrences, not a count of independent bugs. Mirrored logs can contain the same diagnostic.

</details>

<details>
<summary>All recorded counters (exact unchanged values)</summary>

This appendix preserves every state total, including overlapping categories and measurements omitted from compact tables. Raw batch outputs remain authoritative evidence; this renderer neither recomputes nor changes state.

| Phase | Recorded conditions | Recorded status |
| --- | --- | --- |
| Part1 | Three requested merges; release/ASan+UBSan/TSan builds; all16test folders; defaults pinned; unchanged expected fixtures | Complete with four stale fixture comparisons and one incomplete full ASan attempt; reduced retry passed |
| 2D | ASan+UBSan self-play, Threads1, Hash16, OwnBookfalse, defaults, nodes2000,8 seeded opening plies,300-ply cap | Running |
| 2Aprep | Lock-T1 selection and merged-T1 observations: retain40previousKRKroots; generateKQK/KBBK atdepth14; no merged-result filtering | Complete: 40 KRK, 40 KQK and 40 KBBK roots frozen |
| 2A | Frozen40KRK+40KQK+40KBBK, lock/merged, Threads2/4, depth14,10fresh-state trials perroot/build/thread; exactKRKoracle; noKQK/KBBKproofclaim | Complete: merged 0/2,400 and lock 298/2,400 mate-score misses |
| Part4 | Reported mate17/short-PV reproduction and exact KRK assessment; scratch-only trace; production source unchanged | Known-root investigation complete; optional broader sampled audit pending |
| 2B | 200 fixed-seed legal bare-king roots, no mate-score selection; lock and merged, Threads1/2, depth12; raw nodes and times only | Complete: 800 depth-12 searches on 200 roots, both builds at Threads 1/2; no fault |
| 2KRKsplit | Isolated unchanged existing ASAN KRK split retry 2/2: same deterministic40 roots,5 fresh-clear trials each,Threads2 Hash16 depth14; separate100 T1 checks | Complete: two unchanged40x5 invocations; 0/400 main misses,0/200 T1 misses, no sanitizer report |
| 2C | Four disjoint frozen corpus shards; cold depth9 comparisons; counts only | Running |

| Phase | Counter | Recorded value |
| --- | --- | --- |
| Part1 | engine_builds | 3 |
| Part1 | test_checks | 58 |
| Part1 | nonzero_checks | 5 |
| Part1 | sanitizer_reports | 0 |
| Part1 | clock_cases | 14 |
| Part1 | fixture_reproduction_runs | 40 |
| Part1 | release_krk_T1_runs | 100 |
| Part1 | release_krk_T2_runs | 400 |
| Part1 | asan_krk_T1_runs | 100 |
| Part1 | asan_krk_T2_runs | 40 |
| 2D | games | 194 |
| 2D | moves | 27831 |
| 2D | searches | 27831 |
| 2D | opening_moves | 1552 |
| 2D | faults | 0 |
| 2D | illegal | 0 |
| 2D | missing | 0 |
| 2D | badscore | 0 |
| 2D | mates | 146 |
| 2D | stalemates | 0 |
| 2D | repetitions | 24 |
| 2D | fifty | 13 |
| 2D | ply_caps | 2 |
| 2D | insufficient | 9 |
| 2D | batches | 1 |
| 2Aprep | completed_units | 2000 |
| 2Aprep | trials | 2442 |
| 2Aprep | faults | 0 |
| 2Aprep | selected_generated | 402 |
| 2Aprep | shutdown_faults | 0 |
| 2Aprep | unexpected_exits | 0 |
| 2Aprep | mate_score_misses | 0 |
| 2Aprep | krk_non_mating_moves | 0 |
| 2Aprep | loses_forced_mate | 0 |
| 2Aprep | mate_bound_violations | 0 |
| 2Aprep | batches | 2 |
| 2A | completed_units | 480 |
| 2A | trials | 4800 |
| 2A | faults | 298 |
| 2A | selected_generated | 0 |
| 2A | shutdown_faults | 0 |
| 2A | unexpected_exits | 0 |
| 2A | mate_score_misses | 298 |
| 2A | krk_non_mating_moves | 55 |
| 2A | loses_forced_mate | 0 |
| 2A | mate_bound_violations | 0 |
| 2A | groups.lock-t2-KBBK.trials | 400 |
| 2A | groups.lock-t2-KBBK.faults | 62 |
| 2A | groups.lock-t2-KBBK.nodes_reported | 12618950 |
| 2A | groups.lock-t2-KBBK.reported_ms | 2558 |
| 2A | groups.lock-t2-KBBK.wall_ms | 2851.203 |
| 2A | groups.lock-t2-KBBK.at_requested_depth | 400 |
| 2A | groups.lock-t2-KBBK.early_mate_termination | 0 |
| 2A | groups.lock-t2-KBBK.unfinished_depth | 0 |
| 2A | groups.lock-t2-KBBK.shutdown_faults | 0 |
| 2A | groups.lock-t2-KBBK.unexpected_exits | 0 |
| 2A | groups.lock-t2-KBBK.mate_score_misses | 62 |
| 2A | groups.lock-t2-KBBK.krk_non_mating_moves | 0 |
| 2A | groups.lock-t2-KBBK.loses_forced_mate | 0 |
| 2A | groups.lock-t2-KBBK.mate_bound_violations | 0 |
| 2A | groups.lock-t2-KQK.trials | 400 |
| 2A | groups.lock-t2-KQK.faults | 53 |
| 2A | groups.lock-t2-KQK.nodes_reported | 32448227 |
| 2A | groups.lock-t2-KQK.reported_ms | 6008 |
| 2A | groups.lock-t2-KQK.wall_ms | 6303.74 |
| 2A | groups.lock-t2-KQK.at_requested_depth | 400 |
| 2A | groups.lock-t2-KQK.early_mate_termination | 0 |
| 2A | groups.lock-t2-KQK.unfinished_depth | 0 |
| 2A | groups.lock-t2-KQK.shutdown_faults | 0 |
| 2A | groups.lock-t2-KQK.unexpected_exits | 0 |
| 2A | groups.lock-t2-KQK.mate_score_misses | 53 |
| 2A | groups.lock-t2-KQK.krk_non_mating_moves | 0 |
| 2A | groups.lock-t2-KQK.loses_forced_mate | 0 |
| 2A | groups.lock-t2-KQK.mate_bound_violations | 0 |
| 2A | groups.lock-t2-KRK.trials | 400 |
| 2A | groups.lock-t2-KRK.faults | 48 |
| 2A | groups.lock-t2-KRK.nodes_reported | 12008712 |
| 2A | groups.lock-t2-KRK.reported_ms | 2112 |
| 2A | groups.lock-t2-KRK.wall_ms | 2391.57 |
| 2A | groups.lock-t2-KRK.at_requested_depth | 400 |
| 2A | groups.lock-t2-KRK.early_mate_termination | 0 |
| 2A | groups.lock-t2-KRK.unfinished_depth | 0 |
| 2A | groups.lock-t2-KRK.shutdown_faults | 0 |
| 2A | groups.lock-t2-KRK.unexpected_exits | 0 |
| 2A | groups.lock-t2-KRK.mate_score_misses | 48 |
| 2A | groups.lock-t2-KRK.krk_non_mating_moves | 29 |
| 2A | groups.lock-t2-KRK.loses_forced_mate | 0 |
| 2A | groups.lock-t2-KRK.mate_bound_violations | 0 |
| 2A | groups.lock-t4-KBBK.trials | 400 |
| 2A | groups.lock-t4-KBBK.faults | 50 |
| 2A | groups.lock-t4-KBBK.nodes_reported | 16305119 |
| 2A | groups.lock-t4-KBBK.reported_ms | 1718 |
| 2A | groups.lock-t4-KBBK.wall_ms | 2061.941 |
| 2A | groups.lock-t4-KBBK.at_requested_depth | 400 |
| 2A | groups.lock-t4-KBBK.early_mate_termination | 0 |
| 2A | groups.lock-t4-KBBK.unfinished_depth | 0 |
| 2A | groups.lock-t4-KBBK.shutdown_faults | 0 |
| 2A | groups.lock-t4-KBBK.unexpected_exits | 0 |
| 2A | groups.lock-t4-KBBK.mate_score_misses | 50 |
| 2A | groups.lock-t4-KBBK.krk_non_mating_moves | 0 |
| 2A | groups.lock-t4-KBBK.loses_forced_mate | 0 |
| 2A | groups.lock-t4-KBBK.mate_bound_violations | 0 |
| 2A | groups.lock-t4-KQK.trials | 400 |
| 2A | groups.lock-t4-KQK.faults | 38 |
| 2A | groups.lock-t4-KQK.nodes_reported | 44264861 |
| 2A | groups.lock-t4-KQK.reported_ms | 4312 |
| 2A | groups.lock-t4-KQK.wall_ms | 4643.01 |
| 2A | groups.lock-t4-KQK.at_requested_depth | 400 |
| 2A | groups.lock-t4-KQK.early_mate_termination | 0 |
| 2A | groups.lock-t4-KQK.unfinished_depth | 0 |
| 2A | groups.lock-t4-KQK.shutdown_faults | 0 |
| 2A | groups.lock-t4-KQK.unexpected_exits | 0 |
| 2A | groups.lock-t4-KQK.mate_score_misses | 38 |
| 2A | groups.lock-t4-KQK.krk_non_mating_moves | 0 |
| 2A | groups.lock-t4-KQK.loses_forced_mate | 0 |
| 2A | groups.lock-t4-KQK.mate_bound_violations | 0 |
| 2A | groups.lock-t4-KRK.trials | 400 |
| 2A | groups.lock-t4-KRK.faults | 47 |
| 2A | groups.lock-t4-KRK.nodes_reported | 15993828 |
| 2A | groups.lock-t4-KRK.reported_ms | 1459 |
| 2A | groups.lock-t4-KRK.wall_ms | 1783.04 |
| 2A | groups.lock-t4-KRK.at_requested_depth | 400 |
| 2A | groups.lock-t4-KRK.early_mate_termination | 0 |
| 2A | groups.lock-t4-KRK.unfinished_depth | 0 |
| 2A | groups.lock-t4-KRK.shutdown_faults | 0 |
| 2A | groups.lock-t4-KRK.unexpected_exits | 0 |
| 2A | groups.lock-t4-KRK.mate_score_misses | 47 |
| 2A | groups.lock-t4-KRK.krk_non_mating_moves | 26 |
| 2A | groups.lock-t4-KRK.loses_forced_mate | 0 |
| 2A | groups.lock-t4-KRK.mate_bound_violations | 0 |
| 2A | groups.merged-t2-KBBK.trials | 400 |
| 2A | groups.merged-t2-KBBK.faults | 0 |
| 2A | groups.merged-t2-KBBK.nodes_reported | 2460350058 |
| 2A | groups.merged-t2-KBBK.reported_ms | 295740 |
| 2A | groups.merged-t2-KBBK.wall_ms | 296053.6 |
| 2A | groups.merged-t2-KBBK.at_requested_depth | 400 |
| 2A | groups.merged-t2-KBBK.early_mate_termination | 0 |
| 2A | groups.merged-t2-KBBK.unfinished_depth | 0 |
| 2A | groups.merged-t2-KBBK.shutdown_faults | 0 |
| 2A | groups.merged-t2-KBBK.unexpected_exits | 0 |
| 2A | groups.merged-t2-KBBK.mate_score_misses | 0 |
| 2A | groups.merged-t2-KBBK.krk_non_mating_moves | 0 |
| 2A | groups.merged-t2-KBBK.loses_forced_mate | 0 |
| 2A | groups.merged-t2-KBBK.mate_bound_violations | 0 |
| 2A | groups.merged-t2-KQK.trials | 400 |
| 2A | groups.merged-t2-KQK.faults | 0 |
| 2A | groups.merged-t2-KQK.nodes_reported | 839818242 |
| 2A | groups.merged-t2-KQK.reported_ms | 102108 |
| 2A | groups.merged-t2-KQK.wall_ms | 102408.8 |
| 2A | groups.merged-t2-KQK.at_requested_depth | 400 |
| 2A | groups.merged-t2-KQK.early_mate_termination | 0 |
| 2A | groups.merged-t2-KQK.unfinished_depth | 0 |
| 2A | groups.merged-t2-KQK.shutdown_faults | 0 |
| 2A | groups.merged-t2-KQK.unexpected_exits | 0 |
| 2A | groups.merged-t2-KQK.mate_score_misses | 0 |
| 2A | groups.merged-t2-KQK.krk_non_mating_moves | 0 |
| 2A | groups.merged-t2-KQK.loses_forced_mate | 0 |
| 2A | groups.merged-t2-KQK.mate_bound_violations | 0 |
| 2A | groups.merged-t2-KRK.trials | 400 |
| 2A | groups.merged-t2-KRK.faults | 0 |
| 2A | groups.merged-t2-KRK.nodes_reported | 298986005 |
| 2A | groups.merged-t2-KRK.reported_ms | 32329 |
| 2A | groups.merged-t2-KRK.wall_ms | 32606.5 |
| 2A | groups.merged-t2-KRK.at_requested_depth | 400 |
| 2A | groups.merged-t2-KRK.early_mate_termination | 0 |
| 2A | groups.merged-t2-KRK.unfinished_depth | 0 |
| 2A | groups.merged-t2-KRK.shutdown_faults | 0 |
| 2A | groups.merged-t2-KRK.unexpected_exits | 0 |
| 2A | groups.merged-t2-KRK.mate_score_misses | 0 |
| 2A | groups.merged-t2-KRK.krk_non_mating_moves | 0 |
| 2A | groups.merged-t2-KRK.loses_forced_mate | 0 |
| 2A | groups.merged-t2-KRK.mate_bound_violations | 0 |
| 2A | groups.merged-t4-KBBK.trials | 400 |
| 2A | groups.merged-t4-KBBK.faults | 0 |
| 2A | groups.merged-t4-KBBK.nodes_reported | 3587693225 |
| 2A | groups.merged-t4-KBBK.reported_ms | 240732 |
| 2A | groups.merged-t4-KBBK.wall_ms | 241085.3 |
| 2A | groups.merged-t4-KBBK.at_requested_depth | 400 |
| 2A | groups.merged-t4-KBBK.early_mate_termination | 0 |
| 2A | groups.merged-t4-KBBK.unfinished_depth | 0 |
| 2A | groups.merged-t4-KBBK.shutdown_faults | 0 |
| 2A | groups.merged-t4-KBBK.unexpected_exits | 0 |
| 2A | groups.merged-t4-KBBK.mate_score_misses | 0 |
| 2A | groups.merged-t4-KBBK.krk_non_mating_moves | 0 |
| 2A | groups.merged-t4-KBBK.loses_forced_mate | 0 |
| 2A | groups.merged-t4-KBBK.mate_bound_violations | 0 |
| 2A | groups.merged-t4-KQK.trials | 400 |
| 2A | groups.merged-t4-KQK.faults | 0 |
| 2A | groups.merged-t4-KQK.nodes_reported | 1342191895 |
| 2A | groups.merged-t4-KQK.reported_ms | 112201 |
| 2A | groups.merged-t4-KQK.wall_ms | 112580.20000000001 |
| 2A | groups.merged-t4-KQK.at_requested_depth | 400 |
| 2A | groups.merged-t4-KQK.early_mate_termination | 0 |
| 2A | groups.merged-t4-KQK.unfinished_depth | 0 |
| 2A | groups.merged-t4-KQK.shutdown_faults | 0 |
| 2A | groups.merged-t4-KQK.unexpected_exits | 0 |
| 2A | groups.merged-t4-KQK.mate_score_misses | 0 |
| 2A | groups.merged-t4-KQK.krk_non_mating_moves | 0 |
| 2A | groups.merged-t4-KQK.loses_forced_mate | 0 |
| 2A | groups.merged-t4-KQK.mate_bound_violations | 0 |
| 2A | groups.merged-t4-KRK.trials | 400 |
| 2A | groups.merged-t4-KRK.faults | 0 |
| 2A | groups.merged-t4-KRK.nodes_reported | 429437569 |
| 2A | groups.merged-t4-KRK.reported_ms | 29026 |
| 2A | groups.merged-t4-KRK.wall_ms | 29331.1 |
| 2A | groups.merged-t4-KRK.at_requested_depth | 400 |
| 2A | groups.merged-t4-KRK.early_mate_termination | 0 |
| 2A | groups.merged-t4-KRK.unfinished_depth | 0 |
| 2A | groups.merged-t4-KRK.shutdown_faults | 0 |
| 2A | groups.merged-t4-KRK.unexpected_exits | 0 |
| 2A | groups.merged-t4-KRK.mate_score_misses | 0 |
| 2A | groups.merged-t4-KRK.krk_non_mating_moves | 0 |
| 2A | groups.merged-t4-KRK.loses_forced_mate | 0 |
| 2A | groups.merged-t4-KRK.mate_bound_violations | 0 |
| 2A | batches | 3 |
| Part4 | uninstrumented_searches | 4 |
| Part4 | instrumented_searches | 1 |
| Part4 | independent_known_roots | 1 |
| Part4 | false_bounds_demonstrated | 0 |
| 2B | completed_units | 800 |
| 2B | trials | 800 |
| 2B | faults | 0 |
| 2B | selected_generated | 0 |
| 2B | shutdown_faults | 0 |
| 2B | unexpected_exits | 0 |
| 2B | mate_score_misses | 0 |
| 2B | krk_non_mating_moves | 0 |
| 2B | loses_forced_mate | 0 |
| 2B | mate_bound_violations | 0 |
| 2B | groups.lock-t1-KBBK.trials | 66 |
| 2B | groups.lock-t1-KBBK.faults | 0 |
| 2B | groups.lock-t1-KBBK.nodes_reported | 1841473 |
| 2B | groups.lock-t1-KBBK.reported_ms | 735 |
| 2B | groups.lock-t1-KBBK.wall_ms | 783.357 |
| 2B | groups.lock-t1-KBBK.at_requested_depth | 66 |
| 2B | groups.lock-t1-KBBK.early_mate_termination | 0 |
| 2B | groups.lock-t1-KBBK.unfinished_depth | 0 |
| 2B | groups.lock-t1-KBBK.shutdown_faults | 0 |
| 2B | groups.lock-t1-KBBK.unexpected_exits | 0 |
| 2B | groups.lock-t1-KBBK.mate_score_misses | 0 |
| 2B | groups.lock-t1-KBBK.krk_non_mating_moves | 0 |
| 2B | groups.lock-t1-KBBK.loses_forced_mate | 0 |
| 2B | groups.lock-t1-KBBK.mate_bound_violations | 0 |
| 2B | groups.lock-t1-KQK.trials | 67 |
| 2B | groups.lock-t1-KQK.faults | 0 |
| 2B | groups.lock-t1-KQK.nodes_reported | 3533102 |
| 2B | groups.lock-t1-KQK.reported_ms | 1219 |
| 2B | groups.lock-t1-KQK.wall_ms | 1267.47 |
| 2B | groups.lock-t1-KQK.at_requested_depth | 67 |
| 2B | groups.lock-t1-KQK.early_mate_termination | 0 |
| 2B | groups.lock-t1-KQK.unfinished_depth | 0 |
| 2B | groups.lock-t1-KQK.shutdown_faults | 0 |
| 2B | groups.lock-t1-KQK.unexpected_exits | 0 |
| 2B | groups.lock-t1-KQK.mate_score_misses | 0 |
| 2B | groups.lock-t1-KQK.krk_non_mating_moves | 0 |
| 2B | groups.lock-t1-KQK.loses_forced_mate | 0 |
| 2B | groups.lock-t1-KQK.mate_bound_violations | 0 |
| 2B | groups.lock-t1-KRK.trials | 67 |
| 2B | groups.lock-t1-KRK.faults | 0 |
| 2B | groups.lock-t1-KRK.nodes_reported | 1869484 |
| 2B | groups.lock-t1-KRK.reported_ms | 638 |
| 2B | groups.lock-t1-KRK.wall_ms | 688.882 |
| 2B | groups.lock-t1-KRK.at_requested_depth | 67 |
| 2B | groups.lock-t1-KRK.early_mate_termination | 0 |
| 2B | groups.lock-t1-KRK.unfinished_depth | 0 |
| 2B | groups.lock-t1-KRK.shutdown_faults | 0 |
| 2B | groups.lock-t1-KRK.unexpected_exits | 0 |
| 2B | groups.lock-t1-KRK.mate_score_misses | 0 |
| 2B | groups.lock-t1-KRK.krk_non_mating_moves | 0 |
| 2B | groups.lock-t1-KRK.loses_forced_mate | 0 |
| 2B | groups.lock-t1-KRK.mate_bound_violations | 0 |
| 2B | groups.lock-t2-KBBK.trials | 66 |
| 2B | groups.lock-t2-KBBK.faults | 0 |
| 2B | groups.lock-t2-KBBK.nodes_reported | 2653500 |
| 2B | groups.lock-t2-KBBK.reported_ms | 565 |
| 2B | groups.lock-t2-KBBK.wall_ms | 625.698 |
| 2B | groups.lock-t2-KBBK.at_requested_depth | 66 |
| 2B | groups.lock-t2-KBBK.early_mate_termination | 0 |
| 2B | groups.lock-t2-KBBK.unfinished_depth | 0 |
| 2B | groups.lock-t2-KBBK.shutdown_faults | 0 |
| 2B | groups.lock-t2-KBBK.unexpected_exits | 0 |
| 2B | groups.lock-t2-KBBK.mate_score_misses | 0 |
| 2B | groups.lock-t2-KBBK.krk_non_mating_moves | 0 |
| 2B | groups.lock-t2-KBBK.loses_forced_mate | 0 |
| 2B | groups.lock-t2-KBBK.mate_bound_violations | 0 |
| 2B | groups.lock-t2-KQK.trials | 67 |
| 2B | groups.lock-t2-KQK.faults | 0 |
| 2B | groups.lock-t2-KQK.nodes_reported | 5187922 |
| 2B | groups.lock-t2-KQK.reported_ms | 1002 |
| 2B | groups.lock-t2-KQK.wall_ms | 1053.52 |
| 2B | groups.lock-t2-KQK.at_requested_depth | 67 |
| 2B | groups.lock-t2-KQK.early_mate_termination | 0 |
| 2B | groups.lock-t2-KQK.unfinished_depth | 0 |
| 2B | groups.lock-t2-KQK.shutdown_faults | 0 |
| 2B | groups.lock-t2-KQK.unexpected_exits | 0 |
| 2B | groups.lock-t2-KQK.mate_score_misses | 0 |
| 2B | groups.lock-t2-KQK.krk_non_mating_moves | 0 |
| 2B | groups.lock-t2-KQK.loses_forced_mate | 0 |
| 2B | groups.lock-t2-KQK.mate_bound_violations | 0 |
| 2B | groups.lock-t2-KRK.trials | 67 |
| 2B | groups.lock-t2-KRK.faults | 0 |
| 2B | groups.lock-t2-KRK.nodes_reported | 2695918 |
| 2B | groups.lock-t2-KRK.reported_ms | 515 |
| 2B | groups.lock-t2-KRK.wall_ms | 574.081 |
| 2B | groups.lock-t2-KRK.at_requested_depth | 67 |
| 2B | groups.lock-t2-KRK.early_mate_termination | 0 |
| 2B | groups.lock-t2-KRK.unfinished_depth | 0 |
| 2B | groups.lock-t2-KRK.shutdown_faults | 0 |
| 2B | groups.lock-t2-KRK.unexpected_exits | 0 |
| 2B | groups.lock-t2-KRK.mate_score_misses | 0 |
| 2B | groups.lock-t2-KRK.krk_non_mating_moves | 0 |
| 2B | groups.lock-t2-KRK.loses_forced_mate | 0 |
| 2B | groups.lock-t2-KRK.mate_bound_violations | 0 |
| 2B | groups.merged-t1-KBBK.trials | 66 |
| 2B | groups.merged-t1-KBBK.faults | 0 |
| 2B | groups.merged-t1-KBBK.nodes_reported | 1841473 |
| 2B | groups.merged-t1-KBBK.reported_ms | 715 |
| 2B | groups.merged-t1-KBBK.wall_ms | 761.291 |
| 2B | groups.merged-t1-KBBK.at_requested_depth | 66 |
| 2B | groups.merged-t1-KBBK.early_mate_termination | 0 |
| 2B | groups.merged-t1-KBBK.unfinished_depth | 0 |
| 2B | groups.merged-t1-KBBK.shutdown_faults | 0 |
| 2B | groups.merged-t1-KBBK.unexpected_exits | 0 |
| 2B | groups.merged-t1-KBBK.mate_score_misses | 0 |
| 2B | groups.merged-t1-KBBK.krk_non_mating_moves | 0 |
| 2B | groups.merged-t1-KBBK.loses_forced_mate | 0 |
| 2B | groups.merged-t1-KBBK.mate_bound_violations | 0 |
| 2B | groups.merged-t1-KQK.trials | 67 |
| 2B | groups.merged-t1-KQK.faults | 0 |
| 2B | groups.merged-t1-KQK.nodes_reported | 3533102 |
| 2B | groups.merged-t1-KQK.reported_ms | 1237 |
| 2B | groups.merged-t1-KQK.wall_ms | 1287 |
| 2B | groups.merged-t1-KQK.at_requested_depth | 67 |
| 2B | groups.merged-t1-KQK.early_mate_termination | 0 |
| 2B | groups.merged-t1-KQK.unfinished_depth | 0 |
| 2B | groups.merged-t1-KQK.shutdown_faults | 0 |
| 2B | groups.merged-t1-KQK.unexpected_exits | 0 |
| 2B | groups.merged-t1-KQK.mate_score_misses | 0 |
| 2B | groups.merged-t1-KQK.krk_non_mating_moves | 0 |
| 2B | groups.merged-t1-KQK.loses_forced_mate | 0 |
| 2B | groups.merged-t1-KQK.mate_bound_violations | 0 |
| 2B | groups.merged-t1-KRK.trials | 67 |
| 2B | groups.merged-t1-KRK.faults | 0 |
| 2B | groups.merged-t1-KRK.nodes_reported | 1869484 |
| 2B | groups.merged-t1-KRK.reported_ms | 634 |
| 2B | groups.merged-t1-KRK.wall_ms | 688.152 |
| 2B | groups.merged-t1-KRK.at_requested_depth | 67 |
| 2B | groups.merged-t1-KRK.early_mate_termination | 0 |
| 2B | groups.merged-t1-KRK.unfinished_depth | 0 |
| 2B | groups.merged-t1-KRK.shutdown_faults | 0 |
| 2B | groups.merged-t1-KRK.unexpected_exits | 0 |
| 2B | groups.merged-t1-KRK.mate_score_misses | 0 |
| 2B | groups.merged-t1-KRK.krk_non_mating_moves | 0 |
| 2B | groups.merged-t1-KRK.loses_forced_mate | 0 |
| 2B | groups.merged-t1-KRK.mate_bound_violations | 0 |
| 2B | groups.merged-t2-KBBK.trials | 66 |
| 2B | groups.merged-t2-KBBK.faults | 0 |
| 2B | groups.merged-t2-KBBK.nodes_reported | 271756563 |
| 2B | groups.merged-t2-KBBK.reported_ms | 35409 |
| 2B | groups.merged-t2-KBBK.wall_ms | 35470 |
| 2B | groups.merged-t2-KBBK.at_requested_depth | 66 |
| 2B | groups.merged-t2-KBBK.early_mate_termination | 0 |
| 2B | groups.merged-t2-KBBK.unfinished_depth | 0 |
| 2B | groups.merged-t2-KBBK.shutdown_faults | 0 |
| 2B | groups.merged-t2-KBBK.unexpected_exits | 0 |
| 2B | groups.merged-t2-KBBK.mate_score_misses | 0 |
| 2B | groups.merged-t2-KBBK.krk_non_mating_moves | 0 |
| 2B | groups.merged-t2-KBBK.loses_forced_mate | 0 |
| 2B | groups.merged-t2-KBBK.mate_bound_violations | 0 |
| 2B | groups.merged-t2-KQK.trials | 67 |
| 2B | groups.merged-t2-KQK.faults | 0 |
| 2B | groups.merged-t2-KQK.nodes_reported | 372545627 |
| 2B | groups.merged-t2-KQK.reported_ms | 37728 |
| 2B | groups.merged-t2-KQK.wall_ms | 37789.9 |
| 2B | groups.merged-t2-KQK.at_requested_depth | 67 |
| 2B | groups.merged-t2-KQK.early_mate_termination | 0 |
| 2B | groups.merged-t2-KQK.unfinished_depth | 0 |
| 2B | groups.merged-t2-KQK.shutdown_faults | 0 |
| 2B | groups.merged-t2-KQK.unexpected_exits | 0 |
| 2B | groups.merged-t2-KQK.mate_score_misses | 0 |
| 2B | groups.merged-t2-KQK.krk_non_mating_moves | 0 |
| 2B | groups.merged-t2-KQK.loses_forced_mate | 0 |
| 2B | groups.merged-t2-KQK.mate_bound_violations | 0 |
| 2B | groups.merged-t2-KRK.trials | 67 |
| 2B | groups.merged-t2-KRK.faults | 0 |
| 2B | groups.merged-t2-KRK.nodes_reported | 66446330 |
| 2B | groups.merged-t2-KRK.reported_ms | 7802 |
| 2B | groups.merged-t2-KRK.wall_ms | 7858.46 |
| 2B | groups.merged-t2-KRK.at_requested_depth | 67 |
| 2B | groups.merged-t2-KRK.early_mate_termination | 0 |
| 2B | groups.merged-t2-KRK.unfinished_depth | 0 |
| 2B | groups.merged-t2-KRK.shutdown_faults | 0 |
| 2B | groups.merged-t2-KRK.unexpected_exits | 0 |
| 2B | groups.merged-t2-KRK.mate_score_misses | 0 |
| 2B | groups.merged-t2-KRK.krk_non_mating_moves | 0 |
| 2B | groups.merged-t2-KRK.loses_forced_mate | 0 |
| 2B | groups.merged-t2-KRK.mate_bound_violations | 0 |
| 2B | batches | 1 |
| 2KRKsplit | tests_completed | 2 |
| 2KRKsplit | t1_runs | 200 |
| 2KRKsplit | t1_misses | 0 |
| 2KRKsplit | main_runs | 400 |
| 2KRKsplit | main_misses | 0 |
| 2KRKsplit | no_mate_score | 0 |
| 2KRKsplit | non_mating_move | 0 |
| 2KRKsplit | sanitizer_reports | 0 |
| 2KRKsplit | batches | 2 |
| 2C | records_completed | 66580 |
| 2C | positions | 66074 |
| 2C | positions_low_clock | 66049 |
| 2C | positions_high_clock | 25 |
| 2C | differences_low_clock | 7 |
| 2C | differences_high_clock | 16 |
| 2C | fault_positions | 7 |
| 2C | excluded | 506 |
| 2C | excluded_no_legal | 24 |
| 2C | excluded_insufficient | 481 |
| 2C | excluded_halfmove100 | 1 |
| 2C | invalid_fens | 0 |
| 2C | engine_runs | 132608 |
| 2C | illegal | 0 |
| 2C | missing | 0 |
| 2C | missing_info | 0 |
| 2C | wrong_depth | 0 |
| 2C | sanitizer_issues | 0 |
| 2C | transport_issues | 0 |
| 2C | crashes | 0 |
| 2C | nonzero_exits | 0 |
| 2C | shutdown_timeouts | 0 |
| 2C | reproduction_pairs | 230 |
| 2C | reproduction_differences | 230 |
| 2C | reproduction_fault_pairs | 70 |
| 2C | batches | 4 |

</details>

Raw commands, outputs, seeds, process statuses, manifests and source hashes remain in the linked evidence. Missing work and exclusions are retained explicitly; no result here is an Elo or speed claim.
