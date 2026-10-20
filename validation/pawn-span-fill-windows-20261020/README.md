# Frozen Forge 6.4.20 Windows correctness evidence

Source/tests `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`, parent `61f598056572dfade6994af8ad2e38817cd28aa3` (6.4.19).
Strict static LLVM-MinGW 23.1.3 Zen5 C++20 Release, j1, no FMA/LTO/fast-math.
Eleven Wine checks passed: core/perft, 54 correction-history checks, 347 runtime
PSQT checks, 37,320 pawn-span checks, eight TT groups,
rule50, 18,947 legal witnesses, UCI, ponder, five OwnBook transitions and exact
preregistered parent bench signature 352313. Three constexpr assertions compiled.
Pawn-span geometry fill intends exact evaluation/search parity. bitboard.hpp and
eval.cpp intentionally change; Board, NNUE source/weights, search, parameters and
all earlier tests remain unchanged. Native 20 gates/differential evidence remain
separate. Original 6.4.16 TSan FAILED 8/9 remains qualified. No speed, NPS, Elo,
native Windows/physical Ryzen or Stockfish claim follows. Actual PEs/core/runtime
and pawn test objects, source, commands and original logs are retained.
