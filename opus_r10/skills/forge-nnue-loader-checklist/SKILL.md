---
name: forge-nnue-loader-checklist
description: Checklist for adding or changing a neural-net loader / eval path in Forge (FORGENN2, FORGENN3/v4, the R10 HalfKA K32H3^ .nnue path) - read the exporter not your memory, validate hashes + exact size + accumulator range, reject bad files cleanly over UCI, keep the option OFF bench equal to the lock pins, test ON bench stability, SIMD == scalar, incremental == refresh, thread safety, CMake/CTest/CI, and the concrete mistakes made on 2026-10-30. Use before writing or reviewing any loader, any new UCI eval-file option, or a net from a new trainer version.
---

# NNUE loader checklist (from R10, 2026-10-30)

Rules: [[forge-pc-rules]]. Parity method: [[forge-halfka-parity-test]]. Trainer: [[forge-nnue-pytorch-amd]].
Older paths: [[forge-nnue-v3]] (FORGENN3/4).

## Before writing code
1. Read the trainer's exporter and feature code of the EXACT version that produced the nets (git log of the clone):
   nnue-pytorch b2614500 (2026-10-28) has no "HalfKAv2_hm"; its king feature set is **K32H3^** (32 mirrored king
   buckets x 3 states = 96 buckets x 704 planes), the default net adds Full_Threats + PP_3Wide, and the layer stacks are
   32 buckets with [x^2, x] activations and a skip output; FT weights are int8 for K32H3. Names in a job text can be stale.
2. Confirm the layout on a real export before trusting it: compute the expected byte size from the header fields and
   compare with the file (R6's `r6_k32h3_l256.nnue`: 17,642,340 bytes, exact).
3. Decide what "exact parity" means: run the trainer's own forward (float64) as the reference; mimic its rounding,
   including fake-quantization epsilons (see the parity skill).

## Loader must
- check version, network hash, FT hash and every stack hash; derive sizes from hashes (L1 = (ft_hash ^ feature_hash)/2)
  and require the exact file size (a truncated file must not half-load);
- reject other feature sets / architectures with a clear message, never guess;
- prove int16 accumulators cannot overflow: |bias| + 32 x max|w| <= 32767 per output, else reject;
- keep the previous state on failure and turn the eval OFF after a failed explicit load (the R10 UCI option does);
- be read-only during search (load only from setoption, which stops the search first).

## UCI and identity
- Advertise the option (`type string default <empty>`): the PC gate runner checks that options it sets are advertised.
- OFF (default): `uci_check.py <exe> --full` ALL OK (bench 312866/862329/3024920/12389307/34048354, perft5 4865609).
- ON: bench stable over repeats and reloads; bad files (truncated, wrong version, garbage, empty, missing) answer
  `info string ERROR ...` and the bench falls back to the lock pin (`opus_r10/tools/halfka_uci_check.py`).

## Kernels and search
- SIMD vs scalar on every parity position (counts must be 0); `maddubs` needs inputs <= 127 so pairs cannot saturate.
- Incremental vs refresh: random-line walk (from the parent and from several plies back) AND an in-search verify build
  (`-DFORGE_HALFKA_VERIFY`) with Threads > 1.
- Per-worker accumulator storage (no shared mutable state); refresh when the own king square or the feature state changes.

## Build, test, CI
- Box build with `FORGE_EXTRA_SRCS="src/<new>.cpp"`, add the file to `forge_core` in CMakeLists, then CMake all targets
  + CTest (KNOWN-FAILURE CHECK: PASS) before the CI push; the 6 `-Wconversion` warnings in search.cpp are the lock's.

## Speed (lessons of the R10 v2 kernels, 2026-10-30)
- Time every stage before optimising (`opus_r10/tools/halfka_tool.cpp speed`): refresh, update, forward, and the lock's
  FORGENN2 + HCE for comparison. In R10 (v1) the forward was 73-83% of the HalfKA cost per evaluation.
- Always time the SIMD path against the "scalar" one: with `-march=znver5` GCC turns a plain int8 x uint8 dot loop into
  AVX-512 VNNI (`vpdpbusd` zmm), which beat the first hand-written AVX2 forward at L1 1024 (608 vs 873 ns).
- No per-call zero fill of large buffers (the first forward cleared a 4 KB `std::array{}` every evaluation); zero only
  the padding that a kernel reads.
- Column-wise block kernel for the first dense layer: regroup the weights at load time (per 4-input block, the 4 weights
  of every output), broadcast each nonzero block, no horizontal sums; integer sums stay exact in any order.
- `std::vector` storage is only 16-byte aligned on MinGW: 512-bit row loads split cache lines (the AVX-512 refresh was
  slower than AVX2 at L1 256/1024); align FT rows and accumulator rows to 64 bytes before blaming the kernel.
- Measure a kernel change with the SAME net in two builds (identical trees, node counts must match), plus an A/A set:
  `nps_opts_ab.py --set old=exe=<v1>,EvalFileHalfKA=<net> --set new=exe=<v2>,... --set aa=exe=<v1>,...`.
- The OFF path must cost nothing: A/B the new exe with the option off against the lock exe
  (`D:/grok-pc-data/dwqww/.claude/worktrees/b/base/forge_lock_copy.exe`, sha256 5d4df7f1...).
- Check the eval sign and scale with a mirrored pair of queen-up FENs (`opus_r10/logs/sign_check.log`): the R10 test
  nets had the right sign but a queen worth only 2.5-4 pawns, which the lock's search margins do not expect.

## Mistakes made (do not repeat)
- `AccumulatorStack::ensure()` called `l1()`, which inside the class meant the member (0), not the namespace function:
  zero-size buffer, segfault on the first ON search. Qualify (`forge::halfka::l1()`), and debug crashes with a `-g -O1`
  build under `C:\msys64\ucrt64\bin\gdb.exe -batch -ex "run < in.txt" -ex bt` (found it in one run).
- CPU training with nnue-pytorch holds ~5.1-5.4 GB private memory even for L1 64 and a 17 MB binpack: the R6 RAM guard
  (7 GB floor) ended both runs; save a checkpoint every short epoch (`--epoch-size 200000 --save-last-network True`).
