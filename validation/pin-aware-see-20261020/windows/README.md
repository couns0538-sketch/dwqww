Frozen Forge 6.4.15 Windows correctness evidence

Source and tests: `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad`. Parent: `21538ec5416c909fc98a08688242a0b3b9710b25` (6.4.14).
Build: LLVM-MinGW 23.1.3, C++20 Release, znver5, strict float, static linking, one job.
All eight Wine checks passed: core/reference perft and permanent mirrored SEE regressions,
coherent TT (eight groups), rule50, legal witness (18,947 comparisons), UCI, ponder,
OwnBook (five transitions), and bench11 observed candidate signature 382424.
Output-layer SIMD/no-FMA checks passed. The signature is not a parent-parity gate.

Virtual SEE recaptures exclude non-king pieces whose departure exposes their king.
The exchange target remains occupied; along-pin recaptures and existing king checks remain.
Exactly CMakeLists.txt, src/board.cpp, src/uci.cpp and tests/tests.cpp differ from frozen parent.
All NNUE/eval source/header/weight bytes match frozen 6.4.14; no redundant snapshot ran.

The originals directory retains all six actual Windows executables, static core and
frozen inputs. Exact commands, compiler/link data, stdout/stderr, full disassembly,
source/test hashes and Wine adapter provenance are in windows-originals.zip.
Final packaging/audit outputs are captured separately after this immutable snapshot.
Native sanitizer results are reported separately in repository checkpoints.
The prior 6.4.14 native bench-output anomaly remains qualified in its separate evidence.
Wine establishes bounded correctness, not NPS, Elo, native Ryzen or Stockfish superiority.
