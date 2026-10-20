Forge 6.4.14 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.14-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
Frozen source and tests:21538ec5416c909fc98a08688242a0b3b9710b25.

This candidate repairs double-extension counters reused across search branches.
It starts each call from a stable inherited path count before pruning, restores
that count after same-ply null/singular verification, and assigns the correct
count for every searched move, including single extensions. The existing
singular thresholds and extension budget are unchanged. Independent search-trace
evidence belongs to the repository experiment; no Elo gain is established.

The6.4.13 clock contract, earlier TT, legal/rule50, OwnBook and NNUE fixes remain.
Finite timed UCI searches charge admission; unset analysis/ponder clocks remain
worker-local, and ponder budgets start at hit. The inherited TT owner gate applies
only to opted-in single-worker UCI searches; default/SMP callers retain stripes.
Foreign diagnostics can wait for the whole search. Lifecycle changes still need
all accessors quiescent. Rule50 grouping is a heuristic, not universal history
correctness. NNUE/eval source, headers and weights match frozen6.4.13 exactly.

Eight Wine10 checks passed: core/reference perft, eight TT groups, rule50,
18,947 legal-witness comparisons, UCI, ponder, five OwnBook transitions and
bench11 at351,063nodes (Hash16MiB/Threads1), matching Windows6.4.13. AVX2 clamp,
multiply/add and output-layer checks passed, without fused arithmetic.

Compiler: LLVM-MinGW23.1.3, C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking. All six built executables,
actual core, frozen source, commands, stdout/stderr and disassembly are in the
manifest-verified windows-originals.zip. Original files remain retained.
Native sanitizer results are reported separately in repository checkpoints.

This is a correctness candidate; no accepted NPS or Elo improvement exists.
No Windows throughput or timed match was run. Native Windows, physical Ryzen
and Stockfish superiority remain unproven. Earlier validator bundles are separate.

Optional tests:
forge_tests.exe
forge_tt_tests.exe
forge_rule50_tests.exe
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

See source-hashes.json, test-hashes.json, nnue-parent-identity.json,
provenance.json, windows-originals-SHA256.json and SHA256SUMS.
