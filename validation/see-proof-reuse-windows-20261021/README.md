# Frozen Forge 6.4.24 Windows correctness evidence

Source/tests `7db08eac6ead99d641834c56ccec06a06600586a`, parent `1d3ed25bea2c8b781f7ee5a178af0f66061b3984` (6.4.23).
Strict static LLVM-MinGW 23.1.3 Zen5 C++20 Release, j1, no FMA/LTO/fast-math.
Thirteen Wine checks passed: core/perft and 504 SEE threshold assertions, 56 PV metadata assertions, 54 correction-history, 347 runtime PSQT,
37,320 pawn-span and 791,680 nearest-pawn comparisons
across 395,840 sets; twelve TT groups, rule50, 18,947 legal
witnesses, UCI/ponder, five OwnBook transitions and first-capture candidate signature 334752.
Three pawn-span and six nearest-pawn constexpr assertions compiled.
Pure SEE proof reuse optimization preserves exact search behavior and unchanged evaluation.
Reuse is guarded by actual threshold <= 0 and defined arithmetic in the unchanged Board scope.
Only search.cpp, existing core tests and version metadata change; Board, NNUE,
evaluation, parameters and other tests remain unchanged.
Native 24 qualification is separate. Original 6.4.16 TSan FAILED 8/9 remains qualified.
All actual PEs/core, runtime/pawn/nearest/PV metadata/TT objects, source, commands and logs remain.
No new 24 speed, NPS, Elo, native Windows/Ryzen or Stockfish claim follows.
