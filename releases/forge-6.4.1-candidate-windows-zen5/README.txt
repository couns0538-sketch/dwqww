Forge 6.4.1 candidate — Windows x64 / Ryzen 7 9850X3D (Zen 5)

Add forge-6.4.1-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
The neural network and opening book are embedded.

Changes from the earlier AVX2 candidate:
- Charge UCI parsing and thread dispatch against the move budget.
- Recognize stalemate before evaluation, cached scores and search pruning.
- Retain the AVX2 NNUE path and unchanged evaluation weights.

This is a correctness candidate, not an accepted Elo release. No Elo gain or
superiority over unrestricted Stockfish has been established. CPU targeting
has not been benchmarked on a physical 9850X3D. Core, UCI and pondering tests
passed under Wine 10; native Windows testing remains outstanding.

Compiler: LLVM-MinGW 20261006 / Clang 23.1.3, Release,
-march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static.
Source: fab979c (forge/clock-safety-9850x3d).
Validation: validation/clock-safety-9850x3d/ in the same GitHub repository.
Run forge_tests.exe from a terminal for the included functional checks.
