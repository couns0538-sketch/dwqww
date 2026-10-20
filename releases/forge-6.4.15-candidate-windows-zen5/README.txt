Forge 6.4.15 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.15-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
Frozen source and tests: 8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad. Parent: 21538ec5416c909fc98a08688242a0b3b9710b25 (6.4.14).

This candidate excludes virtual non-king SEE recaptures that expose their king.
The target remains occupied so recaptures along a pin remain eligible; the existing
king-recapture safety checks remain. Permanent mirrored fixtures cover absolute and
diagonal pins, departed pinners, newly exposed pins, captured ghosts, legal equal-value
alternatives, en passant and all promotion pieces. No Elo gain is established.

Earlier clock, TT, legal/rule50, OwnBook, double-extension and NNUE fixes remain.
Finite timed UCI searches charge admission; unset analysis/ponder clocks remain
worker-local, and ponder budgets start at hit. Lifecycle changes still need all
accessors quiescent. Rule50 grouping remains a history heuristic. NNUE/eval source,
headers and weights match frozen 6.4.14 exactly.

Eight Wine10 checks passed: core/reference perft and permanent SEE regressions,
eight TT groups, rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook
transitions and bench11 at 382424 nodes (Hash16MiB/Threads1).
This is an observed candidate signature; parent node parity is not asserted for
this SEE change. AVX2 clamp, multiply/add and output-layer checks passed without FMA.

Compiler: LLVM-MinGW23.1.3, C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking, no LTO. All six built executables,
actual core, frozen source, commands, stdout/stderr and disassembly are in the
manifest-verified windows-originals.zip. Original files remain retained.
Native sanitizer results are reported separately in repository checkpoints.
The prior 6.4.14 native bench-output anomaly remains qualified in its separate evidence.

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
