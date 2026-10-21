# Frozen Forge 6.4.23 Windows correctness evidence

Source/tests `1d3ed25bea2c8b781f7ee5a178af0f66061b3984`, parent `ff2e269c6058be84456e3b98344826d17b0056eb` (6.4.22).
Strict static LLVM-MinGW 23.1.3 Zen5 C++20 Release, j1, no FMA/LTO/fast-math.
Thirteen Wine checks passed: core/perft, 56 PV metadata assertions, 54 correction-history, 347 runtime PSQT,
37,320 pawn-span and 791,680 nearest-pawn comparisons
across 395,840 sets; twelve TT groups, rule50, 18,947 legal
witnesses, UCI/ponder, five OwnBook transitions and first-capture candidate signature 334752.
Three pawn-span and six nearest-pawn constexpr assertions compiled.
TT occupied-hit generation refresh intentionally changes replacement/admission/hashfull policy.
Only search.cpp, existing TT tests and version metadata change; Board, NNUE,
evaluation, parameters and all other tests remain unchanged.
Native 23 qualification is separate. Original 6.4.16 TSan FAILED 8/9 remains qualified.
All actual PEs/core, runtime/pawn/nearest/PV metadata/TT objects, source, commands and logs remain.
No new 23 speed, NPS, Elo, native Windows/Ryzen or Stockfish claim follows.
