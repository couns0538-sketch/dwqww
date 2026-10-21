# Frozen Forge 6.4.22 Windows correctness evidence

Source/tests `ff2e269c6058be84456e3b98344826d17b0056eb`, parent `2e151d019bc58dff2ab4e76e99ef99516af8d222` (6.4.21).
Strict static LLVM-MinGW 23.1.3 Zen5 C++20 Release, j1, no FMA/LTO/fast-math.
Thirteen Wine checks passed: core/perft, 56 PV metadata assertions, 54 correction-history, 347 runtime PSQT,
37,320 pawn-span and 791,680 nearest-pawn comparisons
across 395,840 sets; eight TT groups, rule50, 18,947 legal
witnesses, UCI/ponder, five OwnBook transitions and first-capture candidate signature 334752.
Three pawn-span and six nearest-pawn constexpr assertions compiled.
PV metadata save/restore intentionally changes search behavior. Only search.cpp
and version/test metadata change; Board, NNUE, evaluation, parameters and all earlier tests remain unchanged.
Native 22 qualification is separate. Original 6.4.16 TSan FAILED 8/9 remains qualified.
All actual PEs/core, runtime/pawn/nearest/PV metadata objects, source, commands and logs remain.
No new 22 speed, NPS, Elo, native Windows/Ryzen or Stockfish claim follows.
