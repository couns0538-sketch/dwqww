# S37 NNUE inference microbench — how to build and run

`tools/nnue_microbench.cpp` times the engine's own NNUE and evaluation code (from `forge_core`: `src/nnue.cpp`,
`include/forge/nnue.hpp`, the HCE and the search's `Worker::static_evaluate`) per stage, single-threaded, on a fixed
corpus, and checks its own numbers against the engine. It is a separate executable; the engine is not changed
(patch: `forge_sol_S37_nnue_microbench_20261027.patch` = the tool, the WAC300 copy and 7 CMake lines).

## Build
- CMake: target `forge_nnue_microbench` (always built, like `forge_bench`); CTest `forge_nnue_microbench_check`
  runs the consistency checks only (`--check-only --positions 2000`), so CI covers it under ASan/UBSan/TSan.
- PC lock recipe: `bash build_microbench_pc.sh <tree> <out.exe> avx2|scalar` (this folder). `avx2` = the lock
  flags (`-march=znver5`, nnue::evaluate takes its AVX2 branch). `scalar` = S11's scalar NNUE build for nnue.cpp and
  the tool: `-U__AVX2__ -U__SSE__ -fno-tree-vectorize -fno-tree-slp-vectorize` + `scalar_nnue_prelude.hpp` (copied
  from opus-sol-S11; undefines MinGW's `_M_X64/_M_AMD64`). The script prints packed/scalar float op counts of
  `forge::nnue::` (scalar: 0 packed). Another net: copy the tree and replace `src/nnue_weights.inc`.

## Run
```
forge_nnue_microbench --wac tools/nnue_microbench_wac300.epd [--positions 10000] [--repeats 15] [--call-repeats 2]
                      [--dump-fens fens.txt] [--json out.json] [--label lock_avx2] [--check-only]
forge_nnue_microbench --fens FILE ...        (FEN per line, text before '|'; instead of the generated corpus)
```
Corpus: the 8 bench FENs of `src/uci.cpp` + the 300 WAC positions, then round-robin random walks of 1-8 plies per
root (fixed LCG), deduplicated by Zobrist key, until 10,000 positions; every legal move of every position is an
update pair (346,182 for 10k). Same corpus on every run (dump sha256 d238dc06…).

Stages: `refresh`, `dirty` (dirty_pieces), `update_quiet` / `update_capture` / `update_castle` (nnue::update's three
paths), `output` (nnue::evaluate: SCReLU + affine, fused), `activation` + `affine` (a replica of nnue::evaluate split
into two loops, same code path and association; checked bit-exact against nnue::evaluate on every position),
`whole_refresh` / `whole_update` / `whole_cached` (Worker::static_evaluate: refresh path, lazy-update path of a
child, valid accumulator), `hce_uncached` (Evaluator::evaluate_uncached).

Timing: each stage is timed in regions (chunks of 32 positions; output/activation/affine walk the chunk 4 times
on the hot accumulators; updates grouped kind by kind, up to 32 parents per region). Per region the TSC (rdtsc with
lfence) and the thread's CPU time (Windows QueryThreadCycleTime, Linux CLOCK_THREAD_CPUTIME_ID) are read and the
measured empty-region overhead is subtracted; `--repeats` passes give a median and p90 of CPU ns/call. A separate
per-call pass gives the per-call median/p90 (resolution = one TSC step, ~10 ns on Zen). CPU time is the primary
number on a shared machine; all figures are advisory.

Checks (every run): replica == nnue::evaluate; incremental accumulator == refreshed accumulator (bitwise) and the
same eval; whole static eval == clamp(evaluate_uncached + net) for parents and all children. Checksums (sums and
FNV-1a of the per-position net and total evals) are printed for comparison with an independent harness.

## Job tools (this folder)
- `build_microbench_pc.sh`, `scalar_nnue_prelude.hpp`: PC builds (see above).
- `s37_cost_table.py`: aggregates `<config>_round<k>.json` runs into the cost table; checks that all runs passed,
  that checksums agree across rounds and AVX2/scalar, and that they equal `nnue_check.cpp` (lock archive
  `5_nnue/tools/`, built per net with the lock recipe) on the same FEN dump (sums and per-position FNV).
- `logs/`: builds, runs, the table (`logs/cost_table_runs4.txt`, `logs/runs4/cost_table.json`), CTest, mutants.
