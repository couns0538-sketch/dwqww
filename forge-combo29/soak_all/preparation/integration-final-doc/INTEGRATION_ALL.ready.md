# Combined integration validation

Start: 2026-11-14T11:11:32Z. Scheduled eight-hour end: 2026-11-14T19:11:32Z.

Base: `fca0fb40c7e66fdf01e36f4b95ceb179ffee2fca` (`carbon/t21-integrate-round2`). Merged source commit: `f27b1971e459581ad4c85b7015f6af83bbfd4af6`.

The engine source remains pinned to that merged commit. This documentation update starts from integration checkpoint `e04556ddc3a430b2e751159b0d46111ef56c8b89`; it adds no engine changes or later candidate fixes. **Validation is not all-pass:** four unchanged fixture comparisons fail, and eight required low-clock search-equality cases fail and reproduce in 10/10 additional fresh pairs each.

The [live/final soak report](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/SOAK_ALL_REPORT.md) on `soak/combo29-all` is the record for completed and incomplete coverage, sanitizer findings, match outcomes, Part 4 observations and remaining verification limits. Later results and raw logs remain on that branch; this integration document does not assert completion or success for unexecuted phases. Counts and measurements do not support an Elo, strength or speed conclusion.

Requested merges, in order:

- `91103a012c8f77f528606935dcff7184123617eb`
- `5633a78d1ac0684bd0da6db5a0f6d26933c56031`
- `61f59baedecd6c80d2a6803421d2f43e0890935a`

The t23 merge applied cleanly. The t22 UCI conflict keeps the existing `note_invalid`/`apply_spin` style, MultiPV, eval command and UCI-loop wrapper, and adds only the three false-default check options. The t12 search conflict preserves its bare-king definition and five pruning guards while ANDing the relevant t23 mate/rule-50 guards. LMR uses the child halfmove clock plus `new_depth`, as in t23. No unrelated engine cleanup was added.

| File | SHA256 |
| --- | --- |
| src/search.cpp | `2b14b62cd675b047478e70b738932ce4c2c699239b3c0de4ec43551464dc8819` |
| src/uci.cpp | `724a4c9c07a4102d38c39fc292f66ba0c850a9c162c090148734da86acd4fb40` |
| include/forge/search.hpp | `9b88252588398bbe83164d6d9e0200522e919ed813a8cb4b04a8c57eee921600` |

Release and ASan/UBSan CMake builds completed with GCC 14.2, x86-64-v4, the original AVX-512/BMI2 definitions and strict floating-point flags. Default release checks, Threads 1 / Hash 16 / OwnBook false: bench 11 **312866**, bench 13 **862329**, startpos perft 5 **4865609**. All three new options were left at their advertised false defaults.

Release, ASan/UBSan and TSan engine builds completed. The 20 C++ test/helper entry points across all 16 existing test folders were built in release and ASan/UBSan configurations. Test assertions were enabled with `-UNDEBUG`; engine objects retain their original strict floating-point and ISA definitions. The widened-net parity test uses the checked-in 512-wide net and its original namespace isolation. Build commands and outputs are retained in the [soak preparation evidence](https://github.com/couns0538-sketch/dwqww/tree/soak/combo29-all/forge-combo29/soak_all/preparation). A successful sanitizer build alone does not establish a clean sanitizer run.

The [test matrix](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/TEST_MATRIX.md) records every automated suite run and nonzero exit. The unchanged t16 options/clamp expected-output fixtures omit five currently advertised options: MultiPV, NnueFile, ContHist4PlyRead, NonPawnCorrection and LmrDeeperShallower. These four exact comparisons fail across the two builds; expected files were not changed. Each fixture/build combination repeats this difference 10/10 times; all 40 invocations exit normally and have no other output difference or sanitizer diagnostic. Full evidence is [fault 001](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/faults/001.txt).

The 100,000-position comparison found eight required equality failures at root halfmove clocks below 80. All eight differ in node count; three also differ in score and four in PV, while the best move agrees. Each initial failure repeats in ten additional fresh lock/merged pairs. They remain failures: the [source-guided investigation and exact evidence](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/search_equality_investigation.md) do not change expectations or establish which differing score is correct. No production repair was applied.

The recorded existing-suite engine invocations, search/OwnBook protocol checkers, candidate-option suite, 200,000-line UCI fuzz tests and t23 mate/rule-50 tests pass without sanitizer diagnostics; this does not describe every later soak batch. The full release KRK test reports 0/100 single-thread misses and 0/400 two-thread misses. Its full ASan/UBSan attempt hit the 440-second test deadline while other sanitizer tests were running; that incomplete attempt is preserved and is not counted as a passing run. The unchanged test's bounded 40-root, one-trial sanitizer retry completes with 0/100 single-thread misses and 0/40 two-thread misses, exit 0 and no sanitizer diagnostic. This one-trial retry did not establish ten sanitizer trials per root; the later completed split runs below provide that coverage. See the [retry assessment](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/preparation/asan-krk-retry-assessment.txt).

The later isolated full sanitizer invocation also timed out at 435 seconds. Two bounded invocations of the unchanged test, each `40 5 2 16 14 1`, then completed: together **0/400 two-thread misses and 0/200 single-thread reference misses**, with no sanitizer diagnostic. Both used the same binary SHA256 `4e504c5479c5b55c09e00493892f468221a13154f725ac9d6bb381c077030e99` and the same deterministic roots, with full clear before each search. The two completed split runs provide ten total two-thread trials for each of the same 40 roots, as five trials in each invocation. Both timed-out single `40x10` invocations remain incomplete and are not counted as passing runs. Including the initial reduced retry, completed KRK sanitizer executions total **300 single-thread reference checks and 440 two-thread trials**; these are repeated checks, not distinct positions. Evidence: [split 1](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/batches/2KRKsplit-0001.txt), [split 2](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/batches/2KRKsplit-0002.txt).

All seven interactive t3 clock cases pass in each build, with complete UCI traffic and measured times retained in the [clock assessment](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/preparation/t3-clock-interactive-assessment.txt). Initial harness timing measurements and their corrected minimum-150-ms observation are preserved. No expected value was edited to make a check pass.

Existing t12/t22 report files retain their source trailing spaces. The global whitespace check reported those inherited lines; source/include/test checks passed.

Only `integrate/combo29-all` and `soak/combo29-all` are authorized push destinations. The preceding `soak/combo29-fixes` branch/worktree is untouched after this task began. Its last completed in-flight batch remains there without another commit or push.

Evidence on `soak/combo29-all`: [live/final report](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/SOAK_ALL_REPORT.md), [progress](https://github.com/couns0538-sketch/dwqww/blob/soak/combo29-all/forge-combo29/soak_all/PROGRESS.md), [raw batches](https://github.com/couns0538-sketch/dwqww/tree/soak/combo29-all/forge-combo29/soak_all/batches), and [preparation commands and output](https://github.com/couns0538-sketch/dwqww/tree/soak/combo29-all/forge-combo29/soak_all/preparation).
