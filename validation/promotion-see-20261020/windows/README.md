Frozen Forge 6.4.17 Windows correctness evidence

Source/tests: `47f0560221d986e41a309853e1295c557fcf5bf6`. Parent: `553caef144ae2e1b696ba35d7a0eb1a50a03fde9` (6.4.16).
Strict static LLVM-MinGW23.1.3 Zen5 C++20 Release build, one job, no FMA/LTO/fast-math.
Eight Wine checks passed: core/perft with 28 mirrored SEE cases, eight TT groups,
rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook transitions and
first observed candidate17 bench11 signature 382424.
That signature was unknown before execution. No prior-version count was imposed.

A rare back-rank SEE path accounts for later pawn promotion recaptures and their
new victim/material values. Ordinary threshold SEE remains inherited; promotion
exchange behavior intentionally changes. Only board.cpp, tests/tests.cpp and two
version labels differ from frozen16; NNUE/eval sources, headers and weights match.
Original 6.4.16 full TSan FAILED 8/9; its separate five-case OwnBook diagnostic remains
finite coverage only. Candidate 6.4.17 native gates are reported separately.
This Windows stage establishes bounded correctness only; it is not an accepted release.
No NPS/Elo/native Windows/Ryzen claim follows. All original PEs/core/source/logs retained.
