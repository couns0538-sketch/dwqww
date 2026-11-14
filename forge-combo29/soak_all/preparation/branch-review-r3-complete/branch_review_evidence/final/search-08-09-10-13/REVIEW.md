# Final r3 search-branch review: 08, 09, 10, 13

Static review only. No native build, engine search, sanitizer run, game, checkout, merge, ref update, push, or change to the pinned engine was performed by this reviewer. The branch reports below are third-party claims read from Git objects; their native outcomes were not independently reproduced or validated from complete raw run logs.

Reviewed snapshot: `/workspace/work/all-run/branch-review-r3-complete/remote-heads.txt`. Repository: `/workspace/work/dwqww-all`. Comparison baseline: `e04556ddc3a430b2e751159b0d46111ef56c8b89`. A read-only `git diff --exit-code` confirmed that this baseline and pinned source `f27b1971e459581ad4c85b7015f6af83bbfd4af6` have identical `forge-combo29/src` and `forge-combo29/include` contents (command 045, exit 0, empty output). All four heads descend from this baseline; all four `git diff --check` calls pass (commands 050-057, exit 0, empty output).

## Disposition

All four branches add separate default-off search experiments. None directly repairs the currently pinned integration's near-rule-50 equality differences or proves mate-distance correctness. Keep the ongoing soak on its pinned source. These branches provide useful test patterns for later work, particularly r3-10's returned-PV legality walk, but they are not substitutes for the current job's required validation.

| Branch | Exact reviewed head | New option | Static finding |
| --- | --- | --- | --- |
| `grok47/r3-08-asp-capped-reopen` | `fd9f4f0f9efbb2e16d3056271e7d62dd23e8dab5` | `AspCappedReopen=false` | Reopens failed root bound to score +/-13; opens that side fully for mate or decisive score. No branch-specific assertion demonstrates that the special paths actually ran. |
| `grok47/r3-09-asp-arm-late` | `a92af3d7293c254e4ee7f70bb2bd61b93d9935f9` | `AspArmLate=false` | Normally narrows from depth 2, earlier than default depth 4. Added soft-stop tests in the search loop are control-flow redundant. |
| `grok47/r3-10-evasion-ordering` | `1cd68ed033cf90917e4d23a644bbe341c768d2c6` | `EvasionOrdering=false` | Changes capture-evasion scoring; quiet-evasion scoring already used the same history mix. Useful legality-PV test, no direct ordering assertion. |
| `grok47/r3-13-quiet-extinction` | `2158d5832ceac299528ea5a6ca7883c3c742cf8c` | `QuietExtinction=false` | Adds heuristic quiet pruning. Second-stage tail closure can drop later checking quiet moves. Root legality tests do not establish pruning soundness. |

Every branch changes only `search.cpp`, `uci.cpp`, `include/forge/search.hpp`, one new C++ test, and one report relative to the baseline. All flags are initialized false at `src/search.cpp:80`, declared at `include/forge/search.hpp:273`, advertised default false at `src/uci.cpp:192`, and set through strict true/false UCI parsing. r3-08 has its own parser arm at lines 314-320; the other three extend the existing t22 parser arm at lines 305-315. The disabled code paths retain the original scoring/search rules by inspection. This is static evidence, not an independent bench pass.

Implementation commits differ from final report/test tips: r3-08 source is `fef5e0023702bffb2a52a75c626b1596e43fdfbc`; r3-09 source is `ab72d3b07cc343a8f475b435ba88aa2bf4abb19d`; r3-10 source is `a2392f49dc81fbdb6db73213a0a500c472e7ab16`; r3-13 source is `192f66f43e30bd50456f3da89f9dfd636ef26a8b`. Commands 058-061 compare each implementation with its reviewed final head under `src`/`include`: all exit 0 with empty output. Later commits improve tests or record claimed reruns without changing the implementation.

## r3-08: AspCappedReopen

Source references at `fd9f4f0f9efbb2e16d3056271e7d62dd23e8dab5`:

- `forge-combo29/src/search.cpp:1591-1601`: margin 13, decisive threshold 640. Fail-low opens alpha fully for any mate score or returned score <= -640; fail-high opens beta fully for any mate score or score >=640. The existing mate predicate covers both signs.
- `src/search.cpp:1794-1821`: initial window still begins at depth 4. Fail-low still moves beta to the old midpoint before replacing alpha; this is not literally an update of only one bound. On the new path the growing `delta` is not used for bound placement, though its existing update remains.
- `tests_r3_08/asp_legal_test.cpp:28-46,66-100`: verifies the initial default is false, then enables the option for 200 depth-10 searches and four edges (checked king, promotion, checkmate, stalemate). The random roots use 0-15 opening plies; multiples of 16 repeat startpos. This is a count of searches, not a guarantee of 200 unique positions.

Coverage limits: the test checks legal returned root moves or no move for terminal roots. It does not assert returned depth, score, PV legality, changed aspiration bounds, failure counts, mate/decisive branch execution, time behavior, multithread behavior, or interactions with t22 options. It has no compiled-in bench-pin checks; those are only in the branch report. The report explicitly says special-path hit counts, MultiPV pins, and clock-game pins were not established (`REPORT_r3_08.md:53-55`). No concrete bad outcome was independently reproduced here.

Current-job use: the four edge FENs can inform future legality coverage. This is an aspiration policy experiment, not a fix for false mate proof or rule-50 handling.

## r3-09: AspArmLate

Source references at `a92af3d7293c254e4ee7f70bb2bd61b93d9935f9`:

- `forge-combo29/src/search.cpp:1753-1755,1778-1783,1809`: the per-search `asp_score_inside` flag starts false, becomes true after one completed in-window iteration, and then permits narrow windows without a minimum depth. A normal depth-1 full-window result arms it, so depth 2 and 3 use narrow windows when enabled. The disabled rule is still `depth >= 4`. The name should not be read as delaying aspiration relative to this baseline.
- `src/search.cpp:1800-1808`: the added time check ends with `continue` at the very end of the `while` body. Falling through already repeats that loop. This adds a clock read when enabled, but not a new control-flow permission to finish aspiration.
- `src/search.cpp:1790-1799,1810-1823,1925-1927`: the loop exits on abort or after `inside_window=true`. Abort exits the outer iteration before the later soft-limit gate. Consequently, whenever that gate is reached normally, `inside_window` is already true; `soft_finished` adds no independent protection against stopping outside the window. Existing hard/node/external-stop logic remains responsible for aborts.
- `tests_r3_09/asp_arm_late_test.cpp:108-166`: default bench11/13 and perft5 assertions, enabled bench13 must differ, 200 enabled depth-10 legality searches, 20 enabled searches with `time_ms=40`, then restored bench13 assertion.

Coverage limits: the timed tests assert only root-move legality. They do not assert elapsed limits, whether an aspiration failure happened, the depth at which narrowing starts, or whether a soft stop occurred inside/outside a window. Default is explicitly assigned false rather than checking the startup value. No enabled multithread or t22 interaction test is present. The report's soft-time explanation describes a property already supplied by the original loop; it is not evidence of a repaired soft-stop fault.

Current-job use: useful timed-legality input generation. Do not count this branch as an independently established time-safety fix.

## r3-10: EvasionOrdering

Source references at `1cd68ed033cf90917e4d23a644bbe341c768d2c6`:

- `forge-combo29/src/search.cpp:757-790`: the shared evasion generator changes capturing moves to `2000000 + victim SEE value + capture_history_value`. This applies to main search and quiescence when the existing picker takes its in-check stage.
- The TT move still precedes generated evasions. Noncapturing promotions keep their prior band. Capturing promotions now use the capture branch and therefore omit the old promotion-gain term from `capture_value`; this is part of the ordering change, not a move-generation change (`src/search.cpp:178-181,773-779`).
- Quiet evasions already used quiet history and the direct-check bonus; those code paths remain unchanged. `ContHist4PlyRead` can still contribute through the common `QuietScorer` (`src/search.cpp:630-642`) when separately enabled. The two-million capture band is safely above the few int16 history terms used for quiets; no scoring overflow is apparent from these operands.
- `tests_r3_10/evasion_ordering_test.cpp:110-120,123-147`: verifies root move, PV first move, and every PV move against legal moves and `make_move`, with history retained in blocks of 25 searches. This is a useful reusable test pattern absent from the other three new tests.
- `tests_r3_10/evasion_ordering_test.cpp:154-191`: asserts disabled pins, enabled bench13 differs, 200 enabled depth-10 searches, and restored bench13.

Coverage limits: no direct assertion of evasion ordering/capture-history influence, no explicit capture-promotion or en-passant-evasion test, no mate-score/proven-mate validation, no enabled multithread test. Default is assigned false rather than checking initialization. A legal PV may end before mate and does not prove a reported mate distance. This branch does not address that requirement.

## r3-13: QuietExtinction

Source references at `2158d5832ceac299528ea5a6ca7883c3c742cf8c`:

- `forge-combo29/src/search.cpp:1384-1392`: enables only for nonroot, noncheck nodes, `mate_moves_==0`, outside `bare_king_mode`, `halfmove_clock + depth <100`, with non-pawn material on at least one side.
- `src/search.cpp:1438-1444`: after one wide miss, halves ordinary-quiet futility slack; this specific check excludes checking moves, killers, and the counter move.
- `src/search.cpp:1566-1569`: two quiet results at least 176 below current alpha close the ordinary quiet tail. The condition tests `best_score > -MateInMaxPly`, not the individual `score`: after a prior ordinary score, an individually mate-sized losing quiet can still count. The report accurately describes the best-score gate; the nearby broad source comment should not be read as rejecting every mate-sized candidate result.
- `src/search.cpp:502-507,556-557`: closing the tail skips remaining `GenerateQuiets`/`QuietMoves` outright. This also skips quiet checking moves that have not yet been returned; the `!gives_check` exemption applies only to first-stage futility, not tail closure. Captures, promotions, and the dedicated killer/counter stages are not removed by the new flag itself, though existing pruning remains in force.
- This guard does not exclude PV nodes or a mate-valued alpha/beta window. It is a heuristic pruning experiment, not a sound-mate-pruning fix. Bare-king/go-mate gates avoid some current reproducers but do not prove general mate preservation.
- `tests_r3_13/quiet_extinction.cpp:70-91,97-149`: checks startup false, pins, enabled bench difference, 197 short opening walks plus a pure king/pawn position, a checked bare-king position, and startpos. It asserts depth10 and root legality, positive nodes outside immediate draws, and restored bench13.

Coverage limits: no instrumentation proves one-miss/two-miss transitions or preservation of killer/counter/capture/promotion classes; no near-100 halfmove boundary test, no PV or mate correctness oracle, no explicit future checking-quiet fixture, no enabled multiworker or t22 combination test. No bad-move reproducer was run by this reviewer, so the pruning scope is a static risk/coverage finding, not a confirmed runtime fault.

## Overlap with existing t22 tests and ongoing soak

`tests_t22/search_candidates_test.cpp:101-105,112-158,185-193` resets and tests only `ContHist4PlyRead`, `NonPawnCorrection`, and `LmrDeeperShallower`, one at a time. Its UCI command file likewise toggles only those three (`tests_t22/uci_candidates.txt:10-21`). None enables the four new r3 flags. The new tests also leave the three t22 options at their default false values; none validates the combinations.

The source areas overlap mechanically: r3-10 quiet scoring uses the `ContHist4PlyRead`-aware common scorer; r3-13 pruning uses static evaluation and reduction/history data that can be affected by all three t22 experiments. Aspiration experiments can react differently to scores produced by those options. These relationships require dedicated future combination coverage; the current job's enabled-t22 sanitizer and game counts cannot be relabeled as tests of these r3 options.

Baseline CMake creates only the engine executable and has no test registration (command 047). None of these branches changes CMake. A plain release build or `ctest` invocation would not by itself run these new standalone tests; explicit compilation/linking is needed, with matching engine defines. This reviewer did not perform that compilation.

## Branch-reported outcomes, not independently reproduced

These are statements and excerpts in the committed reports, not complete raw native transcripts. They remain unverified here.

| Branch report | Reported default bench11 / bench13 / perft5 | Reported enabled bench13 | Reported enabled sanitizer legality sample |
| --- | --- | --- | --- |
| r3-08 | 312866 / 862329 / 4865609 | 850997 | 200 depth10 + four edges, no report, exit0 |
| r3-09 | 312866 / 862329 / 4865609 | 818642 | 200 depth10 + 20 short-clock searches, no report, exit0 |
| r3-10 | 312866 / 862329 / 4865609 | 772890 | 200 depth10, 9 in-check roots, 2360 legal PV moves, no report, exit0 |
| r3-13 | 312866 / 862329 / 4865609 | 602141 | 200 depth10, root legality, no report, exit0 |

No game result, strength conclusion, or performance conclusion is established by this review.

## Evidence files

All evidence is under `/workspace/work/all-run/r3-complete-search-review/`:

- `commands.txt`: exact Git argv and exit codes, pointing to all raw command records.
- `001-...txt` through `061-...txt`: JSON records containing UTC, cwd, exact Git argv, exit code, signal, full stdout and stderr. No raw output was intentionally truncated in these files.
- `targets.txt`: reviewed baseline and snapshot-selected exact heads.
- `08-source-diff.txt`, `09-source-diff.txt`, `10-source-diff.txt`, `13-source-diff.txt`: complete source diffs against baseline.
- `NN-src_search.cpp.numbered.txt`, `NN-src_uci.cpp.numbered.txt`, `NN-include_forge_search.hpp.numbered.txt`: full final source with original Git line numbers.
- `NN-tests_...numbered.txt`, `NN-REPORT_r3_NN.md.numbered.txt`: full test/report text with original line numbers.
- `baseline-tests_t22_...numbered.txt`: existing t22 coverage inspected.

The only writes by this reviewer were evidence/review files in this scratch directory. Native workload results remain the responsibility of the root controller and are not altered by this review.
