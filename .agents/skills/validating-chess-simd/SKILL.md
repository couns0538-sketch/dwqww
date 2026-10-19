---
name: validating-chess-simd
description: Use when changing SIMD or floating-point NNUE code in a UCI chess engine, preparing an x86 Windows executable, or evaluating speed and Elo claims for such a candidate.
---

# Validating chess SIMD

Preserve arithmetic semantics before measuring speed. Establish playing strength with games under equal clocks.

For the Forge reference, see [tested commands and limitations](../../../validation/nnue-avx2-9850x3d/README.md).

## Reproducible reference procedure

1. Record baseline commit, candidate commit/diff, network checksum, compiler version, complete build flags, executable checksums, target CPU and OS. Use existing isolated checkouts; create no worktree unless requested. Build an immutable baseline export and candidate in separate directories with identical compiler options. Never use the cloud CPU's `-march=native` for another person's computer.
2. For floating-point NNUE, preserve clamp operand order, each accumulation lane's sequence, multiplication association, final reduction order, rounding mode, and FTZ/DAZ settings. Keep `-fno-fast-math -ffp-contract=off`. For Ryzen Zen 5, an AVX2 comparison can use `-march=x86-64-v3 -mtune=znver5`; the shipped Zen 5 executable can use `-march=znver5 -mtune=znver5` after target compatibility checks.
3. Compile the same `tools/nnue_snapshot.cpp` against each core. Redirect stdout to separate files and run `cmp` before computing hashes. The stream compares accumulator float bits and integer evaluation outputs across legal walks, all special-move fixtures and 100,000 finite synthetic activations. It does not expose intermediate output-layer float sums or prove equivalence for NaNs.
4. Verify the emitted arithmetic with `python3 tools/check_nnue_simd.py OBJECT_OR_UNSTRIPPED_EXE`. An unchanged SSE build must fail its 256-bit instruction check; the candidate must pass. Run the complete CTest suite with `PYTHONDONTWRITEBYTECODE=1` and preserve logs.
5. Link `tools/search_benchmark.cpp` and `tools/nnue_benchmark.cpp` separately against both cores. Compare per-position depth/nodes/score/bestmove exactly. `benchmark_compare.py` verifies within-engine repeatability, not equality between engines; check cross-engine signatures explicitly. Counterbalance run order for timing experiments, retain raw repetitions and note other VM load. Kernel speed, search NPS and Elo are separate results.

Example differential build (repeat with each build directory):

```sh
g++ -std=c++20 -O3 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -I include tools/nnue_snapshot.cpp "$BUILD/libforge_core.a" -pthread \
  -o "$BUILD/nnue_snapshot"
"$BUILD/nnue_snapshot" > "$BUILD/nnue-snapshot.bin"
```

## Windows and match evidence

Set `LLVM_MINGW_ROOT` to a checksum-verified LLVM-MinGW release. Configure a separate Release build with `-DCMAKE_TOOLCHAIN_FILE=tools/windows-zen5.cmake`. Inspect PE architecture/imports and run the delivered executable's UCI, pondering, legal-search and bench checks. Report Wine and native Windows separately; PE inspection alone is insufficient runtime evidence.

Run a pinned Fastchess A/A calibration before A/B. Freeze settings, openings, hashes and stopping rules. Equal-clock SPRT acceptance supports an improvement over its specified opponent; fixed-node identity and faster inference do not. A positive estimate before the stopping boundary is inconclusive. A claim against Stockfish requires a pinned full-strength opponent (`UCI_LimitStrength=false`), documented resources, audited terminations and complete paired PGNs. Publish the exact tested artifact and evidence, with unresolved checks named.
