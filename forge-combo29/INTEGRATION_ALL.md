# Combined integration validation

Start: 2026-11-14T11:11:32Z. Scheduled eight-hour end: 2026-11-14T19:11:32Z.

Base: `fca0fb40c7e66fdf01e36f4b95ceb179ffee2fca` (`carbon/t21-integrate-round2`). Merged source commit: `f27b1971e459581ad4c85b7015f6af83bbfd4af6`.

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

Release, ASan/UBSan and TSan engine builds completed. The 20 C++ test/helper entry points across all 16 existing test folders were built in release and ASan/UBSan configurations. Test assertions were enabled with `-UNDEBUG`; engine objects retain their original strict floating-point and ISA definitions. The widened-net parity test uses the checked-in 512-wide net and its original namespace isolation. Build commands and outputs are retained in `soak_all/preparation/`.

The [test matrix](soak_all/TEST_MATRIX.md) records every automated suite run and nonzero exit. The unchanged t16 options/clamp expected-output fixtures omit five currently advertised options: MultiPV, NnueFile, ContHist4PlyRead, NonPawnCorrection and LmrDeeperShallower. Exact comparisons therefore fail in both builds; expected files were not changed. Each fixture/build combination repeats this difference 10/10 times; all 40 invocations exit normally and have no other output difference or sanitizer diagnostic. Full evidence is [fault 001](soak_all/faults/001.txt).

The engine invocations, search/OwnBook protocol checkers, candidate-option suite, 200,000-line UCI fuzz tests and t23 mate/rule-50 tests pass without sanitizer diagnostics. The full release KRK test reports 0/100 single-thread misses and 0/400 two-thread misses. Its full ASan/UBSan attempt hit the 440-second test deadline while other sanitizer tests were running; that incomplete attempt is preserved and is not counted as a passing run. The unchanged test's bounded 40-root, one-trial sanitizer retry completes with 0/100 single-thread misses and 0/40 two-thread misses, exit 0 and no sanitizer diagnostic. Ten sanitizer trials per root remain unverified by this retry. See the [retry assessment](soak_all/preparation/asan-krk-retry-assessment.txt).

All seven interactive t3 clock cases pass in each build, with complete UCI traffic and measured times retained in the [clock assessment](soak_all/preparation/t3-clock-interactive-assessment.txt). Initial harness timing measurements and their corrected minimum-150-ms observation are preserved. No expected value was edited to make a check pass.

Existing t12/t22 report files retain their source trailing spaces. The global whitespace check reported those inherited lines; source/include/test checks passed.

Only `integrate/combo29-all` and `soak/combo29-all` are authorized push destinations. The preceding `soak/combo29-fixes` branch/worktree is untouched after this task began. Its last completed in-flight batch remains there without another commit or push.

Evidence: [progress](soak_all/PROGRESS.md), [preparation commands and output](soak_all/preparation/).
