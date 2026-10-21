# Frozen Forge 6.4.21 Windows correctness evidence

Source/tests `2e151d019bc58dff2ab4e76e99ef99516af8d222`, parent `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e` (6.4.20).
Strict static LLVM-MinGW 23.1.3 Zen5 C++20 Release, j1, no FMA/LTO/fast-math.
Twelve Wine checks passed: core/perft, 54 correction-history, 347 runtime PSQT,
37,320 pawn-span and 791,680 nearest-pawn comparisons
across 395,840 sets; eight TT groups, rule50, 18,947 legal
witnesses, UCI/ponder, five OwnBook transitions and exact parent signature 352313.
Three pawn-span and six nearest-pawn constexpr assertions compiled.
Nearest-pawn geometry intends exact evaluation/search parity. bitboard.hpp/eval.cpp
change; Board, NNUE, search, parameters and all earlier tests remain unchanged.
Native 21 qualification is separate. Original 6.4.16 TSan FAILED 8/9 remains qualified.
All actual PEs/core, runtime/pawn/nearest objects, source, commands and logs remain.
No new 21 speed, NPS, Elo, native Windows/Ryzen or Stockfish claim follows.
