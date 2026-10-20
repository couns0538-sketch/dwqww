# Frozen Forge 6.4.19 Windows correctness evidence

Source/tests `61f598056572dfade6994af8ad2e38817cd28aa3`, parent `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b` (6.4.18).
Strict static LLVM-MinGW 23.1.3 Zen5 C++20 Release, j1, no FMA/LTO/fast-math.
Ten Wine checks passed: core/perft, 54 correction-history checks, private runtime PSQT
contract (347 checks), eight TT groups, rule50, 18,947 legal witnesses,
UCI, ponder, five OwnBook transitions and exact parent bench signature 352313.
Private Worker lazy PSQT/unclamped phase replay intends exact evaluation/search
parity. Eval/search source and headers intentionally change; Board and NNUE
weights/implementation are unchanged. Native 19 gates/differential evidence are
separate; no speed, NPS, Elo, native Ryzen or Stockfish claim follows.
Original 6.4.16 TSan FAILED 8/9 remains qualified; later finite diagnostics do not erase it.
All actual PEs, core, runtime object, source, commands and raw logs remain retained.
