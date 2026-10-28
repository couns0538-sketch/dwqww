# S37 idea sources

- **Spec**: Sol's S37 "NNUE inference microbench + per-stage cost table" (SOL_LEFTOVERS_FOR_CLAUDE.md item 19;
  inventory `jobs[S37].spec_verbatim`): own CMake target, engine binary unchanged, 10k fixed FENs from bench + WAC,
  refresh / incremental update / output layer / whole evaluate(), median and p90 ns/call, eval checksum equal to the
  engine's own eval, cost table for the lock net and e48f006, scalar vs AVX2. Sol left no prepared S37 files.
- **Engine code measured**: `src/nnue.cpp` (refresh, update's quiet/capture/generic paths, evaluate's AVX2/SSE/scalar
  branches, dirty_pieces), `Worker::static_evaluate` (search.cpp), `Evaluator::evaluate_uncached` (eval.cpp).
- **Existing lock tools** (ideas): `tools/nnue_benchmark.cpp` (isolated output-layer timing with a checksum) and
  `tools/nnue_snapshot.cpp` (refresh vs update on every legal first move).
- **Engine-eval reference**: the lock archive's `5_nnue/tools/nnue_check.cpp` (prints net / HCE / total per FEN), as
  used by opus-sol-S21 and S31 for "Python forward == forge::nnue".
- **Scalar build**: opus-sol-S11 `build_pc_scalar_nnue.sh` + `scalar_nnue_prelude.hpp` (flags and forced include).
- **Private access**: the `forge::SearcherTestProbe` friendship that `tests/tests.cpp` already uses.
- **Timing method**: rdtsc with lfence/rdtscp serialization (G. Paoloni, "How to Benchmark Code Execution Times on
  Intel IA-32 and IA-64 Instruction Set Architectures", Intel 2010); per-thread CPU time via QueryThreadCycleTime
  (Windows) / CLOCK_THREAD_CPUTIME_ID (POSIX); empty-region overhead subtraction; medians over repeated passes.
- Own design: deterministic bench+WAC random-walk corpus, region chunking, the kind-major update grouping, the
  bit-exact activation/affine replica, the cross-variant/cross-harness checksum check.
