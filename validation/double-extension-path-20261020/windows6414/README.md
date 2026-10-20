Frozen Forge 6.4.14 Windows correctness evidence

Source and tests: `21538ec5416c909fc98a08688242a0b3b9710b25`.
Parent: `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d` (6.4.13).
Build: LLVM-MinGW 23.1.3, C++20 Release, znver5, strict float, static linking, one job.
All eight Wine checks passed: core/reference perft, coherent TT (eight groups),
rule50, legal witness (18,947 comparisons), UCI, ponder, OwnBook (five transitions),
and bench11 node signature351,063. Output-layer SIMD/no-FMA checks passed.

The candidate initializes a stable inherited double-extension count before pruning,
restores it after same-ply null and singular verification, and assigns every searched
child the inherited count plus its own double extension. This repairs stale sibling
path state without tuning the existing singular threshold or extension limit.
Clock, TT, NNUE, evaluation and replacement policy are otherwise inherited.
All NNUE/eval source/header/weight bytes match frozen6.4.13; no redundant snapshot ran.

The originals directory retains all six actual Windows executables, static core and
frozen inputs. Exact commands, compiler/link data, stdout/stderr, full disassembly,
source/test hashes and Wine adapter provenance are in windows-originals.zip.
Final packaging/audit outputs are captured separately after this immutable snapshot.
Native sanitizer results are reported separately in repository checkpoints.
Wine establishes bounded correctness, not NPS, Elo, native Ryzen or Stockfish superiority.
