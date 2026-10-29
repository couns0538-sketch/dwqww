# R5B idea sources

R5B builds and measures existing node-exact switches and fixes one guard; the ideas below are where each piece
comes from. Every implementation in this folder and in the engine diff is my own code.

| idea | source |
|---|---|
| N2 = one build with `-DFORGE_NNUE_O2=1 -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_SPEEDSTACK=1` | job spec R5B (Engine QA for Couns, 2026-10-29), plan N2; the switches come from opus-O2 (`opus_round1/O2`), S14 zero-fill / buffix (`fable-review-buffix`) and S29 (`opus_round1/sol_S29`), merged in `forge-bundle-int` b7c1772 (BUNDLES.md) |
| "O2's AVX2 kernels are compiled out on AVX-512 targets" | the guard comment in `src/nnue.cpp` (opus-O2) and the R3-2Q report (`opus_r3/R3-2Q/REPORT.md`, SW_V4 row); job spec open question |
| M1 fix: explicit 512-bit float accumulator kernel with register blocking (a block of vector registers stays live while every feature column is added) | the tiling of the Stockfish NNUE feature transformer (`src/nnue/nnue_feature_transformer.h`, accumulator update with `NumRegs` live vector registers and AVX-512 paths; https://github.com/official-stockfish/Stockfish) and the O2 AVX2 kernel templates already in `src/nnue.cpp`; mine is a float `__m512` `Vec` plugged into O2's templates, same per-lane operation order (node-exact) |
| Paired ABBA NPS A/B with fresh processes, node match per pair, A/A byte-copy control, paired t on log ratios | the CI method in `opus_r3/R3-2Q/ci_quietnps.sh` + `quiet_nps.py` and `opus_round1/sol_S29/nps_ab.py` (crew tools); paired-difference benchmarking as in Fishtest speed checks (https://github.com/official-stockfish/fishtest) — my own Windows implementation (`nps_ab.py`) |
| CPU time from `QueryProcessCycleTime` instead of `GetProcessTimes` (15.6 ms ticks) | Microsoft Win32 docs: QueryProcessCycleTime (https://learn.microsoft.com/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryprocesscycletime), GetProcessTimes (https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) |
| Pinning by setting the driver's own affinity (children inherit it) | Microsoft Win32 docs: SetProcessAffinityMask, CreateProcess ("the new process inherits the affinity mask of the parent", priority class inheritance for BelowNormal) |
| Poison test hook `FORGE_R5B_POISON_MOVE_BUFFERS` (fill never-initialised storage with a byte pattern so a read of an unwritten element shows) | the debug-fill technique of allocators and compilers: glibc `MALLOC_PERTURB_` / `glibc.malloc.perturb` (https://www.gnu.org/software/libc/manual/html_node/Memory-Allocation-Tunables.html), GCC/Clang `-ftrivial-auto-var-init=pattern` (https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html) |
| valgrind memcheck for uninitialised reads (OFF as control) | Valgrind manual, Memcheck "Use of uninitialised values" (https://valgrind.org/docs/manual/mc-manual.html) |
| 200-game crash/legality smoke | R5A `opus_r5/r5a/smoke.py` (branch opus-r5a-singles, crew tool); `smoke_ab.py` adds a second exe for the OFF side |
