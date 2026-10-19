# Forge 6.4 AVX2 candidate for Ryzen 7 9850X3D

This is a tested SIMD candidate, not an accepted strength release. No Elo gain or superiority over unrestricted Stockfish has been established.

## Source identity

- Baseline: `9108d012526be80c6d163f7cab684e6acd9abf8d`, the existing `forge/6.4-hourly-20261019` source with corrected TT verification tags.
- Release ZIP supplied by the user: `chess-engine-forge-6.4.0.zip` at `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`; CRC validation passed. ZIP SHA-256: `98d2ff2c523a25931897794bad3c39d40398799b8907d51596dad3e326a2ba9d`.
- The baseline differs from that ZIP in `src/search.cpp` and `include/forge/search.hpp` because it retains the existing TT fix. The candidate adds an AVX2 output path in `src/nnue.cpp`; search constants and the neural network remain the baseline's.

## Verified behavior

- GCC 14.2 Linux Release: all four CTest suites passed. See `ctest-linux.xml`.
- 20,226 legal-state snapshots plus 100,000 finite synthetic evaluations produce a 21,192,328-byte stream. Baseline/candidate Linux and Windows streams compare byte-for-byte; SHA-256 for each: `3ef4bacc1877f34b929c6c4cd349c56ff0c07c93545b292914775bcd9ae173a5`.
- The stream exposes accumulator float bits and integer evaluation outputs. It does not expose intermediate output-layer float sums or establish behavior for NaNs.
- The baseline fails the 256-bit output instruction check; candidate Linux and Windows binaries pass. The final Windows PE imports Windows system/UCRT DLLs, with static C++ linkage.
- Windows core, UCI and pondering checks passed under Wine 10. Native Windows and physical Ryzen performance have not been tested. See `runtime/`.
- Linux `bench 11`: baseline/candidate 417491 nodes. Windows LLVM-MinGW `bench 11`: baseline/candidate 343022 nodes. Do not compare different-platform signatures as if they shared one baseline. A standalone equal-score `std::sort` probe reproduces differing tie orders between libstdc++ and libc++; Forge's move picker uses this unspecified tie order.

## Timing

`output-layer-paired.json` records 12 counterbalanced repetitions of five million calls per executable. Excluding the first repetition, medians were approximately 96.37 ns/call baseline and 67.00 ns/call candidate: 43.8% more output-layer calls per second on the Intel Xeon VM. This is not an engine-wide speedup, physical Ryzen measurement or Elo result.

`search-paired/` is the initial experiment whose order was biased by the old benchmark script. It is retained for audit, not used as the final timing comparison. `search-balanced/` uses the corrected runner with 11 rotations and identical per-position signatures. Shared-VM timings vary substantially; inspect raw repetitions instead of treating a median difference as an established hardware gain.

## Strength evidence

Every attempt is retained under `matches/`, including failures. `protocol.json` and `command.json` freeze settings before the respective games. Linux A/A calibration passed. Wine A/A required CRLF normalization and OwnBook=false; the corrected calibration passed. An initial raw Wine run failed parsing CRLF moves, and the next book-enabled run failed deterministic-sequence validation; neither establishes an engine strength defect.

The short-clock Windows SPRT, Linux SPRT and Stockfish pilot stopped on timeouts. Their outcomes are invalid strength evidence, and must not be pooled into later runs. Separately registered `standard-baseline/` and `standard-stockfish/` use 10+0.1 clocks and a 100 ms reserve. The latter explicitly disables Stockfish's strength limiter. Both longer-control pilots also stopped on clock overruns, including the unchanged baseline. Their full attempts are invalid strength evidence. The cause has not been isolated between engine clock handling and VM scheduling/transport effects; no speculative time-manager patch was applied. Fixed-size pilots cannot establish an accepted SPRT result or broad superiority.

## Reproduce builds and checks

Use an immutable export of the baseline and the candidate checkout in separate source/build directories. The Linux comparison uses GCC 14.2, Release, `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off` for both.

```sh
cmake -S "$SOURCE" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off'
cmake --build "$BUILD" --parallel 2
PYTHONDONTWRITEBYTECODE=1 ctest --test-dir "$BUILD" --output-on-failure
g++ -std=c++20 -O3 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -I "$SOURCE/include" tools/nnue_snapshot.cpp "$BUILD/libforge_core.a" -pthread -o "$BUILD/nnue_snapshot"
"$BUILD/nnue_snapshot" > "$BUILD/snapshot.bin"
# After generating one stream per build:
cmp "$BASE_BUILD/snapshot.bin" "$CANDIDATE_BUILD/snapshot.bin"
python3 tools/check_nnue_simd.py "$CANDIDATE_BUILD/forge"
```

The Windows compiler is LLVM-MinGW 20261006 / Clang 23.1.3. Download:
`https://github.com/mstorsjo/llvm-mingw/releases/download/20261006/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64.tar.xz`.
Verify SHA-256 `5f9c6ed95b2d4bdb2869a488c5fd5857fbdabcf288a0aa3eb1da43f6a08d8ab4` before extraction/use. With `LLVM_MINGW_ROOT` set to that extracted directory:

```sh
cmake -S . -B "$WINDOWS_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE="$PWD/tools/windows-zen5.cmake"
cmake --build "$WINDOWS_BUILD" --parallel 2
python3 tools/check_nnue_simd.py "$WINDOWS_BUILD/forge.exe"
objdump -p "$WINDOWS_BUILD/forge.exe"
```

The toolchain explicitly uses `-march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static`. This is CPU targeting, not measured proof that these flags are optimal on a 9850X3D.

To validate on Windows, run `forge_tests.exe`, UCI/ponder regression scripts against the actual delivered `forge.exe`, and `bench 11`. On Linux, run those binaries through a configured Wine wrapper; cross-built CTest cannot execute Windows binaries without an emulator/wrapper. The prepared cloud Wine prefix and wrapper paths are saved in environment startup instructions.

Fastchess is pinned to `60d7a7a26c6b0582a15c112fb29a1829bef2adb3`. Stockfish is the official 19 universal Linux release, archive SHA-256 `9defc0d4e55d49c65a6d042f3e571a39fcea499ade6dbe741b53b8c65e03611f`.

## Review and reusable guidance

An independent agent review found no blocking SIMD regressions. CodeRabbit's installer returned HTTP 403; no CodeRabbit review was obtained. SonarQube tools/CLI were unavailable; no Sonar analysis was obtained. Other named plugins without callable capabilities were not represented as used.

`.agents/skills/validating-chess-simd/SKILL.md` contains reusable validation guidance. Its baseline retrieval exercise lacked a concrete Windows build procedure; after the skill was added, an independent application test found the tools, ran the positive/negative instruction controls, compared streams and correctly rejected unsupported speed/Elo/native-hardware claims.
