Forge 6.4.24 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.24-ryzen-9850x3d.exe as a UCI engine.
Source/tests 7db08eac6ead99d641834c56ccec06a06600586a; parent 1d3ed25bea2c8b781f7ee5a178af0f66061b3984 (6.4.23).

Pure SEE proof reuse avoids repeated exchange queries already established by
Main GoodCaptures in the unchanged Board scope. Reuse has an actual threshold <= 0
guard and defined arithmetic; exact search parity and unchanged evaluation are intended.
Only search.cpp, existing core tests and version metadata change. Board, NNUE
source/headers/weights, evaluation and evaluation parameters and all other tests remain unchanged; TT refresh and the accepted PV metadata fix are retained.

Thirteen Wine checks passed: core/perft and 504 SEE threshold assertions, 56 PV metadata assertions, 54 correction-history, 347 runtime PSQT,
37,320 pawn-span and 791,680 nearest-pawn comparisons
across 395,840 sets; twelve TT groups, rule50, 18,947 legal
witnesses, UCI/ponder, five OwnBook transitions and first-capture candidate signature 334752.
Three pawn-span and six nearest-pawn constexpr assertions compiled.
AVX2 output-layer checks passed with no fused operations. Strict LLVM-MinGW 23.1.3
Zen5 C++20 Release/static, j1, no FMA/LTO/fast-math. All eleven built PEs, actual core,
runtime/pawn/nearest/PV metadata/TT/core test objects, frozen source and original commands/streams/logs
remain in verified windows-originals.zip.

This is an unaccepted candidate. Native 24 gates and differential checks are
reported separately. Original 6.4.16 TSan FAILED 8/9 remains qualified. No measured
24 speed, NPS or Elo improvement, native Windows/physical Ryzen testing, or
Stockfish superiority is established. Parent 23 performance does not validate 24.

Optional tests: forge_tests.exe; forge_correction_history_tests.exe;
forge_runtime_psqt_tests.exe; forge_pawn_span_tests.exe; forge_nearest_pawn_tests.exe; forge_pv_metadata_tests.exe;
forge_tt_tests.exe; forge_rule50_tests.exe; forge_legal_witness_tests.exe
legal_witness_fixtures.tsv forge-10000.epd. See provenance.json, source/test hashes,
nnue-parent-identity.json, windows-originals-SHA256.json and SHA256SUMS.
