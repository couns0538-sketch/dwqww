Frozen Forge 6.4.13 Windows correctness evidence

Source and tests: `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d`.
Build: LLVM-MinGW 23.1.3, C++20 Release, znver5, strict float and static linking, one job.
All eight Wine checks passed: core/reference perft, coherent TT (eight groups), rule50,
legal witness (18,947 comparisons), UCI, ponder, OwnBook (five transitions), and
bench11 node signature 351,063. Output-layer SIMD and no-fused-arithmetic checks passed.

The candidate reconciles the newer accepted clock contract with the current engine.
Finite clocked UCI searches charge admission delay. Untimed depth/node/mate, infinite
and ponder searches retain worker-local reporting origins when no origin is supplied.
The accepted start_time field takes precedence over the supported request_start alias.
Ponder budgeting still starts at ponderhit. Existing deadline, helper-zeroing, gated
single-worker TT and all earlier fixes remain. All NNUE/eval source/header/weight bytes
match frozen6.4.12; no redundant large differential snapshot was needed or run.

The originals directory retains all six actual Windows executables, static core and
frozen build inputs. Exact commands, compiler/link data, stdout/stderr, full disassembly,
source/test hashes and Wine OwnBook adapter provenance are included in windows-originals.zip.
Its per-file manifest is checked against every archived original byte.

Native ASan/UBSan and TSan validation is reported separately in repository checkpoints.
Wine establishes bounded correctness; no NPS, Elo, native Windows, physical Ryzen or
Stockfish superiority is established. No timed match or new NPS measurement was run.
