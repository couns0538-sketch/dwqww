Frozen Forge 6.4.18 Windows correctness evidence

Source/tests: `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`. Parent: `47f0560221d986e41a309853e1295c557fcf5bf6` (6.4.17).
Strict static LLVM-MinGW23.1.3 Zen5 C++20 Release build, one job, no FMA/LTO/fast-math.
Nine Wine checks passed: core/perft with 28 mirrored SEE cases, correction-history
actual-method contract (54 checks), eight TT groups,
rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook transitions and
first observed candidate18 bench11 signature 352313.
That signature was unknown before execution. No prior-version count was imposed.

This independent unaccepted search ablation changes correction-history EMA decay
to a residual increment. It is not a known-bug repair or accepted strength
improvement. Only search.cpp, its dedicated test, CMake registration/version and UCI
version label differ from frozen17; NNUE/eval sources, headers and weights match.
Original 6.4.16 full TSan FAILED 8/9; its separate five-case OwnBook diagnostic remains
finite coverage only. Candidate 6.4.18 native gates are reported separately.
This Windows stage establishes bounded correctness only; it is not an accepted release.
No NPS/Elo/native Windows/Ryzen claim follows. All original PEs/core/source/logs retained.
