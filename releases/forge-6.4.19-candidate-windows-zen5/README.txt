Forge 6.4.19 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.19-ryzen-9850x3d.exe as a UCI engine.
Source/tests 61f598056572dfade6994af8ad2e38817cd28aa3; parent fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b (6.4.18).

Private Worker lazy packed PSQT and unclamped phase cache reuses inherited NNUE
dirty replay. This performance hypothesis intends exact 6.4.18 evaluation and search
parity. Eval/search implementation and their headers change; Board, NNUE source
and weights, evaluation parameters and all earlier tests remain unchanged.

Ten Wine checks passed: core/perft, 54 correction-history assertions, runtime PSQT
contract (347 assertions), eight TT groups, rule50, 18,947 legal witnesses,
UCI, ponder, five OwnBook transitions and exact preregistered parent bench signature 352313.
AVX2 clamp/multiply/add and output-layer checks passed without fused arithmetic.
Strict LLVM-MinGW 23.1.3 C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking, j1, no LTO.
Eight actual built PEs, core, runtime test object, frozen source and all original
commands/stdout/stderr/disassembly remain in verified windows-originals.zip.

This is an unaccepted candidate. Native 19 gates and differential checks are
reported separately. Original 6.4.16 TSan FAILED 8/9 remains qualified. No measured
speed, NPS or Elo improvement, native Windows/physical Ryzen testing, or Stockfish
superiority is established.

Optional tests: forge_tests.exe; forge_correction_history_tests.exe;
forge_runtime_psqt_tests.exe; forge_tt_tests.exe; forge_rule50_tests.exe;
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd.
See provenance.json, source-hashes.json, test-hashes.json, nnue-parent-identity.json,
windows-originals-SHA256.json and SHA256SUMS. Native differential evidence is separate.
