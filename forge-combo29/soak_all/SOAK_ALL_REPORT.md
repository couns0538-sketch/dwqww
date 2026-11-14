# Eight-hour combined Forge integration and soak

Start: 2026-11-14T11:11:32Z. Scheduled end: 2026-11-14T19:11:32Z. Report snapshot: 2026-11-14T17:03:34.742Z.

Elapsed at snapshot: 352.05 minutes; current phase: 3-ContHist4PlyRead; recorded pushes: 64. Cloud VM only. Counts and measurements do not support an Elo, strength or speed conclusion.

Base: `fca0fb40c7e66fdf01e36f4b95ceb179ffee2fca`; merged source: `f27b1971e459581ad4c85b7015f6af83bbfd4af6`; unchanged lock: `16833ecc03b425586f91f4c8834dea8807bf4c22`. [Source provenance](../INTEGRATION_ALL.md), [progress](PROGRESS.md), [raw batches](batches/), [test matrix](TEST_MATRIX.md).

Recorded default pins: bench11 = 312,866; bench13 = 862,329; perft5 = 4,865,609.

## Phase summary

| Phase | Conditions | Recorded completed work | Status |
| --- | --- | --- | --- |
| Part 1 | Release, ASAN+UBSAN and TSan builds; existing tests and fixed node/perft pins. | 3 engine builds; 58 test checks; 5 nonzero checks; 0 sanitizer reports | Initial checkpoint: Complete with four stale fixture comparisons and one incomplete full ASan attempt; reduced retry passed. Later completed split coverage is recorded under 2KRKsplit; original timeouts remain incomplete. |
| 2A preparation | Retain all 40 supplied KRK roots; select generated KQK/KBBK using lock T1 positive exact mate scores. | 2,000 completed units; 2,442 trials; 402 selected generated; 0 faults | Complete: 40 KRK, 40 KQK and 40 KBBK roots frozen |
| 2A | 40 KRK + 40 KQK + 40 KBBK; lock and merged; T2/T4; depth 14; ten cold-state trials per group. | 480 completed units; 4,800 trials; 298 mate score misses; 55 original t12 criterion flags; 298 faults | Complete: merged 0/2,400 and lock 298/2,400 mate-score misses |
| 2B | 200 fixed-seed legal bare-king positions; lock and merged; depth 12; reported T1/T2 conditions. | 800 completed units; 800 trials; 0 faults | Complete: 800 depth-12 searches on 200 roots, both builds at Threads 1/2; no fault |
| 2C | Fixed corpus comparison; completed eligible positions and exclusions tracked separately. | 100,000 positions; 715 excluded; 8 differences low clock; 31 differences high clock; 8 fault positions | Complete:100,000 positions; 8 required low-clock equality failures; 31 high-clock differences observed |
| 2D | Sanitizer self-play; inspect each batch for its exact node/depth/thread limits. | 1,131 games; 131,115 searches; 0 faults | Complete: 1131 games / 131115 searches; ASAN+UBSAN Threads1/2, nodes2000/20000; no chess/runtime diagnostics |
| 2E | ThreadSanitizer runs; exact thread and search conditions remain in batch evidence. | 56 games; 8,297 searches; 0 faults | Complete: 56 games / 8297 searches; TSan Threads2/4; no warnings; original E5 timeout excluded and retry completed |
| 2F | ASAN+UBSAN self-play plus supplemental TSan with all three new options enabled; exact instrumentation and limits remain in batch evidence. | 1,116 games; 128,418 searches; 0 faults | Complete: 1102 ASAN+UBSAN games / 126532 searches plus14 enabled-option TSan games /1886 searches; no chess/runtime diagnostics |
| 2G | t23 mate/fifty-move suites; unchanged expectations and complete test outputs retained. | 4 tests completed; 120 cases; 60 mate cases; 20 nonmate cases; 40 rule50 cases; 0 sanitizer reports | Complete: four unchanged suite runs; 120 cases; zero missed/false mates, illegal moves, rule50 failures, or sanitizer reports |
| 3-default | Merged defaults (candidate) versus unchanged lock (baseline). | 4,000 games; 1,094 wins; 1,177 losses; 1,729 draws; 0 audit errors | Complete:4000 games,2000 color-swapped UHO pairs; W-L-D1094-1177-1729; no crash/illegal/disconnect/stall/abort marker or event; counts only |
| 3-ContHist4PlyRead | Merged with only ContHist4PlyRead enabled versus merged with all three new options disabled. | 2,000 games; 558 wins; 541 losses; 901 draws; 0 audit errors | Running |
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

## Sanitizer self-play outcomes

Chess fault counters, runtime failures and sanitizer warnings are separate observations. A chess summary with zero faults does not establish a clean sanitizer run. Counts in this section come only from matched finished batches in the supplied audit snapshot; state game/search totals remain unchanged.

Audit snapshot: 2026-11-14T15:55:27.421Z; reported reconciliation errors 0. Batch identity, finish time, recorded counts and available exit/signal are matched to state. This renderer does not assert that the audit state hash matches current state.

| Phase | Audited / finished attempts | With canonical counts | With process classification | TSan warning blocks | Unresolved blocks | Nonzero exits | Runtime/diagnostic affected | Timeout/forced |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2D | 8 / 8 | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| 2E | 8 / 8 | 8 | 8 | 0 | 0 | 1 | 0 | 1 |
| 2F | 10 / 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 |

Coverage includes finished attempts with no committed chess counts. A dash means unavailable, not zero. Nonzero exits, runtime diagnostics and timeouts can overlap; timeout/forced termination is not labelled an engine crash. ASan/UBSan marker lines are not TSan warning events.

<details>
<summary>Per-batch sanitizer and process evidence</summary>

| Batch | Finished UTC | Threads | Depth / node setting | Candidate flags | Counted games / searches / chess faults | Exit / signal | Runtime classification | Runtime marker lines | Canonical TSan warnings | Resolved groups / unresolved blocks | TSan footer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [2D #1](batches/2D-0001.txt) | 2026-11-14T11:58:57.355Z | 1 | 0 / 2,000 | false / false / false | 194 / 27,831 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2D #2](batches/2D-0002.txt) | 2026-11-14T13:32:31.315Z | 2 | 0 / 2,000 | false / false / false | 319 / 30,660 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2E #1](batches/2E-0001.txt) | 2026-11-14T13:38:29.617Z | 2 | 9 / 0 | false / false / false | 11 / 1,525 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2E #2](batches/2E-0002.txt) | 2026-11-14T13:44:17.798Z | 4 | 9 / 0 | false / false / false | 7 / 1,200 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #1](batches/2F-0001.txt) | 2026-11-14T13:49:33.242Z | 1 | 0 / 2,000 | true / true / true | 190 / 26,119 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #2](batches/2F-0002.txt) | 2026-11-14T13:54:52.485Z | 2 | 0 / 2,000 | true / true / true | 315 / 30,495 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2D #3](batches/2D-0003.txt) | 2026-11-14T14:01:00.557Z | 1 | 0 / 20,000 | false / false / false | 21 / 2,742 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2D #4](batches/2D-0004.txt) | 2026-11-14T14:08:27.406Z | 2 | 0 / 20,000 | false / false / false | 30 / 4,454 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #3](batches/2F-0003.txt) | 2026-11-14T14:14:03.673Z | 1 | 0 / 20,000 | true / true / true | 16 / 2,687 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #4](batches/2F-0004.txt) | 2026-11-14T14:19:33.064Z | 2 | 0 / 20,000 | true / true / true | 25 / 4,279 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2E #3](batches/2E-0003.txt) | 2026-11-14T14:25:17.865Z | 2 | 9 / 0 | false / false / false | 4 / 762 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2E #4](batches/2E-0004.txt) | 2026-11-14T14:30:49.324Z | 4 | 9 / 0 | false / false / false | 10 / 1,559 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2D #5](batches/2D-0005.txt) | 2026-11-14T14:36:06.497Z | 1 | 0 / 2,000 | false / false / false | 200 / 27,144 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2D #6](batches/2D-0006.txt) | 2026-11-14T14:41:25.043Z | 2 | 0 / 2,000 | false / false / false | 316 / 31,104 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #5](batches/2F-0005.txt) | 2026-11-14T14:46:47.860Z | 1 | 0 / 2,000 | true / true / true | 183 / 26,054 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #6](batches/2F-0006.txt) | 2026-11-14T14:52:13.748Z | 2 | 0 / 2,000 | true / true / true | 321 / 30,005 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2E #5](batches/2E-0005.evidence/manifest.txt) | 2026-11-14T15:00:09.720Z | — | — / — | — / — / — | — / — / — | 124 / none | budget_timeout_or_forced_termination; not classified as engine crash | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2E #5r1](batches/2E-05r1.txt) | 2026-11-14T15:08:22.989Z | 2 | 9 / 0 | false / false / false | 7 / 1,026 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2E #6](batches/2E-0006.txt) | 2026-11-14T15:14:28.970Z | 4 | 9 / 0 | false / false / false | 7 / 1,050 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2D #7](batches/2D-0007.txt) | 2026-11-14T15:19:58.557Z | 1 | 0 / 20,000 | false / false / false | 19 / 2,621 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2D #8](batches/2D-0008.txt) | 2026-11-14T15:26:43.715Z | 2 | 0 / 20,000 | false / false / false | 32 / 4,559 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #7](batches/2F-0007.txt) | 2026-11-14T15:32:24.203Z | 1 | 0 / 20,000 | true / true / true | 17 / 2,789 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #8](batches/2F-0008.txt) | 2026-11-14T15:37:55.039Z | 2 | 0 / 20,000 | true / true / true | 35 / 4,104 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #11](batches/2F-0011.txt) | 2026-11-14T15:43:42.506Z | 2 | 9 / 0 | true / true / true | 5 / 771 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2F #12](batches/2F-0012.txt) | 2026-11-14T15:49:45.862Z | 4 | 9 / 0 | true / true / true | 9 / 1,115 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |
| [2E #7](batches/2E-0007.txt) | 2026-11-14T15:55:20.296Z | 2 | 9 / 0 | false / false / false | 10 / 1,175 / 0 | 0 / none | normal_exit | 0 | 0 | 0 / 0 | Unavailable / not applicable |

Conditions come from each retained raw SUMMARY, or its retained parsed SUMMARY when raw text is unavailable. Candidate order is ContHist4PlyRead / NonPawnCorrection / LmrDeeperShallower; literal booleans are shown. A positive depth setting selects depth-limited search; depth zero selects the node limit. Missing conditions are not inferred from the phase description or later batches.


Only canonical warning blocks from each primary runtime log enter the totals. Mirrored artifacts, WARNING/SUMMARY markers and runtime footers are not additional warnings. Runtime duplicate suppression can hide repeated manifestations; these counts are not reproduction frequencies.

</details>

No resolved source-line-pair groups are available in the matched audit data. This is not a clean-run claim; inspect unresolved blocks, missing coverage and process outcomes.

Audit coverage and grouping omissions:

- 2E:5: one or more per-batch condition fields unavailable; planned or latest phase conditions are not substituted.

## Match counts

All W–L–D and pair bins are from the candidate’s perspective. Default mode compares merged defaults with the lock. Each option mode compares the merged executable with only that option enabled against the merged executable with all three options disabled. Modes are kept separate.

Recorded match configuration: 20,000 nodes per move, Threads 1, Hash 16, OwnBook false, color-swapped pairs, UHO openings and `-recover`; exact commands, seeds, options and process results remain in batch artifacts. Pending rows describe planned conditions only.

| Mode | Games | Wins | Losses | Draws | Status |
| --- | --- | --- | --- | --- | --- |
| default | 4,000 | 1,094 | 1,177 | 1,729 | Complete:4000 games,2000 color-swapped UHO pairs; W-L-D1094-1177-1729; no crash/illegal/disconnect/stall/abort marker or event; counts only |
| ContHist4PlyRead | 2,000 | 558 | 541 | 901 | Running |
| NonPawnCorrection | — | — | — | — | Pending; no completed counts recorded |
| LmrDeeperShallower | — | — | — | — | Pending; no completed counts recorded |

| Mode | LL | LD | DD or WL | DW | WW | Complete pairs | Incomplete pairs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| default | 77 | 315 | 1,272 | 286 | 50 | 2,000 | 0 |
| ContHist4PlyRead | 58 | 226 | 411 | 251 | 54 | 1,000 | 0 |
| NonPawnCorrection | — | — | — | — | — | — | — |
| LmrDeeperShallower | — | — | — | — | — | — | — |

Pair bins correspond to candidate scores 0, ½, 1, 1½ and 2 across a color-swapped pair. The middle bin combines two draws with one win and one loss. Scored abnormal games remain in W–L–D and complete pair bins.

| Mode | Illegal events / games | Disconnect games | Stall games | Aborted games | Abnormal terminations | Crash markers | Audit errors |
| --- | --- | --- | --- | --- | --- | --- | --- |
| default | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ContHist4PlyRead | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| NonPawnCorrection | — / — | — | — | — | — | — | — |
| LmrDeeperShallower | — / — | — | — | — | — | — | — |

A crash can appear as a disconnect. Log markers are occurrences, not additional distinct game failures; abnormal categories overlap. A completed match is not necessarily a passed audit. Failed or interrupted attempts retain their raw scored results below and must not be silently treated as successful batches.

<details>
<summary>Match batch coverage, including failed and incomplete attempts</summary>

| Batch | Seed | Recorded totals? | Completed / passed | Raw W–L–D | Complete / incomplete pairs | Runner result |
| --- | --- | --- | --- | --- | --- | --- |
| [3-default #1](batches/3-default-0001.txt) | 8474001 | Yes; see retained counts | true / true | 113–107–180 | 200 / 0 | exit 0, signal — |
| [3-default #2](batches/3-default-0002.txt) | 8474002 | Yes; see retained counts | true / true | 110–122–168 | 200 / 0 | exit 0, signal — |
| [3-default #3](batches/3-default-0003.txt) | 8474003 | Yes; see retained counts | true / true | 94–125–181 | 200 / 0 | exit 0, signal — |
| [3-default #4](batches/3-default-0004.txt) | 8474004 | Yes; see retained counts | true / true | 114–130–156 | 200 / 0 | exit 0, signal — |
| [3-default #5](batches/3-default-0005.txt) | 8474005 | Yes; see retained counts | true / true | 118–117–165 | 200 / 0 | exit 0, signal — |
| [3-default #6](batches/3-default-0006.txt) | 8474006 | Yes; see retained counts | true / true | 106–108–186 | 200 / 0 | exit 0, signal — |
| [3-default #7](batches/3-default-0007.txt) | 8474007 | Yes; see retained counts | true / true | 114–124–162 | 200 / 0 | exit 0, signal — |
| [3-default #8](batches/3-default-0008.txt) | 8474008 | Yes; see retained counts | true / true | 117–116–167 | 200 / 0 | exit 0, signal — |
| [3-default #9](batches/3-default-0009.txt) | 8474009 | Yes; see retained counts | true / true | 103–122–175 | 200 / 0 | exit 0, signal — |
| [3-default #10](batches/3-default-0010.txt) | 8474010 | Yes; see retained counts | true / true | 105–106–189 | 200 / 0 | exit 0, signal — |
| [3-ContHist4PlyRead #1](batches/3-ContHist4PlyRead-0001.txt) | 8475001 | Yes; see retained counts | true / true | 104–112–184 | 200 / 0 | exit 0, signal — |
| [3-ContHist4PlyRead #2](batches/3-ContHist4PlyRead-0002.txt) | 8475002 | Yes; see retained counts | true / true | 130–106–164 | 200 / 0 | exit 0, signal — |
| [3-ContHist4PlyRead #3](batches/3-ContHist4PlyRead-0003.txt) | 8475003 | Yes; see retained counts | true / true | 114–118–168 | 200 / 0 | exit 0, signal — |
| [3-ContHist4PlyRead #4](batches/3-ContHist4PlyRead-0004.txt) | 8475004 | Yes; see retained counts | true / true | 99–108–193 | 200 / 0 | exit 0, signal — |
| [3-ContHist4PlyRead #5](batches/3-ContHist4PlyRead-0005.txt) | 8475005 | Yes; see retained counts | true / true | 111–97–192 | 200 / 0 | exit 0, signal — |

Raw attempt rows can include excluded work and must not be summed into the completed totals.

</details>

## Existing tests and limitations

Existing test/check records: 61; nonzero checks: 6; reported sanitizer diagnostics: 0. The [test matrix](TEST_MATRIX.md) and raw outputs distinguish fixture mismatches, timeouts and engine failures. A nonzero fixture comparison is not automatically an engine crash.

Initial Part 1 KRK coverage: release T1 100, release T2 400, ASAN T1 100, ASAN T2 40. The original full ASAN 40×10 attempt timed out without completed counts; this initial reduced retry is separate from later supplemental coverage.

Later completed ASAN split retries (2KRKsplit): 2 invocations, T1 200 reference checks and T2 400 trials; T1 misses 0, T2 misses 0, reported sanitizer diagnostics 0. The two unchanged 40×5 invocations cover ten T2 trials per root as five plus five on the same 40 roots. See the 2KRKsplit batch evidence.

Combined completed ASAN KRK coverage from Part 1 plus these split retries: T1 300 reference checks, T2 440 trials. These are repeated executions, not counts of distinct positions.

Timed-out single 40×10 invocations remain incomplete and contribute no completed coverage. Completed split retries do not turn an original timeout into a pass.

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
- Final depth9 comparison completed100000positions:99958 below halfmove80 and42 high-clock positions. Eight required low-clock equality failures repeat10/10; all8 differ in nodes,3 in score,4 in PV,0 in bestmove. Scratch rule50-gate restoration reproduces lock for all8; TT-only restoration suffices for7. Production and expected criterion are unchanged. See search_equality_investigation.md and faults084–091.
- At user request during the run, inspected the2026-11-14 13:51:59UTC remote snapshot to avoid duplicate work: r3-21/r3-23 contain no extra commit; r3-24 has an existing TT stale-slot candidate fix; r3-17 has legal-prefix/helper-node-budget changes. These branches were reviewed statically only and not merged. The pinned source/protocol remain unchanged. See BRANCH_REVIEW.md.
- At14:02UTC an exec-server transport disconnect prevented creation of a preparation command. No batch was active or lost; connection recovered on the next probe. The failed command had made no state/file changes and was retried.
- To cover enabled-option concurrency within the same Part2 clock budget, final prepared F slots9/10 (extra ASAN+UBSAN repeats, never executed) are replaced by F11/12: the unchanged TSan driver, Threads2/4,depth9, allthree options true. Exact specifications and validation are retained in preparation/f-tsan-supplemental.
- TSan E5 seed9520005 timed out at450seconds while game2 reached bare-king position8/5R2/2B5/3P4/P3k3/2P1N3/1P5P/6K1 w - - 1 60. Process was CPU-active and inputs advanced; no deadlock/crash assertion. No finalSUMMARY, so all partial counts excluded. Same-condition retry E5r1 scheduled; full input/output and observation retained.
- E5 same-condition retry5r1 completed7games/1026searches with cleanTSan exit; originaltimeout retainszeroacceptedcounts. Optional extraASAN D9/D10 (neverrun) deferred to preserve Part2clock after retry; D7/D8,F7/F8,E7/E8 and enabled-optionTSan F11/F12 remain planned.
- Final24 r3 heads at15:00:12UTC reviewed statically and published in BRANCH_REVIEW_R3_COMPLETE.md; initial13:51 inventory is explicitly historical. No r3 code merged or runtime claim adopted. Part4 short-PV wording clarified: no UCI bound qualifier, no exact-DTM or engine-proof certification. Report now distinguishes initial ASAN KRK coverage from later400 split trials; originaltimeouts remainincomplete.
- At15:38UTC prioritized the already-prepared enabled-option TSan batches F11/F12 before optional default-option repeat batches E7/E8, preserving engine, flags, seeds and per-batch limits. Clock will be checked before optional repeats; target Part2end remains around15:56UTC.
- Part2 closed near15:56UTC. Optional extra D9/D10 and E8 repeats were prepared but not run; required thread/option/instrumentation coverage completed. Existing E5 timeout and fullKRK timeouts remain excluded attempts, with actual subsequent retry coverage separate. Part3 starts with400-game default merged-vs-lock batch; only completed audited games will be counted.
- All4000 default merged-vs-lock games were independently verified from original logs, preserved chunks and published Git blobs; counts1094/1177/1729 and pairbins77/315/1272/286/50. Immutable text evidence is in preparation/part3-independent-default. Option modes are separate same-merged-binary on/off matches.

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
| [2C #4](batches/2C-0004.txt) | 4754000 | 16,534 records completed; 16,410 positions | See raw partial evidence | — | Attempt 5 recorded as retry; completion not inferred | driver retained partial work separately |
| [2C #5](batches/2C-0005.txt) | 4754000 | 16,847 records completed; 16,727 positions | See raw partial evidence | — | Attempt 6 recorded as retry; completion not inferred | driver retained partial work separately |
| [2C #6](batches/2C-0006.txt) | 4754000 | 15,083 records completed; 14,994 positions | See raw partial evidence | — | Attempt 7 recorded as retry; completion not inferred | driver retained partial work separately |
| [2E #5](batches/2E-0005.evidence/manifest.txt) | 9520005 | None recorded | See raw partial evidence | — | Attempt 5r1 recorded as retry; completion not inferred | no SUMMARY line |

A retry link records a later attempt; it does not imply that every partial unit has completed. Retained completed units are already included once in phase totals.

## Findings and evidence audit

91 numbered files: 1 fixture; 90 soak.

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
| [091.txt](faults/091.txt) | soak | Comparison fault at required-equality root; 10/10 additional fault pairs |

</details>

Optional audit snapshot: 2026-11-14T15:55:27.421Z; state SHA256 `c5c1d377b6b8163c956207dcf4693b0cec5252dfdbfefa8d675dbd595cf0672b`; apply mode true; reported errors 0, warnings 3. This snapshot is not assumed to verify later state or active work. [Full audit](preparation/latest-audit.txt).

| Audited batch | Raw verification | Partial safety observations | Artifacts with diagnostic markers |
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
| 2C:5 | Raw records inspected; see audit issues | 0 | 0 |
| 2C:6 | Raw records inspected; see audit issues | 0 | 0 |
| 2C:7 | Raw records inspected; see audit issues | 0 | 0 |
| 2D:2 | Limited; see audit | 0 | 0 |
| 2E:1 | Limited; see audit | 0 | 0 |
| 2E:2 | Limited; see audit | 0 | 0 |
| 2F:1 | Limited; see audit | 0 | 0 |
| 2F:2 | Limited; see audit | 0 | 0 |
| 2D:3 | Limited; see audit | 0 | 0 |
| 2D:4 | Limited; see audit | 0 | 0 |
| 2F:3 | Limited; see audit | 0 | 0 |
| 2F:4 | Limited; see audit | 0 | 0 |
| 2E:3 | Limited; see audit | 0 | 0 |
| 2E:4 | Limited; see audit | 0 | 0 |
| 2D:5 | Limited; see audit | 0 | 0 |
| 2D:6 | Limited; see audit | 0 | 0 |
| 2F:5 | Limited; see audit | 0 | 0 |
| 2F:6 | Limited; see audit | 0 | 0 |
| 2E:5 | Limited; see audit | 0 | 0 |
| 2E:5r1 | Limited; see audit | 0 | 0 |
| 2E:6 | Limited; see audit | 0 | 0 |
| 2D:7 | Limited; see audit | 0 | 0 |
| 2D:8 | Limited; see audit | 0 | 0 |
| 2F:7 | Limited; see audit | 0 | 0 |
| 2F:8 | Limited; see audit | 0 | 0 |
| 2F:11 | Limited; see audit | 0 | 0 |
| 2F:12 | Limited; see audit | 0 | 0 |
| 2E:7 | Limited; see audit | 0 | 0 |

<details>
<summary>Audit issues and limits</summary>

- warning: 2D:1 lacks --trace: search/move/game counts are self-reported, with SUMMARY invariants and emitted FAULT rows checked; no per-search replay enumeration available
- warning: 2KRKfull:1 incomplete existing-test invocation; zero completed coverage; native budget expired; incomplete status alone is not an engine fault
- warning: 2E:5 has no recognized final summary; no completed counters inferred, but raw sanitizer evidence is scanned
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
| 2D | ASan+UBSan self-play, Threads2, Hash16, OwnBookfalse, UseNNUEtrue, MultiPV1, all3 candidates false, nodes20000,8 seeded opening plies,300-ply cap,full trace,300-second game-boundary budget | Complete: 1131 games / 131115 searches; ASAN+UBSAN Threads1/2, nodes2000/20000; no chess/runtime diagnostics |
| 2Aprep | Lock-T1 selection and merged-T1 observations: retain40previousKRKroots; generateKQK/KBBK atdepth14; no merged-result filtering | Complete: 40 KRK, 40 KQK and 40 KBBK roots frozen |
| 2A | Frozen40KRK+40KQK+40KBBK, lock/merged, Threads2/4, depth14,10fresh-state trials perroot/build/thread; exactKRKoracle; noKQK/KBBKproofclaim | Complete: merged 0/2,400 and lock 298/2,400 mate-score misses |
| Part4 | Reported mate17/short-PV reproduction and exact KRK assessment; scratch-only trace; production source unchanged | Known-root investigation complete; optional broader sampled audit pending |
| 2B | 200 fixed-seed legal bare-king roots, no mate-score selection; lock and merged, Threads1/2, depth12; raw nodes and times only | Complete: 800 depth-12 searches on 200 roots, both builds at Threads 1/2; no fault |
| 2KRKsplit | Isolated unchanged existing ASAN KRK split retry 2/2: same deterministic40 roots,5 fresh-clear trials each,Threads2 Hash16 depth14; separate100 T1 checks | Complete: two unchanged40x5 invocations; 0/400 main misses,0/200 T1 misses, no sanitizer report |
| 2C | Four disjoint frozen corpus shards; cold depth9 comparisons; counts only | Complete:100,000 positions; 8 required low-clock equality failures; 31 high-clock differences observed |
| 2E | TSan self-play, Threads2, Hash16, OwnBookfalse, UseNNUEtrue, MultiPV1, all3 candidates false, depth9,8 seeded opening plies,300-ply cap,full trace,300-second game-boundary budget | Complete: 56 games / 8297 searches; TSan Threads2/4; no warnings; original E5 timeout excluded and retry completed |
| 2F | Supplemental TSan enabled-option self-play, Threads4,Hash16,OwnBookfalse,UseNNUEtrue,MultiPV1,all3 candidates true,depth9/nodes0,8 seeded opening plies,300-ply cap,full trace,300-second game-boundary budget | Complete: 1102 ASAN+UBSAN games / 126532 searches plus14 enabled-option TSan games /1886 searches; no chess/runtime diagnostics |
| 2G | Unchanged t23 mate and rule50 suites, release and ASan+UBSan;40mate-suite cases plus20rule50 cases perbuild | Complete: four unchanged suite runs; 120 cases; zero missed/false mates, illegal moves, rule50 failures, or sanitizer reports |
| 3-default | Official fastchess; merged defaults versus lock;400 games in200 color-swapped UHO pairs, nodes20000,Threads1,Hash16,OwnBookfalse,recover,no clock/adjudication | Complete:4000 games,2000 color-swapped UHO pairs; W-L-D1094-1177-1729; no crash/illegal/disconnect/stall/abort marker or event; counts only |
| 3-ContHist4PlyRead | Official fastchess; merged ContHist4PlyRead on versus all-three off;400 games in200 color-swapped UHO pairs, nodes20000,Threads1,Hash16,OwnBookfalse,recover,no clock/adjudication | Running |

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
| 2D | games | 1131 |
| 2D | moves | 131115 |
| 2D | searches | 131115 |
| 2D | opening_moves | 9048 |
| 2D | faults | 0 |
| 2D | illegal | 0 |
| 2D | missing | 0 |
| 2D | badscore | 0 |
| 2D | mates | 918 |
| 2D | stalemates | 2 |
| 2D | repetitions | 107 |
| 2D | fifty | 38 |
| 2D | ply_caps | 10 |
| 2D | insufficient | 56 |
| 2D | batches | 8 |
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
| 2C | records_completed | 100715 |
| 2C | positions | 100000 |
| 2C | positions_low_clock | 99958 |
| 2C | positions_high_clock | 42 |
| 2C | differences_low_clock | 8 |
| 2C | differences_high_clock | 31 |
| 2C | fault_positions | 8 |
| 2C | excluded | 715 |
| 2C | excluded_no_legal | 34 |
| 2C | excluded_insufficient | 680 |
| 2C | excluded_halfmove100 | 1 |
| 2C | invalid_fens | 0 |
| 2C | engine_runs | 200780 |
| 2C | illegal | 0 |
| 2C | missing | 0 |
| 2C | missing_info | 0 |
| 2C | wrong_depth | 0 |
| 2C | sanitizer_issues | 0 |
| 2C | transport_issues | 0 |
| 2C | crashes | 0 |
| 2C | nonzero_exits | 0 |
| 2C | shutdown_timeouts | 0 |
| 2C | reproduction_pairs | 390 |
| 2C | reproduction_differences | 390 |
| 2C | reproduction_fault_pairs | 80 |
| 2C | batches | 7 |
| 2E | games | 56 |
| 2E | moves | 8297 |
| 2E | searches | 8297 |
| 2E | opening_moves | 448 |
| 2E | faults | 0 |
| 2E | illegal | 0 |
| 2E | missing | 0 |
| 2E | badscore | 0 |
| 2E | mates | 28 |
| 2E | stalemates | 0 |
| 2E | repetitions | 19 |
| 2E | fifty | 3 |
| 2E | ply_caps | 0 |
| 2E | insufficient | 6 |
| 2E | batches | 7 |
| 2F | games | 1116 |
| 2F | moves | 128418 |
| 2F | searches | 128418 |
| 2F | opening_moves | 8928 |
| 2F | faults | 0 |
| 2F | illegal | 0 |
| 2F | missing | 0 |
| 2F | badscore | 0 |
| 2F | mates | 904 |
| 2F | stalemates | 3 |
| 2F | repetitions | 99 |
| 2F | fifty | 41 |
| 2F | ply_caps | 8 |
| 2F | insufficient | 61 |
| 2F | batches | 10 |
| 2G | tests_completed | 4 |
| 2G | cases | 120 |
| 2G | mate_cases | 60 |
| 2G | nonmate_cases | 20 |
| 2G | rule50_cases | 40 |
| 2G | missed_mates | 0 |
| 2G | false_mates | 0 |
| 2G | illegal | 0 |
| 2G | rule50_failures | 0 |
| 2G | sanitizer_reports | 0 |
| 2G | batches | 1 |
| 3-default | games | 4000 |
| 3-default | games_started | 4000 |
| 3-default | wins | 1094 |
| 3-default | losses | 1177 |
| 3-default | draws | 1729 |
| 3-default | moves | 570911 |
| 3-default | complete_pairs | 2000 |
| 3-default | incomplete_pairs | 0 |
| 3-default | audit_errors | 0 |
| 3-default | pair_LL | 77 |
| 3-default | pair_LD | 315 |
| 3-default | pair_DD_or_WL | 1272 |
| 3-default | pair_DW | 286 |
| 3-default | pair_WW | 50 |
| 3-default | illegal_move_events | 0 |
| 3-default | illegal_move_games | 0 |
| 3-default | disconnect_games | 0 |
| 3-default | stall_games | 0 |
| 3-default | aborted_games | 0 |
| 3-default | abnormal_terminations | 0 |
| 3-default | crash_markers | 0 |
| 3-default | illegal_markers | 0 |
| 3-default | disconnect_markers | 0 |
| 3-default | stall_markers | 0 |
| 3-default | batches | 10 |
| 3-ContHist4PlyRead | games | 2000 |
| 3-ContHist4PlyRead | games_started | 2000 |
| 3-ContHist4PlyRead | wins | 558 |
| 3-ContHist4PlyRead | losses | 541 |
| 3-ContHist4PlyRead | draws | 901 |
| 3-ContHist4PlyRead | moves | 280948 |
| 3-ContHist4PlyRead | complete_pairs | 1000 |
| 3-ContHist4PlyRead | incomplete_pairs | 0 |
| 3-ContHist4PlyRead | audit_errors | 0 |
| 3-ContHist4PlyRead | pair_LL | 58 |
| 3-ContHist4PlyRead | pair_LD | 226 |
| 3-ContHist4PlyRead | pair_DD_or_WL | 411 |
| 3-ContHist4PlyRead | pair_DW | 251 |
| 3-ContHist4PlyRead | pair_WW | 54 |
| 3-ContHist4PlyRead | illegal_move_events | 0 |
| 3-ContHist4PlyRead | illegal_move_games | 0 |
| 3-ContHist4PlyRead | disconnect_games | 0 |
| 3-ContHist4PlyRead | stall_games | 0 |
| 3-ContHist4PlyRead | aborted_games | 0 |
| 3-ContHist4PlyRead | abnormal_terminations | 0 |
| 3-ContHist4PlyRead | crash_markers | 0 |
| 3-ContHist4PlyRead | illegal_markers | 0 |
| 3-ContHist4PlyRead | disconnect_markers | 0 |
| 3-ContHist4PlyRead | stall_markers | 0 |
| 3-ContHist4PlyRead | batches | 5 |

</details>

Raw commands, outputs, seeds, process statuses, manifests and source hashes remain in the linked evidence. Missing work and exclusions are retained explicitly; no result here is an Elo or speed claim.
