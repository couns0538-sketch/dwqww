PROPOSAL N2: Update P3b's Linux build plan to (a) fix `source/CMakeLists.txt` / add a Linux Clang ThinLTO+PGO script that defines `FORGE_NNUE_V3=1` and `FORGE_MATE_ALPHA_GUARD=1` and decouples `FORGE_SPD_SLIDER_PEXT` from `FORGE_SPD_NNUE_ZMM`, and (b) add an AVX2 fused `apply_pair_and_sum_avx2` + 4-column unrolled `refresh_from_pieces` path if the rented 64-core server lacks AVX-512.

KIND: measurement

EVIDENCE:
1. Stock `source/CMakeLists.txt:27-40` omits `FORGE_NNUE_V3=1` and `FORGE_MATE_ALPHA_GUARD=1`, and `FORGE_PORTABLE=ON` (`CMakeLists.txt:17,36-38`) forces BOTH `FORGE_SPD_SLIDER_PEXT=0` and `FORGE_SPD_NNUE_ZMM=0` together. Meanwhile `loop/build_recipe/build_forge_clang_pgo.sh` is Windows/MinGW-only (`cygpath`, `clang++.exe`) and `loop/build_recipe/pgo_selfgame.py:9` hardcodes `C:/nnue-lab/pipeline`.
2. Raw local build test on Linux (`cmake -S source -B /tmp/forge-cmake-build -DCMAKE_CXX_COMPILER=g++ && cmake --build /tmp/forge-cmake-build -j4`, then feeding `loop/LOOP_OPTIONS.txt` with `loop/forge65_r0067.fnn3` and `bench 11`):
   ```text
   info string unknown option MateAlphaGuard
   info string unknown option NNUEArchFile
   info string unknown option NNUEArch
   info string bench depth 11 nodes 278016 time 152 nps 1829052
   ```
   The stock CMake build silently rejects the v3 net and `MateAlphaGuard` and runs the built-in 256-wide net (`278016` instead of `226187`).
3. Source fact on AVX2 gap: `source/src/nnue_v3.cpp:907-917` only invokes fused `apply_pair_and_sum_avx512` under `#if FORGE_NNUE_V3_AVX512`; AVX2 falls back to two separate passes (`apply_changes_pair` + `output_sum`). Likewise `refresh_from_pieces` (`source/src/nnue_v3.cpp:946-976`) only unrolls 4 columns per pass under `#if FORGE_NNUE_V3_AVX512`; AVX2 loops one column at a time (`sub_column`/`add_column`), multiplying accumulator L1 read-modify-write traffic by up to 4x on king bucket changes.
4. Raw local Linux comparison (`g++ 13.3.0 -std=c++20 -O3 -DNDEBUG ... -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, unmodified `source/src/*.cpp`, `loop/LOOP_OPTIONS.txt` + `loop/forge65_r0067.fnn3`, 3 runs of `bench 13` on this Xeon VM with AVX-512 & BMI2):
   - `-march=x86-64-v4 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1` (AVX-512 + PEXT): `616966` nodes in `268 / 260 / 268 ms` (`2.30 - 2.37 Mnps`)
   - `-march=x86-64-v3 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=0` (AVX2 + PEXT): `616966` nodes in `288 / 290 / 284 ms` (`2.13 - 2.17 Mnps`, ~8% slower)
   - `-march=x86-64-v3 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0` (AVX2, PEXT off, as `FORGE_PORTABLE=ON` does): `616966` nodes in `363 ms` (`1.70 Mnps`, ~27% slower than AVX-512+PEXT and ~21% slower than AVX2+PEXT; single run).
   All three matched `226187 / 616966` (loop+r0067) and `312866 / 862329 / 4865609` (defaults) bit-for-bit. (Note: PEXT should remain an independent flag because AMD Zen 1/2 had slow microcoded PEXT whereas Zen 3/4/5 and Intel Haswell+ have fast PEXT; the rented CPU model is not yet known.)

COST:
- Linux Clang ThinLTO+PGO build script + decoupled CMake options: ~1-2 hours engineering + 10 CPU minutes verification in WSL/Linux before the rental day.
- AVX2 fused `apply_pair_and_sum_avx2` + 4-col refresh: ~1-2 hours engineering + 5 CPU minutes bit-exactness verification (`FORGE_NNUE_V3_VERIFY=1` + 2-build speed check per `PLAN.md:164`), ONLY needed if the rented 64-core server lacks AVX-512 (skip if the server is Zen 4/5 EPYC or AVX-512 Xeon).
- GPU hours: 0.

HOW IT IS JUDGED:
1. Build on Linux (WSL rehearsal before rental, and again on the rented server at startup) using Clang ThinLTO + self-play PGO with `-march=native`, `FORGE_NNUE_V3=1`, `FORGE_MATE_ALPHA_GUARD=1`, and per-CPU tested `FORGE_SPD_SLIDER_PEXT={0,1}` (auto-benchmarked on the server in <10 s at startup: pick the faster of PEXT=0 vs PEXT=1).
2. Require exact reference pins (`312866 / 862329 / 4865609` defaults; `226187 / 616966` with `LOOP_OPTIONS.txt` + best net) and zero `unknown option` / `invalid value` lines.
3. If the server lacks AVX-512, require `apply_pair_and_sum_avx2` + 4-col AVX2 refresh to pass `FORGE_NNUE_V3_VERIFY=1` with 0 eval mismatches, match `226187 / 616966`, and beat unfused AVX2 across 2 independent PGO builds per variant (`PLAN.md:164`) by > 2% on self-play pos/s.

WHAT WOULD CHANGE MY MIND:
- If the rented server is confirmed to be AVX-512 (e.g. AMD EPYC Zen 4/5 or Intel Xeon Sapphire/Emerald/Granite Rapids), drop part (b) (AVX2 fused kernel) immediately; part (a) (Linux ThinLTO+PGO script with `FORGE_NNUE_V3=1`, `FORGE_MATE_ALPHA_GUARD=1`, and decoupled PEXT/ZMM) still applies.
