Forge 6.4.23 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.23-ryzen-9850x3d.exe as a UCI engine.
Source/tests 1d3ed25bea2c8b781f7ee5a178af0f66061b3984; parent ff2e269c6058be84456e3b98344826d17b0056eb (6.4.22).

Occupied TT hits refresh their generation under the existing lock/lease. This is
a coupled replacement/admission/hashfull policy trial with intentional search
changes. Only search.cpp, existing TT tests and version metadata change.
Board, NNUE source/headers/weights, evaluation and evaluation parameters and
all other tests remain unchanged; the accepted PV metadata fix is retained.

Thirteen Wine checks passed: core/perft, 56 PV metadata assertions, 54 correction-history, 347 runtime PSQT,
37,320 pawn-span and 791,680 nearest-pawn comparisons
across 395,840 sets; twelve TT groups, rule50, 18,947 legal
witnesses, UCI/ponder, five OwnBook transitions and first-capture candidate signature 334752.
Three pawn-span and six nearest-pawn constexpr assertions compiled.
AVX2 output-layer checks passed with no fused operations. Strict LLVM-MinGW 23.1.3
Zen5 C++20 Release/static, j1, no FMA/LTO/fast-math. All eleven built PEs, actual core,
runtime/pawn/nearest/PV metadata/TT test objects, frozen source and original commands/streams/logs
remain in verified windows-originals.zip.

This is an unaccepted candidate. Native 23 gates and differential checks are
reported separately. Original 6.4.16 TSan FAILED 8/9 remains qualified. No measured
23 speed, NPS or Elo improvement, native Windows/physical Ryzen testing, or
Stockfish superiority is established. Parent 22 performance does not validate 23.

Optional tests: forge_tests.exe; forge_correction_history_tests.exe;
forge_runtime_psqt_tests.exe; forge_pawn_span_tests.exe; forge_nearest_pawn_tests.exe; forge_pv_metadata_tests.exe;
forge_tt_tests.exe; forge_rule50_tests.exe; forge_legal_witness_tests.exe
legal_witness_fixtures.tsv forge-10000.epd. See provenance.json, source/test hashes,
nnue-parent-identity.json, windows-originals-SHA256.json and SHA256SUMS.
