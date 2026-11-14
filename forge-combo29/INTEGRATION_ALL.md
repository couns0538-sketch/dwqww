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

The complete test-folder matrix is in progress; no all-tests-pass claim is made yet. Existing t12/t22 report files retain their source trailing spaces. The global whitespace check reported those inherited lines; source/include/test checks passed.

Only `integrate/combo29-all` and `soak/combo29-all` are authorized push destinations. The preceding `soak/combo29-fixes` branch/worktree is untouched after this task began. Its last completed in-flight batch remains there without another commit or push.

Evidence: [progress](soak_all/PROGRESS.md), [preparation commands and output](soak_all/preparation/).
