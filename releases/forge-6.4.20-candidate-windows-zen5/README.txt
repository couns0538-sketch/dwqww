Forge 6.4.20 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.20-ryzen-9850x3d.exe as a UCI engine.
Source/tests fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e; parent 61f598056572dfade6994af8ad2e38817cd28aa3 (6.4.19).

Pawn-span geometry replaces a per-pawn loop with a pure constexpr unsigned
forward_fill using unsigned shifts of 8/16/32 bits of the existing enemy pawn attack mask. This
performance hypothesis intends exact 6.4.19 evaluation and search parity. bitboard.hpp
and eval.cpp change; Board, NNUE source/headers/weights, search, evaluation
parameters and all earlier tests remain unchanged.

Eleven Wine checks passed: core/perft, 54 correction-history assertions, 347 runtime
PSQT assertions, 37,320 pawn-span assertions, eight TT
groups, rule50, 18,947 legal witnesses, UCI, ponder, five OwnBook transitions and
exact preregistered parent bench signature 352313. Three constexpr assertions compiled.
AVX2 clamp/multiply/add and output-layer checks passed without fused arithmetic.
Strict LLVM-MinGW 23.1.3 C++20 Release -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking, j1, no LTO.
Nine actual built PEs, core, both runtime and pawn test objects, frozen source and
all original commands/stdout/stderr/disassembly remain in windows-originals.zip.

This is an unaccepted candidate. Native 20 gates and differential checks are
reported separately. Original 6.4.16 TSan FAILED 8/9 remains qualified. No measured
speed, NPS or Elo improvement, native Windows/physical Ryzen testing, or Stockfish
superiority is established.

Optional tests: forge_tests.exe; forge_correction_history_tests.exe;
forge_runtime_psqt_tests.exe; forge_pawn_span_tests.exe; forge_tt_tests.exe;
forge_rule50_tests.exe; forge_legal_witness_tests.exe legal_witness_fixtures.tsv
forge-10000.epd. See provenance.json, source-hashes.json, test-hashes.json,
nnue-parent-identity.json, windows-originals-SHA256.json and SHA256SUMS.
