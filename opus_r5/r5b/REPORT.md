# Forge Opus R5B: N2 speed build (O2 + NOZERO + SPEEDSTACK) — DONE

**Status:** DONE (all milestones M1-M5 and the final checks); last push: the head commit of `opus-r5b-speed` (times in the commit list below). Push cadence: every push within 10 min except one gap, 08:33 -> 08:48 Vienna (15 min, while I chased the CI failure).

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
| M1 (b2983d07) | forge_r5b_off_v3_m1fix.exe | v3 | 241368e8... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_v3_m1fix.log`) |
| M1 (b2983d07) | forge_r5b_off_z5_m1fix.exe | znver5 | ca5b9331... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_z5_m1fix.log`) |
| final (head 4129663d, after M2-M5) | forge_r5b_off_v3_final_4129663d.exe | v3 | 02480228... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_v3_final_4129663d.log`) |
| final (head 4129663d, after M2-M5) | forge_r5b_off_z5_final_4129663d.exe | znver5 | ea3a8778... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_z5_final_4129663d.log`) |

Between M1 and the end the only engine-source change is the test-only macro hook of 5c80ffe3 (M4), which does not
exist in an OFF or N2 build: the final OFF and N2 rebuilds differ from the M1 exes only at file offsets 137-138 and
217-219, the PE TimeDateStamp and CheckSum fields (`logs/final_checks_4129663d.log`). M2 (tools) and M3 (switch
builds of the same tree) change no engine source.

## M1: is O2 really on? (done)

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
| OFF exes unchanged | `forge_r5b_off_{v3,z5}_m1fix.exe` differ from the b7c1772 OFF exes in 4 bytes (PE timestamp/checksum fields) | `cmp -l`, EXES.txt |
| identity O2 znver5 (avx512 kernel) | ALL OK | `logs/identity_o2_z5_m1fix.log` |
| identity O2 v3 (avx2 kernel) | ALL OK | `logs/identity_o2_v3_m1fix.log` |
| kernel in the binary | O2 znver5 refresh: 8 `vaddps zmm` + 8 stores per block (register-blocked); update: explicit zmm kernels; FMA 0 | `logs/m1_kernel_audit_m1fix.log`, `logs/m1_nnue_disasm_m1fix.txt` |
| UCI line | O2 znver5: `info string nnue kernel: accumulator avx512, output avx2`; O2 v3: `accumulator avx2, output avx2`; OFF: no new line | manual `uci` |
| bit parity vs AL1 s198 (tests/nnue_parity_tests.cpp, box recipe, `tools/parity_r5b.sh`) | AVX-512 (znver5), AVX2 (v3) and FORCE_SCALAR (znver5) builds: PASS, same digest `f807d80cbabc1d59` over 1,303,743 positions (1,270,681 updates, 32,135 refreshes, 249,957 in-place, 8,267 castles, 100,000 synthetic evaluations) | `logs/m1_parity_o2_{z5_avx512,v3_avx2,z5_scalar}.log` |

Which O2 variant is faster on this PC is measured in M3 (arms `o2_portable` = b7c1772 O2 znver5 and
`o2_avx512` = the fix, both against the same OFF znver5 exe).

## M2: reproducible NPS bench (done)

`opus_r5/r5b/nps_ab.py` (+ `nps_ab.sh` wrapper; PowerShell: `& <venv python> -I -B opus_r5\r5b\nps_ab.py ...`),
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
- cooperative stop: `--stop-file` (checked before every run);
- `--copies K` (added after pass 1): every arm runs K byte copies of its exe in rotation; with K = pairs every slot
  runs fresh files, so per-file speed offsets (ASLR image base / page placement; seen as A/A failures of +2.55 and
  -2.76 % at d16 in passes 1-2) are sampled into the CI (pass 3: A/A back to about 1 %); with `--aa` every arm is
  also compared against the A/A arm (`cpu vs AA`, a second reference); `--names` are checked (unique, not A/AA).
Noise: live gates keep the PC 80-97 % busy (all CPUs, per-run GetSystemTimes); the A/A arm is the noise floor at
that moment. It cannot see code-layout effects of a different binary (same bytes), which R3-2Q found to dominate PC
switch rows (NOZERO -4.2 % on the PC vs +1.6 % on quiet runners); `tools/relink_layout.sh` builds a layout control
(same objects, other link order).
Known limit: the per-run timeout is soft (checked when a line arrives).

## M3: per-switch and combined builds (done)

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

### NPS pass 1 (08:12-08:27 Vienna; both recipes in parallel on cores 14 and 12, 12 pairs, one file per arm)

CPU-time NPS (primary) and engine NPS, B vs the OFF exe of the same recipe, % with 95 % CI; logs
`logs/m3_nps_{z5,v3}.log`, every run in `logs/m3_nps_{z5,v3}.json`.

| run | arm (B vs A) | cpu d16 % | cpu d20 % | engine d16 % | engine d20 % | median cpu ratio d16 / d20 | rule |
|---|---|---|---|---|---|---|---|
| m3_nps_z5.json (A = forge_r5b_off_z5_m1fix.exe, core 14, 12 pairs, PC busy 0.85) | o2_portable | +1.89 [+0.67, +3.12] | -0.15 [-0.78, +0.48] | +1.85 [+0.60, +3.12] | -0.14 [-0.86, +0.59] | 1.0217 / 0.9953 | not met |
|  | o2_avx512 | +0.91 [+0.03, +1.80] | -0.26 [-0.97, +0.46] | +0.88 [-0.01, +1.78] | -0.19 [-0.95, +0.58] | 1.0060 / 0.9986 | not met |
|  | nozero | +1.59 [+0.80, +2.39] | -0.14 [-0.78, +0.51] | +1.59 [+0.79, +2.40] | -0.02 [-0.73, +0.69] | 1.0152 / 0.9971 | not met |
|  | speedstack | +3.46 [+2.23, +4.70] | +1.21 [+0.63, +1.79] | +3.46 [+2.28, +4.65] | +1.29 [+0.61, +1.97] | 1.0326 / 1.0127 | not met |
|  | n2 | +4.94 [+3.55, +6.36] | +3.03 [+2.34, +3.72] | +4.96 [+3.59, +6.36] | +3.14 [+2.38, +3.92] | 1.0468 / 1.0304 | MET |
|  | AA | +2.55 [+1.27, +3.85] | +0.31 [-0.58, +1.21] | +2.54 [+1.23, +3.86] | +0.39 [-0.57, +1.37] | 1.0233 / 1.0043 | A/A control |
| m3_nps_v3.json (A = forge_r5b_off_v3_m1fix.exe, core 12, 12 pairs, PC busy 0.86) | o2_avx2 | +0.59 [+0.03, +1.16] | +0.21 [-0.25, +0.67] | +0.14 [-0.62, +0.91] | +0.19 [-0.45, +0.83] | 1.0085 / 1.0012 | not met |
|  | nozero | +0.69 [-0.39, +1.78] | +0.64 [-0.29, +1.59] | +0.60 [-0.54, +1.76] | +0.71 [-0.36, +1.79] | 1.0001 / 1.0089 | not met |
|  | speedstack | +0.25 [-0.67, +1.18] | +1.02 [+0.50, +1.55] | +0.10 [-0.95, +1.16] | +1.06 [+0.18, +1.95] | 1.0015 / 1.0089 | not met |
|  | n2 | +2.32 [+1.66, +2.99] | +2.02 [+1.36, +2.69] | +2.10 [+1.33, +2.89] | +2.12 [+1.35, +2.90] | 1.0209 / 1.0193 | not met |
|  | AA | -0.01 [-0.85, +0.85] | +0.12 [-0.52, +0.76] | -0.18 [-1.12, +0.77] | -0.01 [-0.90, +0.90] | 0.9983 / 1.0028 | A/A control |

Reading pass 1:
- **v3 run: the A/A control is clean** (-0.01 / +0.12 %). N2 +2.32 [+1.66, +2.99] / +2.02 [+1.36, +2.69]: a real gain
  that does **not** meet the +2 % lower-bound rule. The singles add up to about N2 (O2 +0.6 / +0.2, NOZERO +0.7 /
  +0.6, SPEEDSTACK +0.3 / +1.0). O2's AVX2 kernels give much less on this Zen 5 core than on the quiet CI runners
  (R3-2Q all-runner +3.1 / +3.0 %, mostly Zen 3 EPYC 7763).
- **znver5 run: the A/A control FAILED at d16** (+2.55 [+1.27, +3.85] for byte-identical files): the A exe ran about
  3 % slower than its copy in slots 0-7 and caught up from slot 8 (per-slot dump in this section's JSON); at d20 A/A
  is clean (+0.31). So every znver5 d16 row of pass 1 is biased by about +2.5 % and is not used. At d20: O2
  (either kernel) and NOZERO about 0, SPEEDSTACK +1.2, but N2 +3.03 [+2.34, +3.72], more than the sum of its parts:
  the signature of a code-layout effect (R3-2Q), not of the three switches.
- Likely cause of the A/A failure: the exes are `DYNAMIC_BASE` + `HIGH_ENTROPY_VA` (objdump -p), so every file gets
  its own ASLR image base; branch-predictor aliasing then differs per file, and an image re-mapped under the PC's
  RAM pressure can change speed mid-run. Not proven; the fix is to sample it: `nps_ab.py --copies K` runs K byte
  copies per arm in rotation (pass 2).

### NPS pass 2 (08:31-08:45 Vienna; znver5, core 14, 12 pairs, 3 byte copies per arm in rotation, smoke running)

| run | arm (B vs A) | cpu d16 % | cpu d20 % | engine d16 % | engine d20 % | median cpu ratio d16 / d20 | rule |
|---|---|---|---|---|---|---|---|
| m3_nps_z5_r2.json (A = forge_r5b_off_z5_m1fix.exe, core 14, 12 pairs, PC busy 0.92) | o2_portable | -0.32 [-1.05, +0.41] | +0.19 [-0.39, +0.77] | -0.31 [-1.07, +0.46] | +0.17 [-0.56, +0.91] | 0.9946 / 0.9999 | not met |
|  | o2_avx512 | -0.22 [-0.99, +0.55] | -0.09 [-0.77, +0.59] | -0.02 [-0.78, +0.74] | -0.08 [-0.74, +0.58] | 1.0000 / 0.9990 | not met |
|  | nozero | +1.01 [-0.24, +2.28] | +0.90 [+0.16, +1.65] | +1.17 [-0.18, +2.53] | +0.84 [-0.07, +1.77] | 1.0159 / 1.0121 | not met |
|  | speedstack | +1.09 [+0.04, +2.15] | +0.87 [+0.10, +1.64] | +1.19 [-0.01, +2.41] | +0.95 [+0.05, +1.85] | 1.0098 / 1.0094 | not met |
|  | n2 | +1.74 [+0.29, +3.21] | +2.43 [+1.91, +2.97] | +1.86 [+0.34, +3.39] | +2.49 [+1.85, +3.14] | 1.0203 / 1.0245 | not met |
|  | AA | -2.76 [-4.72, -0.75] | -0.81 [-1.88, +0.27] | -2.73 [-4.81, -0.59] | -0.75 [-1.82, +0.32] | 0.9776 / 0.9965 | A/A control |

(`cpu vs AA` second-reference rows are in `logs/m3_nps_z5_r2.log`.)
- **The A/A control failed at d16 again, with the opposite sign: -2.76 [-4.72, -0.75]** (pass 1: +2.55). So the
  per-file offset is random (about +-2.5 % at d16), not a bias towards A or AA. With 3 copies, the 12 pairs share
  only 3 file pairings (pseudo-replication), so the interval is too narrow. Pass 3 uses a fresh copy for every slot
  (`--copies` = `--pairs`), so every pair carries independent file effects and the t interval includes them.
- With A as reference, O2 (portable or avx512) is about 0 at both depths, NOZERO +1.0 / +0.9, SPEEDSTACK +1.1 / +0.9,
  N2 +1.74 [+0.29, +3.21] / +2.43 [+1.91, +2.97]: rule not met. Against AA as reference every arm reads 1-3 % higher
  (the same arms, another reference file): the reference file alone moves every row by the A/A offset.

### NPS pass 3 (08:46-09:00 Vienna; znver5, core 14, 20 pairs, a fresh byte copy of every arm in every slot)

Arms: N2, `off_relink` (the OFF objects re-linked in reverse unit order: identical code, other addresses and 64-byte
alignment of the hot functions, e.g. `nnue::update` 0x...1a1c0 -> 0x...31c60; identity ALL OK; `tools/relink_layout.sh`),
and AA. `--copies 20 --pairs 20`: no two slots share a file, so the per-file offsets are independent per pair.

| run | arm (B vs A) | cpu d16 % | cpu d20 % | engine d16 % | engine d20 % | median cpu ratio d16 / d20 | rule |
|---|---|---|---|---|---|---|---|
| m3_nps_z5_r3.json (A = forge_r5b_off_z5_m1fix.exe, core 14, 20 pairs, PC busy 0.91) | n2 | +2.05 [+1.30, +2.80] | +1.91 [+1.47, +2.36] | +2.01 [+1.18, +2.85] | +1.81 [+1.33, +2.29] | 1.0200 / 1.0208 | not met |
|  | off_relink | -0.80 [-1.96, +0.37] | -0.14 [-0.82, +0.54] | -0.81 [-1.96, +0.36] | -0.19 [-0.93, +0.55] | 0.9978 / 1.0001 | not met |
|  | AA | -0.67 [-1.98, +0.65] | -0.89 [-1.73, -0.03] | -0.82 [-2.23, +0.60] | -0.93 [-1.79, -0.07] | 0.9918 / 0.9917 | A/A control |

- **A/A is back near zero** (-0.67 [-1.98, +0.65] / -0.89 [-1.73, -0.03]: about 1 % floor, d20 just excludes 0).
- **Layout control: re-linking OFF moves NPS by -0.80 [-1.96, +0.37] / -0.14 [-0.82, +0.54]**, i.e. inside the floor
  for this one alternative layout (one sample of the layout distribution, not its spread).
- **N2 znver5: +2.05 [+1.30, +2.80] at d16, +1.91 [+1.47, +2.36] at d20: a real gain of about 2 %, rule NOT met**
  (lower bounds +1.30 / +1.47 < +2). This agrees with the v3 pass 1 (N2 +2.32 [+1.66, +2.99] / +2.02 [+1.36, +2.69]);
  pass 1-2's larger znver5 N2 values (d20 +3.03, +2.43) carried per-file offsets.

### Quiet runners (GitHub, the CI method; run 40837780229, dispatched 08:48 Vienna on 3da5dbc7)

`opus_r3/R3-2Q/ci_quietnps.sh` got an `N2` config (R5B): per runner, g++-14 CMake Release with the box flags
(x86-64-v3), OFF vs N2 (and OFF vs a byte copy, A/A), paired ABBA CPU-time NPS, 10 pairs at d16 and 8 at d20; on an
AVX-512 runner also OFF_v4 vs N2_v4 built with -march=x86-64-v4 (the O2 512-bit kernels). 6 reps; logs and per-run
JSON in `logs/quietnps/`, pooled with `opus_r3/R3-2Q/analyze_quietnps.py`:

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N2 | SW | 1 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +5.27 [+4.45, +6.10] | +4.57 [+3.68, +5.46] | -0.40 [-1.21, +0.40] | -0.39 [-0.90, +0.13] | MET | +5.12 / +4.87 | 2.8 / 3.0 |  |
| N2 | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +5.56 [+4.76, +6.36] | +5.44 [+4.47, +6.43] | +0.05 [-0.66, +0.77] | -0.01 [-0.84, +0.83] | MET | +5.44 / +4.95 | 3.9 / 4.7 |  |
| N2 | SW | 3 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +5.91 [+4.84, +6.99] | +6.32 [+4.39, +8.28] | +0.34 [-0.93, +1.64] | +0.80 [-0.15, +1.75] | MET | +6.22 / +6.22 | 6.5 / 8.4 |  |
| N2 | SW | 4 | INTEL(R) XEON(R) PLATINUM 8573C (AVX-512) | d16 yes; d20 yes | +5.93 [+4.60, +7.27] | +5.91 [+5.13, +6.70] | -0.27 [-1.25, +0.72] | +0.06 [-0.70, +0.83] | MET | +5.86 / +6.24 | 4.5 / 3.0 |  |
| N2 | SW | 5 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +0.28 [-4.72, +5.54] | +1.68 [+0.31, +3.06] | +0.17 [-3.54, +4.01] | +0.73 [-0.63, +2.11] | not met | +2.69 / +1.80 | 28.1 / 11.7 |  |
| N2 | SW | 6 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +5.71 [+4.89, +6.54] | +5.19 [+4.31, +6.09] | +0.15 [-0.47, +0.78] | -0.16 [-0.69, +0.38] | MET | +5.70 / +5.31 | 3.1 / 4.8 |  |
| N2 | SW | all (6) | 6 runners | | **+4.76 [+3.83, +5.69]** | **+4.84 [+4.41, +5.27]** | +0.01 [-0.66, +0.68] | +0.17 [-0.14, +0.48] | MET | | | |
| N2 | SW_V4 | 4 | INTEL(R) XEON(R) PLATINUM 8573C (AVX-512) | d16 yes; d20 yes | +5.94 [+5.07, +6.81] | +6.03 [+5.62, +6.43] | -0.27 [-1.25, +0.72] | +0.06 [-0.70, +0.83] | MET | +6.24 / +5.97 | 2.4 / 3.9 |  |
| N2 | SW_V4 | 5 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +3.80 [+2.40, +5.23] | +4.79 [+1.64, +8.02] | +0.17 [-3.54, +4.01] | +0.73 [-0.63, +2.11] | not met | +3.92 / +4.02 | 6.2 / 10.3 |  |
| N2 | SW_V4 | all (2) | 2 runners | | **+4.86 [+4.08, +5.65]** | **+5.40 [+3.81, +7.02]** | -0.05 [-1.94, +1.88] | +0.39 [-0.33, +1.12] | MET | | | |

- **Pooled over 6 runners N2 = +4.76 [+3.83, +5.69] at d16 and +4.84 [+4.41, +5.27] at d20: rule MET** (A/A
  +0.01 / +0.17). On the Zen 3 (EPYC 7763) and Intel runners every rep alone meets it (+4.6 to +6.3 %).
- **Zen 5 is the exception:** the one EPYC 9V45 runner (the PC's core family; noisy, spread 28 % at d16) gives
  +0.28 / +1.68 for the x86-64-v3 build, and +3.80 [+2.40, +5.23] / +4.79 [+1.64, +8.02] for the x86-64-v4 build
  (512-bit kernels). The PC (Zen 5 Ryzen 7 9850X3D) measured about +2 % (passes 1 and 3).
- So N2 is a real, larger-than-the-singles speed-up wherever it was measured; it clears the +2 % lower-bound rule on
  the quiet runners (the rule's proxy, forge-engine-verify) and does not clear it on the loaded Zen 5 PC.

## CI (GitHub Actions)

| run | workflow | commit | result | note |
|---|---|---|---|---|
| 40833411141 | opus-ci (default config) | b2983d07 | attempt 1: release OK, **asan FAILED**, tsan OK; **attempt 2 (re-run of the failed job): success** | `forge_tt_mate_tb_tests`: "Threads 2, search 1 on the shared TT: a real mate, never shorter than mate in 3 (466 e8e4)" (EPYC 9V74 runner) |
| 40834623805 | opus-ci | 519d6531 | attempt 1: **release FAILED** (same test, "(442 e8e4)", EPYC 7763 runner); **attempt 2: success** | same flake |
| 40834623964 | opus-r5b-n2 | 519d6531 | success (N2 release / asan / tsan, memcheck) | first version of the workflow |
| 40834819014 | opus-r5b-n2 | f99966f7 | success (N2 release / asan / tsan, singles release, N2 v4 release + asan, memcheck) | |
| 40835194501 | opus-r5b-n2 | 5c80ffe3 | success (incl. memcheck with the poison identities) | |
| 40835194560 | opus-ci | 5c80ffe3 | success | |
| 40834819007 | opus-ci | f99966f7 | success | |
| 40837780229 | opus-r3-quietnps (dispatch, configs ["N2"], reps 1-6) | 3da5dbc7 | success | quiet-runner N2 NPS (v3, and v4 on AVX-512 runners) |

The red opus-ci jobs are a nondeterministic two-thread test, not this job's code: the opus-ci default
configuration builds none of the R5B code (every engine change is under `#if FORGE_NNUE_O2` or the test-only poison
macro; the OFF exes differ from b7c1772 only in the PE timestamp/checksum fields), the same check failed in a release job and in an
asan job on two different CPU types, and it passed in the other jobs of the same commits. The search behind it (a
two-thread search on a shared TT not finding the mate in 3) is the SmpV2 mate area that Astra owns (rule 9), so I
neither edit nor weaken it; the failed jobs were re-run (attempts 2) and the base-tree rate is measured on the PC
below. Owner/Astra item: `tests/tt_mate_tb_tests.cpp` Threads 2 check is flaky on CI runners.

Final state of the run list: every run of every workflow on the branch is green (two opus-ci runs after one re-run
of the failed job each). The last commit that changes anything a workflow builds is 5c80ffe3 (opus-ci and
opus-r5b-n2 green); later commits change reports, job tools and `opus_r3/R3-2Q/ci_quietnps.sh` (used only by the
dispatched quietnps run, green) and carry `[skip ci]`.

Base-tree evidence (`tools/flake_tt_mate.sh`, `logs/ci_flake_tt_mate_tb.log`, 08:56-08:57 Vienna): the test built
the same way from a `git archive` of b7c1772 and from this branch's head (box flags, -O3, static), 40 runs each with
its CTest argument `tests/syzygy_reference.tsv`: **base 1 of 40 failed, with the same message** ("Threads 2, search 1
on the shared TT: a real mate, never shorter than mate in 3 (455 e8e4)"); head 0 of 40. So the flake predates R5B;
on 4-vCPU CI runners it shows more often (2 of the first 6 opus-ci jobs here).

## M4: non-regression evidence for N2 (done)

### (a) node-exact proof with real searches

`m4_nodeexact.py`: one process per exe, the same command sequence (`ucinewgame`, `position fen`, `go depth 18`) on 50
positions taken evenly from `tests/data/nnue_selfplay_sample_916.txt`; N2 znver5 (`forge_r5b_n2_z5_b2983d07.exe`) vs
OFF znver5 (`forge_r5b_off_z5_m1fix.exe`): **50/50 positions identical** in bestmove, node count, score and pv at
depth 18 (64,772,376 nodes in total). Lists: `logs/m4a/nodeexact_n2_z5_{A,B}.tsv`, log `logs/m4a_nodeexact_n2_z5.log`.

### (b) 200-game crash / legality smoke

`smoke_ab.py` (R5A smoke.py + `--exe-off`), N2 znver5 vs OFF znver5, 5+0.05, Threads 1, Hash 16, OwnBook false,
openings from 8moves_v3.pgn (seed 1, each played with both colours), 2 games at once pinned to CPUs 0-11 (the NPS
run had core 14), 08:31-08:54 Vienna: **PASS: 200/200 games, 0 illegal, 0 crashes, 0 time losses, 0 missing
bestmoves, 0 error lines, 0 engine restarts, 0 near-flags (< 20 ms), go/stop stress 50/50 with 0 problems.** Average
131.2 plies; terminations: threefold 132, mate 58, insufficient material 9, fifty moves 1 (two node-exact engines
repeat a lot). N2 scored 98/200 (not a strength measurement). `logs/m4b_smoke_n2_z5.log`,
`logs/m4b_smoke_n2_z5_summary.json`, games.pgn sha256 in `logs/m4b_smoke_n2_z5_games.sha256` (pgn in
`F:\opus_scratch\r5\r5b\smoke\n2_z5\`).

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
  tree differs from the b2983d07 N2 exe in 4 bytes (PE timestamp/checksum fields).
- **Poisoned N2 (znver5, box recipe): `-DFORGE_R5B_POISON_MOVE_BUFFERS=0xFE` and `=0x5A`: 0 warnings, FMA 0,
  identity ALL OK** (bench d11-d22 + perft startpos/kiwipete; perft walks MoveList, the bench search MovePicker and
  MoveList). `logs/identity_n2_z5_poison0x{FE,5A}.log`, `logs/build_n2_z5_poison0x{FE,5A}.log`.
- ASan/UBSan catch out-of-bounds and UB, not uninitialised reads; valgrind memcheck does. Both run in the new CI
  workflow `.github/workflows/opus-r5b-n2.yml` (asan job; `memcheck` job = `ci_n2_memcheck.sh`: valgrind memcheck of
  OFF (control) and N2 on bench 11, perft 4 and four depth-10 searches, plus the poison and pattern identities).
- **CI results** (artifacts of run 40835194501, checked, not only the job status): valgrind memcheck
  `ERROR SUMMARY: 0 errors from 0 contexts` for OFF and for N2; on Linux too the N2 poison identities (0xFE, 0x5A)
  and the pattern identity are ALL OK; N2 release / ASan+UBSan / TSan CTest with the known-failure check: PASS (only
  the 4 known forge_tests lines; no sanitizer report). N2 built with -march=x86-64-v4 (the 512-bit kernels): release
  on an AVX-512 runner, identity ALL OK and KNOWN-FAILURE CHECK PASS (run 40835194501); ASan+UBSan on an AVX-512
  runner PASS with no sanitizer report (run 40834819014; the later run's v4 ASan job drew a runner without AVX-512
  and skipped with a notice).
- **Local CTest of N2 with the PC toolchain** (MinGW g++ 15.2, `-march=znver5`, CMake Release with the three switches,
  all targets, 62 compiler warnings, all in `src/search/{alphabeta,qsearch,tt_lockless}.inc`, none in a file R5B
  touched; `logs/cmake_n2_z5.build.log`): **54/54 tests passed** on a 3-CPU mask at BelowNormal
  (`tools/run_ctest_3cpu.cmd`, `logs/ctest_n2_z5.log`; forge_tests excluded as in R5A because two of its checks
  search with 4 threads; CI runs it). The CMake-built parity test reports `AVX-512 (O2 512-bit accumulator kernels,
  R5B; AVX2 output layer)`, digest `f807d80cbabc1d59`, PASS.

## Final checks (09:03-09:05 Vienna, head 4129663d; `tools/final_checks.sh`, `logs/final_checks_4129663d.log`)

| exe rebuilt from the head | compared with | differing bytes (file offsets) | identity | FMA | warnings |
|---|---|---|---|---|---|
| forge_r5b_off_z5_final_4129663d.exe | forge_r5b_off_z5_m1fix.exe | 4 (137-138, 217-218) | ALL OK | 0 | 0 |
| forge_r5b_off_v3_final_4129663d.exe | forge_r5b_off_v3_m1fix.exe | 5 (137-138, 217-219) | ALL OK | 0 | 0 |
| forge_r5b_n2_z5_final_4129663d.exe | forge_r5b_n2_z5_b2983d07.exe (the candidate) | 5 (137-138, 217-219) | ALL OK | 0 | 0 |
| forge_r5b_n2_v3_final_4129663d.exe | forge_r5b_n2_v3_b2983d07.exe | 4 (137-138, 217-218) | ALL OK | 0 | 0 |

Offsets 137-138 and 217-219 are the PE TimeDateStamp and CheckSum fields: the head builds the same code as the
proposal's exes. UCI kernel lines of the rebuilt N2 exes: znver5 `accumulator avx512, output avx2`, v3 `accumulator
avx2, output avx2`. The M1-fix OFF exes also passed the lock identity here (the "M1" rows of the rule-7 table).

## M5: proposal (done)

`N2_PROPOSAL.md` (and the same gate as data in `n2_gate_spec.json`): candidate `forge_r5b_n2_z5_b2983d07.exe`
(sha256 1823fe61...) vs `forge_r5b_off_z5_m1fix.exe` (ca5b9331...), both the PC lock recipe; identity table; the O2
fix spelled out; NPS with CI and the A/A floor (PC about +2 %, rule not met; quiet runners +4.8 %, rule met);
non-regression SPRT [-10, 0] nElo normalized, alpha = beta = 0.05, 10+0.1, cap_games 3000, srand / openings start
blank. Optional extra speed idea: not done (see below).

## What to gate first

1. **R5B-N2** (`N2_PROPOSAL.md`, `n2_gate_spec.json`): N2 znver5 vs OFF znver5, non-regression SPRT [-10, 0] nElo,
   10+0.1, cap 3000, srand / openings start blank. Node-exact, about +2 % CPU-time NPS on this PC and +4.8 % on quiet
   runners; the gate checks that the faster binary is not weaker. If the queue prefers the job-spec flags, gate the
   v3 pair instead (same evidence; both pairs pass identity).
2. Nothing else from R5B needs a gate: the singles are inside N2, and on this PC O2 alone is about 0 and NOZERO /
   SPEEDSTACK about +1 % each (rule not met).

## What I did not finish

- Optional M5 speed idea: not done. Candidate for a later job: a 512-bit output layer in `nnue::evaluate` (one zmm of
  16 lanes is exactly the existing lane assignment `index % 16`, so it is bit-exact by construction); it needs a
  profile and a quiet-runner A/B, because the PC's floor (about 1 %) cannot show a sub-percent gain.
- The +2 % rule was never met on the PC; a measurement on an idle PC was not possible (machine not exclusive).
- The cause of the per-file A/A offsets (ASLR image base or physical page placement) is not isolated; the
  fresh-copy design only samples it. The layout control is one relink sample, not a layout distribution.
- Local (PC toolchain) CMake + CTest only for N2 znver5; OFF and the three singles got CTest on Linux CI only (release
  + known-failure check, green). ASan/TSan are Linux-only (MinGW has no ASan).
- O2's 512-bit kernel is proven bit-exact and present in the binary, but on this PC it is not measurably faster than
  the portable loops it replaced (passes 1-2: both about 0 vs OFF at d20).
- `tests/tt_mate_tb_tests.cpp` Threads 2 flake: pre-existing (base 1/40 on the PC), owner/Astra item; not touched.
- One push gap of 15 min (08:33 -> 08:48 Vienna).

## Owner items

- Install the gate pair (`forge_r5b_n2.exe`, `forge_r5b_off.exe` from `F:\opus_scratch\r5\r5b\exe\`, sha256 in
  `EXES.txt`), fill srand and openings start, queue R5B-N2.
- Astra / owner: the `forge_tt_mate_tb_tests` Threads 2 check fails on CI runners now and then (2 of the first 6
  opus-ci jobs here, base 1/40 on the PC); a re-run of the failed job turned both runs green.
- Merge decision: the M1 fix (commit b2983d07) and the test hook (5c80ffe3) are engine changes for
  `forge-bundle-int`; `opus-r3-switches` (every switch at once) only runs there.
- Recipe decision for later bundles: znver5 (PC lock exe) or v3 (job spec); R5A used v3, this proposal uses znver5.

## Time and machine (measured)

- Commits: 18 from 07:58 to 09:03 Vienna (first 46b8a57e, M1 fix b2983d07 at 08:07, last 4129663d), plus the final
  report commits; job start 07:53 Vienna, so about 1 h 20 min of the 3 h cap were used. The depth not bought by the
  shorter time: no extra speed idea, one layout sample, no local CTest of the singles.
- Temperatures (HWiNFO via `tools/cpu_temp.sh`, rule sensor taken as "CPU IOD Hotspot" as in R5A): 49.2-50.5 C at
  every check (07:56, 08:05, 08:13, 08:34); Tctl/Tdie 80.8-83.0 C (80.9 C before my first build, from the PC's own
  gate and training load). Threads: at most 3 of mine at any time (builds JOBS <= 3 alone; NPS 1 + smoke 2;
  CTest on a 3-CPU mask). BelowNormal throughout; no process killed, nothing deleted, nothing written to E:, gates,
  queue, manifest, forge_push and training untouched.
