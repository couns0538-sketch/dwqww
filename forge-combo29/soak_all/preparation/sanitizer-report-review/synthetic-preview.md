# Eight-hour combined Forge integration and soak

Start: 2026-11-14T11:11:32Z. Scheduled end: 2026-11-14T19:11:32Z. Report snapshot: 2026-11-14T13:02:00Z.

Elapsed at snapshot: 110.47 minutes; current phase: 2E; recorded pushes: 3. Cloud VM only. Counts and measurements do not support an Elo, strength or speed conclusion.

Base: `abc`; merged source: `def`; unchanged lock: `ghi`. [Source provenance](../INTEGRATION_ALL.md), [progress](PROGRESS.md), [raw batches](batches/), [test matrix](TEST_MATRIX.md).

Active batch: 2F #2, seed 42, started now. Its unfinished work is absent from completed totals.

## Phase summary

| Phase | Conditions | Recorded completed work | Status |
| --- | --- | --- | --- |
| Part 1 | Release, ASAN+UBSAN and TSan builds; existing tests and fixed node/perft pins. | No completed counts recorded | Pending; no completed counts recorded |
| 2A preparation | Retain all 40 supplied KRK roots; select generated KQK/KBBK using lock T1 positive exact mate scores. | No completed counts recorded | Pending; no completed counts recorded |
| 2A | 40 KRK + 40 KQK + 40 KBBK; lock and merged; T2/T4; depth 14; ten cold-state trials per group. | No completed counts recorded | Pending; no completed counts recorded |
| 2B | 200 fixed-seed legal bare-king positions; lock and merged; depth 12; reported T1/T2 conditions. | No completed counts recorded | Pending; no completed counts recorded |
| 2C | Fixed corpus comparison; completed eligible positions and exclusions tracked separately. | No completed counts recorded | Pending; no completed counts recorded |
| 2D | Sanitizer self-play; inspect each batch for its exact node/depth/thread limits. | 2 games; 20 searches; 0 faults | Pending; no completed counts recorded |
| 2E | ThreadSanitizer runs; exact thread and search conditions remain in batch evidence. | 8 games; 80 searches; 0 faults | Pending; no completed counts recorded |
| 2F | ASAN+UBSAN self-play with all three new options enabled; exact limits remain in batch evidence. | 2 games; 20 searches; 0 faults | Running; no completed batch recorded |
| 2G | t23 mate/fifty-move suites; unchanged expectations and complete test outputs retained. | 4 tests completed; 84 cases; 60 mate cases; 16 nonmate cases; 8 rule50 cases; 0 sanitizer reports | Pending; no completed counts recorded |
| 3-default | Merged defaults (candidate) versus unchanged lock (baseline). | No completed counts recorded | Pending; no completed counts recorded |
| 3-ContHist4PlyRead | Merged with only ContHist4PlyRead enabled versus merged with all three new options disabled. | No completed counts recorded | Pending; no completed counts recorded |
| 3-NonPawnCorrection | Merged with only NonPawnCorrection enabled versus merged with all three new options disabled. | No completed counts recorded | Pending; no completed counts recorded |
| 3-LmrDeeperShallower | Merged with only LmrDeeperShallower enabled versus merged with all three new options disabled. | No completed counts recorded | Pending; no completed counts recorded |
| Part4 | Mate-bound/PV investigation and optional sampled KRK audit; exact DTM checks, no universal correctness claim. | No completed counts recorded | Pending; no completed counts recorded |

Counts below use committed state totals. A dash means unavailable or not applicable, never an inferred zero. Fault categories can overlap.

## Mate observations

No completed mate groups are recorded yet.

A mate-score miss includes missing, nonpositive or bounded mate scores. The KRK criterion also flags a legal winning move whose exact DTM exceeds the claimed mate bound, or requested depth when no positive mate score is returned. “Lost forced mate” is the separate drawing-move condition. These columns must not be added together.

KRK uses the retained exact t12 retrograde algorithm with shared board/attack primitives, fresh halfmove-zero roots and no history-dependent draw model. KQK/KBBK roots were selected by a lock T1 positive exact mate score; the merged result never filtered selection. KQK/KBBK have no independent mate oracle. Ten recorded trials are ten group observations, not ten additional reproductions after a separate baseline. An incomplete PV is not a proof of false mate.

## Sanitizer self-play outcomes

Chess fault counters, runtime failures and sanitizer warnings are separate observations. A chess summary with zero faults does not establish a clean sanitizer run. Counts in this section come only from matched finished batches in the supplied audit snapshot; state game/search totals remain unchanged.

Audit snapshot: 2026-11-14T13:01:00Z; reported reconciliation errors 0. Batch identity, finish time, recorded counts and available exit/signal are matched to state. This renderer does not assert that the audit state hash matches current state.

| Phase | Audited / finished attempts | With canonical counts | With process classification | TSan warning blocks | Unresolved blocks | Nonzero exits | Runtime/diagnostic affected | Timeout/forced |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2D | 1 / 1 | 0 | 0 | — | — | — | — | — |
| 2E | 3 / 4 | 3 | 3 | 7 | 1 | 3 | 3 | 0 |
| 2F | 0 / 1 | 0 | 0 | — | — | — | — | — |

Coverage includes finished attempts with no committed chess counts. A dash means unavailable, not zero. Nonzero exits, runtime diagnostics and timeouts can overlap; timeout/forced termination is not labelled an engine crash. ASan/UBSan marker lines are not TSan warning events.

<details>
<summary>Per-batch sanitizer and process evidence</summary>

| Batch | Finished UTC | Threads | Depth / node setting | Candidate flags | Counted games / searches / chess faults | Exit / signal | Runtime classification | Runtime marker lines | Canonical TSan warnings | Resolved groups / unresolved blocks | TSan footer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [2E #1](batches/2E-0001.txt) | 2026-11-14T13:00:01Z | 2 | 9 / 0 | false / false / false | 2 / 20 / 0 | 66 / none | sanitizer_diagnostic_nonzero_exit | 11 | 3 | 1 / 1 | Matches retained blocks |
| [2E #2](batches/2E-0002.txt) | 2026-11-14T13:00:02Z | 4 | 9 / 0 | false / false / false | 2 / 20 / 0 | 66 / none | sanitizer_diagnostic_nonzero_exit | 11 | 4 | 2 / 0 | Matches retained blocks |
| [2E #3](batches/2E-0003.txt) | 2026-11-14T13:00:03Z | 2 | 9 / 0 | false / false / false | 2 / 20 / 0 | 66 / none | No audit row supplied | — | — | — / — | Unavailable / not applicable |
| [2F #1](batches/2F-0001.txt) | 2026-11-14T13:00:01Z | 2 | 0 / 2,000 | true / true / true | 2 / 20 / 0 | 0 / none | Audit identity, finish time or recorded counters differ from state | — | — | — / — | Unavailable / not applicable |
| [2D #1](batches/2D-0001.txt) | 2026-11-14T13:00:01Z | 2 | 0 / 2,000 | false / false / false | 2 / 20 / 0 | 0 / none | Unavailable | — | — | — / — | Unavailable / not applicable |
| [2E #4](batches/2E-0004.txt) | 2026-11-14T13:00:04Z | 2 | 9 / 0 | false / false / false | 2 / 20 / 0 | 66 / none | nonzero_sanitizer_exit_code_without_runtime_diagnostic | 0 | 0 | 0 / 0 | Matches retained blocks |

Conditions come from each retained raw SUMMARY, or its retained parsed SUMMARY when raw text is unavailable. Candidate order is ContHist4PlyRead / NonPawnCorrection / LmrDeeperShallower; literal booleans are shown. A positive depth setting selects depth-limited search; depth zero selects the node limit. Missing conditions are not inferred from the phase description or later batches.


Only canonical warning blocks from each primary runtime log enter the totals. Mirrored artifacts, WARNING/SUMMARY markers and runtime footers are not additional warnings. Runtime duplicate suppression can hide repeated manifestations; these counts are not reproduction frequencies.

</details>

2 observed source-line-pair groups across the matched audit batches. This is a grouping of reported evidence, not a count of distinct bugs. Repeated pairs across batches appear once below; their reported warning blocks are summed once per batch.

| Warning type | Access source 1 | Access source 2 | Reported warning blocks | Contributing batches |
| --- | --- | --- | --- | --- |
| data race | forge-combo29/include/forge/search.hpp:20 | forge-combo29/src/search.cpp:10 | 5 | [2E #1](batches/2E-0001.txt) (2); [2E #2](batches/2E-0002.txt) (3) |
| data race | forge-combo29/src/tt.cpp:30 | forge-combo29/src/tt.cpp:40 | 1 | [2E #2](batches/2E-0002.txt) (1) |

Audit coverage and grouping omissions:

- 2E:3: No audit row supplied; no sanitizer count inferred.
- 2F:1: Audit identity, finish time or recorded counters differ from state; no sanitizer count inferred.
- 2D:1: canonical sanitizer counts unavailable; legacy marker/artifact totals are not a substitute.
- 2D:1: independent runtime/process classification unavailable.
- 2F:2: active attempt omitted from finished coverage and all counts.

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

Existing test/check records: —; nonzero checks: —; reported sanitizer diagnostics: —. The [test matrix](TEST_MATRIX.md) and raw outputs distinguish fixture mismatches, timeouts and engine failures. A nonzero fixture comparison is not automatically an engine crash.

The unchanged t16 options/clamp fixtures omit newly advertised options. Their exact-output mismatches and repeated clean process exits remain recorded separately. Clock-fixture timings use documented observation guards, not exact scheduler guarantees. TSan findings and runtime limitations must be read from the recorded test outputs; building TSan alone is not evidence of a clean run.

Completed-unit totals exclude partial work; interrupted cleanup diagnostics remain evidence even when excluded from a completed frequency denominator. In particular, inspect partial records’ interrupted-trial and shutdown fields. For untraced self-play batches, searches/moves/games can be self-reported counters rather than independently enumerated raw observations. Sanitizer occurrences can repeat in mirrored logs and are not counts of distinct bugs.

<details>
<summary>Recorded notes and exceptions (preserved)</summary>

- Root note preserved

These notes retain their original recording context; subsequent retry coverage is stated separately.

</details>

## Incomplete attempts and retries

No incomplete attempts are listed in state; see test limitations above for attempts tracked only in test evidence.

## Findings and evidence audit

No numbered fault files are recorded in this state snapshot. This does not by itself establish zero observed faults.

Optional audit snapshot: 2026-11-14T13:01:00Z; state SHA256 `snapshot-hash`; apply mode false; reported errors 0, warnings 0. This snapshot is not assumed to verify later state or active work.

| Audited batch | Raw verification | Partial safety observations | Artifacts with diagnostic markers |
| --- | --- | --- | --- |
| 2E:1 | Limited; see audit | 0 | 2 |
| 2E:2 | Limited; see audit | 0 | 2 |
| 2F:1 | Limited; see audit | 0 | 2 |
| 2D:1 | Limited; see audit | 0 | 0 |
| 2E:4 | Limited; see audit | 0 | 2 |

<details>
<summary>All recorded counters (exact unchanged values)</summary>

This appendix preserves every state total, including overlapping categories and measurements omitted from compact tables. Raw batch outputs remain authoritative evidence; this renderer neither recomputes nor changes state.

| Phase | Recorded conditions | Recorded status |
| --- | --- | --- |
| 2D | — | — |
| 2E | — | — |
| 2F | — | — |
| 2G | — | — |

| Phase | Counter | Recorded value |
| --- | --- | --- |
| 2D | games | 2 |
| 2D | searches | 20 |
| 2D | faults | 0 |
| 2E | games | 8 |
| 2E | searches | 80 |
| 2E | faults | 0 |
| 2F | games | 2 |
| 2F | searches | 20 |
| 2F | faults | 0 |
| 2G | tests_completed | 4 |
| 2G | cases | 84 |
| 2G | mate_cases | 60 |
| 2G | nonmate_cases | 16 |
| 2G | rule50_cases | 8 |
| 2G | sanitizer_reports | 0 |

</details>

Raw commands, outputs, seeds, process statuses, manifests and source hashes remain in the linked evidence. Missing work and exclusions are retained explicitly; no result here is an Elo or speed claim.
