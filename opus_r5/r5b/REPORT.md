# Forge Opus R5B: N2 speed build (O2 + NOZERO + SPEEDSTACK) — IN PROGRESS

**Status:** 00_baseline done; M1 in progress. Last push: see the commit time (pushes every 10 min).

Branch `opus-r5b-speed` = `origin/forge-bundle-int` b7c1772 + R5B commits. Job folder `opus_r5/r5b/`, scratch
`F:\opus_scratch\r5\r5b\` (exes in `exe\`, sha256 in `EXES.txt` here and next to the exes).
Machine exclusive: no (live gates, NNUE training and self-play ran the whole time). Every build, test and bench ran
at BelowNormal (Git Bash `nice -n 10`), at most 3 threads in total, engine runs with Threads 1.
No Elo claims; no gate run by me.

Time base: the PC clock reads PST but runs 9 h ahead of GitHub's server clock (`gh api -i rate_limit` Date header,
06:53 GMT at 07:53 Vienna); Vienna (CET, UTC+1) = PC "PST" time - 1 h. Every time below is Vienna.
Job start 07:53 Vienna (3 h cap: 10:53 Vienna).

## 00_baseline (07:53-08:00 Vienna)

Two build recipes exist on this PC and they differ exactly where the O2 question lives (M1):

| recipe | flags (MSYS2 ucrt64 g++ 15.2, direct g++, static) | where it is used |
|---|---|---|
| `v3` (job spec) | `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -mtune=znver5 -pthread -static` | the job spec's flags; R5A `build_r5a.sh`; the Linux box reference (lock archive `2_build/BUILD.md`, CMake) |
| `znver5` (PC lock exe) | same, but `-march=znver5` | the PC lock exe `forge_h256_s198.exe` (`2_build/BUILD.md` "Windows"), `worktrees/b/tools/build_pc.sh`, and through it `opus_r3/R3-1/tools/build_gate_exes.sh` (the R3 gate exes) |

Build script `tools/build_r5b.sh` (8 units compiled in parallel, `JOBS` <= 3, BelowNormal, fixed link order):
```
RECIPE=v3     bash opus_r5/r5b/tools/build_r5b.sh "$PWD" /f/opus_scratch/r5/r5b/exe/forge_r5b_off_v3_b7c1772.exe
RECIPE=znver5 bash opus_r5/r5b/tools/build_r5b.sh "$PWD" /f/opus_scratch/r5/r5b/exe/forge_r5b_off_z5_b7c1772.exe
```
Check: lock `uci_check.py <exe> --full` (fresh process, Threads 1, Hash 16, OwnBook false).

## OFF identity after every milestone (rule 7)

| after | exe (F:\opus_scratch\r5\r5b\exe) | recipe | sha256 | bench d11 / d13 / d16 / d20 / d22 | perft 5 | kiwipete 5 | FMA | result |
|---|---|---|---|---|---|---|---|---|
| 00 baseline | forge_r5b_off_v3_b7c1772.exe | v3 | 71843266... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_v3_b7c1772.log`) |
| 00 baseline | forge_r5b_off_z5_b7c1772.exe | znver5 | 88e15c7d... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_z5_b7c1772.log`) |

## M1: is O2 really on? (in progress)

**Answer: on the PC lock recipe (`-march=znver5`) the O2 AVX2 kernels are compiled out; on the job-spec recipe
(`-march=x86-64-v3 -mtune=znver5`) they are on.** (R3-2Q already noted this for its x86-64-v4 CI row; here it is
read from the PC exes themselves.)

`#if` audit of `src/nnue.cpp` at b7c1772 (the O2 path):

| line | guard | v3 recipe | znver5 recipe |
|---|---|---|---|
| 41-47 | `FORGE_NNUE_SSE` = SSE available and not (O2 and FORCE_SCALAR) | 1 | 1 |
| 49-54 | `FORGE_NNUE_AVX2` = `__AVX2__` and not (O2 and FORCE_SCALAR) | 1 | 1 |
| 60-64 | `FORGE_NNUE_KERNEL_AVX2` = `FORGE_NNUE_AVX2 && !defined(__AVX512F__)` | **1** | **0** (`-march=znver5` defines `__AVX512F__`) |
| 65-69 | `FORGE_NNUE_KERNEL_SSE2` = `FORGE_NNUE_SSE && !defined(__AVX2__)` | 0 | 0 |
| 170-191 | `Vec` = `__m256` (AVX2 kernel) / `__m128` (SSE2 kernel) / `float` (portable) | `__m256` | **`float`** |
| 223-242 | refresh: register-blocked kernel if AVX2/SSE2 kernel, else copy + one pass per column | blocked | **portable** |
| 443-483 | output layer (`evaluate`): explicit AVX2 if `FORGE_NNUE_AVX2` (OFF and O2 alike) | AVX2 | AVX2 |

The guard is deliberate (comment at line 57-59: "AVX-512 targets keep the portable loops, which the compiler widens
to 512 bits itself as it does for AL1 s198"), so on the PC recipe O2 = the portable fused update loops + 64-byte
alignment, widened by g++ to zmm, without the register-blocked refresh.

Binary check (`tools/nnue_kernel_audit.sh`, objdump of the exes; log `logs/m1_kernel_audit_b7c1772.log`, the three
functions' disassembly in `logs/m1_nnue_disasm_b7c1772.txt`):

| exe | refresh: vaddps/vsubps zmm / ymm, vector stores | update: zmm / ymm add-sub, stores | evaluate | FMA |
|---|---|---|---|---|
| OFF v3 `forge_r5b_off_v3_b7c1772.exe` | 0 / 1, 1 (8-wide loop) | 0 / 7, 4 | ymm (AVX2 output layer) | 0 |
| O2 v3 `forge_r5b_o2_v3_b7c1772.exe` | 0 / **8**, 10 (8 ymm accumulators per block = the AVX2 kernel) | 0 / 11, 5 | ymm | 0 |
| OFF znver5 `forge_r5b_off_z5_b7c1772.exe` | **16** / 0, 18 (unrolled zmm copy + column loop) | 112 / 0, 66 | ymm | 0 |
| O2 znver5 `forge_r5b_o2_z5_b7c1772.exe` | **16** / 0, 17 (same portable loop as OFF) | 176 / 0, 82 | ymm | 0 |

So on znver5 the O2 refresh is the same compiler-widened loop as OFF, and no `__m256` kernel exists in the exe;
the update function differs only by the portable fused loops (castling included) that g++ widens to zmm.

## M2: reproducible NPS bench (pending)

## M3: per-switch and combined builds (pending)

## M4: non-regression evidence for N2 (pending)

## M5: proposal (pending)

## What to gate first (pending)

## What I did not finish (pending)
