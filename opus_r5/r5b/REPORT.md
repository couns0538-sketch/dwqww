# Forge Opus R5B: N2 speed build (O2 + NOZERO + SPEEDSTACK) — IN PROGRESS

**Status:** 00_baseline, M1 done; M2 driver done; M3 exes + identity done, NPS runs in progress. Last push: see the commit time (pushes every 10 min).

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

### M1 fix (commit b2983d07, engine change, all under `#if FORGE_NNUE_O2`)

Cause: the guard at `src/nnue.cpp:60` (`!defined(__AVX512F__)`), not a missing flag: `-march=znver5` enables
AVX-512, and O2 then fell back to the portable loops by design. Fix in the guard (the recipe stays the PC lock
recipe): a 512-bit `Vec` (`__m512`, 16 lanes, `_mm512_load_ps/_store_ps/_add_ps/_sub_ps`) for AVX-512 targets,
plugged into the existing kernel templates (`apply_sub_add`, `apply_sub_sub_add`, `apply_sub_add_sub_add`,
register-blocked `accumulate_columns` with 8 vectors = 128 floats per block). Node-exact: every lane sees the same
float operations in the same order as the portable loop and the AVX2 kernel (no FMA, no reassociation, IEEE add/sub
lane by lane); O2's 64-byte alignment of the weights and the Accumulator already covers 512-bit aligned loads.
Also: `forge::nnue::kernel_name()` and an `info string nnue kernel: <accumulator ...>, <output ...>` line before
`uciok`, both only in O2 builds; the parity test's kernel label names the new kernel.

| check | result | evidence |
|---|---|---|
| OFF exes unchanged | `forge_r5b_off_{v3,z5}_m1fix.exe` differ from the b7c1772 OFF exes in 4 bytes (PE timestamp) | `cmp -l`, EXES.txt |
| identity O2 znver5 (avx512 kernel) | ALL OK | `logs/identity_o2_z5_m1fix.log` |
| identity O2 v3 (avx2 kernel) | ALL OK | `logs/identity_o2_v3_m1fix.log` |
| kernel in the binary | O2 znver5 refresh: 8 `vaddps zmm` + 8 stores per block (register-blocked); update: explicit zmm kernels; FMA 0 | `logs/m1_kernel_audit_m1fix.log`, `logs/m1_nnue_disasm_m1fix.txt` |
| UCI line | O2 znver5: `info string nnue kernel: accumulator avx512, output avx2`; O2 v3: `accumulator avx2, output avx2`; OFF: no new line | manual `uci` |
| bit parity vs AL1 s198 (tests/nnue_parity_tests.cpp, box recipe, `tools/parity_r5b.sh`) | AVX-512 (znver5), AVX2 (v3) and FORCE_SCALAR (znver5) builds: PASS, same digest `f807d80cbabc1d59` over 1,303,743 positions (1,270,681 updates, 32,135 refreshes, 249,957 in-place, 8,267 castles, 100,000 synthetic evaluations) | `logs/m1_parity_o2_{z5_avx512,v3_avx2,z5_scalar}.log` |

Which O2 variant is faster on this PC is measured in M3 (arms `o2_portable` = b7c1772 O2 znver5 and
`o2_avx512` = the fix, both against the same OFF znver5 exe).

## M2: reproducible NPS bench (driver done)

`opus_r5/r5b/nps_ab.py` (+ `nps_ab.sh` wrapper; PowerShell: `& <venv python> -I -B opus_r55b
ps_ab.py ...`),
my own Windows implementation of the R3-2Q CI method (`opus_r3/R3-2Q/ci_quietnps.sh` + `quiet_nps.py`):
- arms: A (reference, the OFF build) + one or more B exes + with `--aa` the A/A control = a byte copy of A
  (sha256-checked) under another file name; slot i runs the arms in list order for even i and reversed for odd i
  (with two arms exactly ABBA), so linear drift cancels for every arm pair;
- fresh process per run: `uci`, Threads 1, Hash 16, OwnBook false, `isready`, `bench <d>`, `quit`; default
  depths 16 and 20, 12 pairs (minimum 10 enforced);
- the driver pins itself to ONE logical CPU (`--core`, default 14) and sets BelowNormal before it starts engines;
  children inherit the mask and are also created BelowNormal; the first run per arm logs the child's real affinity
  mask and priority class (`arm A child affinity mask 0x4000 priority BelowNormal`);
- primary speed = CPU-time NPS: nodes / QueryProcessCycleTime cycles between `readyok` and the bench line
  (start-up and exit excluded; cycle rate calibrated at start, 4.696 GHz here, ratios do not depend on it).
  GetProcessTimes is not used: it moves in 15.6 ms ticks (the first smoke run showed 0.172/0.188 s steps at d11);
  secondary = the engine's own nps (wall clock);
- every run of a depth must give the same node count and the pin (`--pins 16=3024920,20=12389307`), else exit 2;
- per arm and depth: mean of paired log ratios, 95 % Student t CI, median ratio, and the rule line
  (cpu lower bound >= +2 % at d16 AND d20); PC busy share (GetSystemTimes) per run and overall; JSON with every run;
- cooperative stop: `--stop-file` (checked before every run).
Noise: live gates keep the PC 80-85 % busy (all CPUs); the A/A arm is the noise floor at that moment. It cannot
see code-layout effects (same bytes), which R3-2Q found to dominate PC switch rows (NOZERO -4.2 % on the PC vs
+1.6 % on quiet runners).

## M3: per-switch and combined builds (exes + identity done; NPS running)

Exes from engine tree b2983d07 (M1 fix): OFF and O2 = `forge_r5b_{off,o2}_{v3,z5}_m1fix.exe`, NOZERO / SPEEDSTACK /
N2 = `forge_r5b_{nozero,speedstack,n2}_{v3,z5}_b2983d07.exe` (`tools/build_m3.sh`, log
`logs/m3_build_identity_b2983d07.log`). Every exe: 0 warnings, FMA 0, lock identity ALL OK (switches are node-exact,
so ON = the pins).

| switch | flags | znver5 exe sha256 | v3 exe sha256 | identity (both) |
|---|---|---|---|---|
| OFF | (none) | ca5b9331... | 241368e8... | ALL OK |
| O2 | `-DFORGE_NNUE_O2=1` | 1cd1e55a... (accumulator avx512) | d22e1ace... (accumulator avx2) | ALL OK |
| NOZERO | `-DFORGE_NOZERO_MOVE_BUFFERS=1` | 5bbf4944... | 05c59931... | ALL OK |
| SPEEDSTACK | `-DFORGE_SPEEDSTACK=1` | b8172950... | 368ee29e... | ALL OK |
| N2 | all three | 1823fe61... | faac168d... | ALL OK |

## M4: non-regression evidence for N2 (in progress)

### (c) uninitialised reads (the NOZERO risk)

- `-ftrivial-auto-var-init=pattern` and `=zero` builds of N2 znver5 (box recipe + the flag): 0 warnings, FMA 0,
  identity ALL OK (`logs/identity_n2_z5_init{pattern,zero}_b2983d07.log`). **But this is no NOZERO test on g++ 15:**
  the pattern build adds 10 memset-with-0xFE sites, none in the search bodies (`search_cuckoo_body` has 2862
  instructions in N2 and 2859 in N2+pattern; the 0xfefefefe immediates there are the bitboard file mask, present
  in both), i.e. GCC does not pattern-fill the `UninitArray` members of `MovePicker` (a class with a constructor).
  `logs/m4_autovarinit_codegen.log`.
- So I added a direct test hook (commit after b2983d07, `include/forge/board.hpp`): with
  `-DFORGE_R5B_POISON_MOVE_BUFFERS=<byte>` every `UninitArray` (the MoveList and MovePicker buffers under NOZERO)
  fills its storage with that byte when constructed. A read of an element that was never written then sees the
  pattern and would change the nodes or crash. Without the macro the hook does not exist: N2 rebuilt from the hook
  tree differs from the b2983d07 N2 exe in 4 bytes (PE timestamp).
- ASan/UBSan catch out-of-bounds and UB, not uninitialised reads; valgrind memcheck does. Both run in the new CI
  workflow `.github/workflows/opus-r5b-n2.yml` (asan job; `memcheck` job = `ci_n2_memcheck.sh`: valgrind memcheck of
  OFF (control) and N2 on bench 11, perft 4 and four depth-10 searches, plus the poison and pattern identities).

## M5: proposal (pending)

## What to gate first (pending)

## What I did not finish (pending)
