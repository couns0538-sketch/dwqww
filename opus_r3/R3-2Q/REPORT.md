# R3-2Q Quiet-runner NPS of every R3 build switch (paired ABBA, CPU time, ≥ 2 runners per config) — DONE

Branch `opus-r3-quietnps` = opus-r3-stack `cae5e6bf` plus these commits:
- `43de4f66`: workflow + tools.
- `4f0ace56`: dispatch inputs, analyzer columns, docs, PC logs.
- `ba72d607`: DRIFT config.
- `f81b6bb7` and `8439f377`: evidence, `[skip ci]`.

Scope and limits:
- No engine, CMake or test change: `git diff cae5e6bf HEAD -- src include tests tools bench CMakeLists.txt` is empty.
- Every NPS figure comes from GitHub ubuntu-24.04 runners: 4-vCPU VMs, one job per VM. The PC only ran the smoke test (depth 6-11, nice 19).
- **Machine exclusive: no** (PC).
- No Elo claim, and no speed claim beyond the CIs below.

## Acceptance

| line | result | evidence |
|---|---|---|
| Workflow `opus-r3-quietnps.yml` | **DONE**. Trigger: push to `opus-r3-quietnps` only, plus workflow_dispatch (inputs `configs` / `reps`). Matrix config × rep, timeout 60 min. Raw per-run JSON and logs are uploaded; a Table step and a summary job print the table. Push run 40582060957: 18/18 jobs plus summary succeeded. | `.github/workflows/opus-r3-quietnps.yml`, `logs/ci_40582060957/` |
| Fresh processes; ≥ 8 ABBA pairs at d16, ≥ 6 at d20; nodes must match | **PASS**. 10 pairs at bench 16 and 8 at bench 20 in every comparison. Every OFF, switch and option run hits the lock pins (d16 3024920, d20 12389307). The exception is the NnueInt16=true side, whose tree changes (2760596 / 9564588), so that row is NPS only. 73 comparison files, 0 node-rule or exit failures. | `logs/ci_*/r3q-*/nps_*.json`, `logs/summary_cpu_bench.md` |
| CPU-time NPS with 95% CI (paired t on log ratios) | **DONE**. Primary metric: process CPU minus the CPU already used at `readyok` (37-64 ms of start-up removed). Whole-process CPU and wall-clock NPS agree with it within about 0.1 points. | `quiet_nps.py`, `logs/summary_{cpu_bench,cpu_total,wall}.md` |
| A/A in every job; ≥ 2 independent runners per config | **DONE**. Every job times OFF against a byte copy of OFF. 2 of 56 A/A intervals exclude 0 (about 2.8 expected at 95%). All 22 OFF builds are byte-identical (sha256 `644830f9…`), and a rebuild of OFF is byte-identical too. | table below |
| Same-exe option rows | **DONE**. TtChildPrefetch, NnueLazyAcc, NnueInt16 (the ON side printed "NnueInt16 active") and bench_prof (printed its 56 counter lines). | `nps_*_OPT.json` |
| Configs AA, NOZERO, O2, SPEEDSTACK, S13, LAZY, INT16, PROF, optional ALL | **DONE**. Runner counts: O2 6, NOZERO / LAZY / INT16 4 each, the others 2. | table |
| Optional x86-64-v4 O2 row | **DONE on one runner** (Xeon 8573C). The other 5 O2 jobs got AMD EPYC 7763 runners, which have no AVX-512. | `logs/ci_40583387872/r3q-O2-5/` |
| Extra: DRIFT (R3-2's H3DRIFT on quiet runners) | **DONE**, 2 runners. OFF at `2432670b` vs OFF at this head; this head's engine source equals R3-2's `330237f3`. | `logs/ci_40583751865/` |
| opus-ci on the push | **GREEN**: run 40582060873, release / ASan / TSan all succeeded. | gh |
| Local smoke test | **PASS**. `bash -n`, py_compile, and one-pair runs on R3-2's PC exes at nice 19, depth 6-11. NnueInt16 changes d11 nodes from 312866 to 330610; bench_prof prints its counters. | `logs/pc_smoke/` |

## Table

Columns: B vs A, cpu_bench NPS in %, with the 95% CI of the paired t on per-pair log ratios.
- Rule = 95% CI lower bound ≥ +2% at d16 AND d20.
- `*` = the runner has AVX-512.
- Row types:
  - SW = OFF vs switch build, options off.
  - OPT = same exe, option off vs on.
  - SW_V4 = both builds with -march=x86-64-v4.
  - DRIFT = OFF@2432670b vs OFF@HEAD.
- "all" = mean over the runners. The runners can have different CPUs, so it is not one machine's effect.
- Per-rep median and run-spread columns are in `logs/summary_cpu_bench.md`.

| config | row | rep | runner | nodes equal | d16 | d20 | A/A d16 | A/A d20 | rule |
|---|---|---|---|---|---|---|---|---|---|
| AA | AA | 1 | EPYC 9V45* | yes | +0.02 [-0.56, +0.60] | +0.38 [-2.13, +2.94] | - | - | n/a |
| AA | AA | 2 | EPYC 9V45* | yes | -0.45 [-2.18, +1.30] | -0.96 [-2.38, +0.48] | - | - | n/a |
| AA | AA | all | 2 runners | | **-0.22 [-1.11, +0.68]** | **-0.29 [-1.63, +1.06]** | - | - | n/a |
| AA | AA_REBUILD | all | 2 runners | | **-0.66 [-1.71, +0.40]** | **+1.01 [-1.11, +3.18]** | | | n/a |
| NOZERO | SW | 1 | Xeon 8370C* | yes | +1.93 [+1.70, +2.16] | +1.76 [+1.41, +2.10] | -0.03 [-0.79, +0.75] | -0.10 [-0.52, +0.33] | not met |
| NOZERO | SW | 2 | EPYC 7763 | yes | +1.78 [+0.96, +2.60] | +1.21 [+0.34, +2.09] | -0.20 [-0.88, +0.48] | -0.18 [-1.03, +0.67] | not met |
| NOZERO | SW | 3 | EPYC 7763 | yes | +1.22 [+0.76, +1.68] | +2.03 [+1.02, +3.05] | -0.21 [-0.83, +0.42] | +0.06 [-0.48, +0.61] | not met |
| NOZERO | SW | 4 | EPYC 7763 | yes | +1.33 [+0.63, +2.03] | +1.85 [+1.15, +2.55] | +0.03 [-0.81, +0.87] | +0.51 [-0.41, +1.43] | not met |
| NOZERO | SW | all | 4 runners | | **+1.56 [+1.29, +1.83]** | **+1.71 [+1.37, +2.05]** | -0.10 [-0.43, +0.23] | +0.07 [-0.24, +0.38] | not met |
| O2 | SW | 1 | EPYC 7763 | yes | +3.56 [+2.92, +4.20] | +3.52 [+2.61, +4.43] | +0.56 [-0.11, +1.23] | +0.42 [-0.34, +1.19] | MET |
| O2 | SW | 2 | EPYC 7763 | yes | +2.50 [+1.42, +3.59] | +2.34 [+1.68, +3.00] | -0.50 [-1.29, +0.30] | -0.19 [-1.88, +1.53] | not met |
| O2 | SW | 3 | EPYC 7763 | yes | +2.96 [+2.27, +3.66] | +2.80 [+2.23, +3.36] | -0.05 [-0.75, +0.66] | -0.22 [-0.78, +0.35] | MET |
| O2 | SW | 4 | EPYC 7763 | yes | +3.13 [+2.39, +3.88] | +3.45 [+2.42, +4.49] | -0.04 [-0.73, +0.64] | -0.30 [-0.99, +0.39] | MET |
| O2 | SW | 5 | Xeon 8573C* | yes | +3.27 [+2.62, +3.93] | +2.35 [+2.08, +2.62] | +0.14 [-0.50, +0.77] | -0.26 [-0.98, +0.46] | MET |
| O2 | SW | 6 | EPYC 7763 | yes | +3.36 [+2.61, +4.12] | +3.49 [+2.89, +4.08] | +0.52 [-0.28, +1.32] | +0.23 [-0.58, +1.05] | MET |
| O2 | SW | all | 6 runners | | **+3.13 [+2.85, +3.42]** | **+2.99 [+2.74, +3.24]** | +0.10 [-0.16, +0.36] | -0.05 [-0.40, +0.29] | MET |
| O2 | SW_V4 | 5 | Xeon 8573C* | yes | **+4.06 [+3.53, +4.59]** | **+3.95 [+3.10, +4.81]** | +0.14 [-0.50, +0.77] | -0.26 [-0.98, +0.46] | MET (1 runner) |
| SPEEDSTACK | SW | 1 | EPYC 9V45* | yes | +0.64 [+0.26, +1.03] | +1.03 [-1.48, +3.60] | -0.01 [-0.29, +0.27] | -0.02 [-0.36, +0.32] | not met |
| SPEEDSTACK | SW | 2 | EPYC 7763 | yes | +0.37 [-0.25, +0.99] | +1.08 [-0.41, +2.59] | -0.49 [-1.10, +0.14] | -0.82 [-1.87, +0.24] | not met |
| SPEEDSTACK | SW | all | 2 runners | | **+0.51 [+0.16, +0.85]** | **+1.06 [-0.30, +2.43]** | -0.25 [-0.57, +0.08] | -0.42 [-0.96, +0.12] | not met |
| S13 | SW | 1 | EPYC 7763 | yes | -0.09 [-1.12, +0.96] | +0.26 [-0.51, +1.03] | +1.21 [-0.20, +2.65] | -0.20 [-1.27, +0.88] | not met |
| S13 | SW | 2 | EPYC 7763 | yes | -0.16 [-0.59, +0.26] | -0.50 [-1.00, -0.01] | -0.37 [-1.17, +0.44] | +0.17 [-0.31, +0.64] | not met |
| S13 | SW | all | 2 runners | | **-0.13 [-0.66, +0.42]** | **-0.12 [-0.54, +0.30]** | +0.42 [-0.35, +1.19] | -0.02 [-0.57, +0.54] | not met |
| S13 | OPT TtChildPrefetch | all | 2 runners (both EPYC 7763) | yes | **+0.02 [-0.46, +0.49]** | **+0.23 [-0.52, +0.99]** | | | not met |
| LAZY | SW | 1 | EPYC 7763 | yes | -0.31 [-1.47, +0.86] | +0.21 [-0.86, +1.30] | -0.06 [-0.67, +0.55] | +0.25 [-0.50, +1.00] | not met |
| LAZY | SW | 2 | EPYC 7763 | yes | +0.31 [-0.34, +0.96] | +0.11 [-0.42, +0.64] | +0.52 [-0.26, +1.31] | +1.08 [+0.03, +2.15] | not met |
| LAZY | SW | 3 | EPYC 9V45* | yes | +1.96 [-0.83, +4.84] | -1.84 [-3.81, +0.17] | +0.30 [-0.59, +1.20] | +1.43 [-2.05, +5.05] | not met |
| LAZY | SW | 4 | Xeon 8370C* | yes | +0.19 [-0.03, +0.41] | +0.50 [+0.33, +0.67] | +0.04 [-0.30, +0.38] | +0.08 [-0.18, +0.35] | not met |
| LAZY | SW | all | 4 runners | | **+0.53 [-0.20, +1.28]** | **-0.26 [-0.80, +0.29]** | +0.20 [-0.11, +0.51] | +0.71 [-0.19, +1.61] | not met |
| LAZY | OPT NnueLazyAcc | all | 4 runners | yes | **+0.06 [-0.40, +0.53]** | **+0.29 [-0.34, +0.92]** | | | not met |
| INT16 | SW | 1 | EPYC 9V45* | yes | +1.41 [-2.99, +6.00] | +1.10 [+0.13, +2.08] | +1.39 [-1.52, +4.38] | +0.41 [-1.63, +2.48] | not met |
| INT16 | SW | 2 | EPYC 7763 | yes | -1.16 [-1.90, -0.41] | -0.90 [-1.94, +0.16] | -0.10 [-0.77, +0.56] | -0.16 [-1.02, +0.71] | not met |
| INT16 | SW | 3 | EPYC 9V74* | yes | -0.40 [-1.68, +0.89] | +0.03 [-1.30, +1.38] | +0.29 [-0.03, +0.61] | -0.12 [-1.54, +1.32] | not met |
| INT16 | SW | 4 | EPYC 9V74* | yes | -0.95 [-1.40, -0.50] | -0.66 [-1.01, -0.30] | -0.08 [-0.66, +0.51] | +0.06 [-0.88, +1.01] | not met |
| INT16 | SW | all | 4 runners | | **-0.28 [-1.41, +0.86]** | **-0.11 [-0.55, +0.33]** | +0.37 [-0.37, +1.12] | +0.05 [-0.57, +0.67] | not met |
| INT16 | OPT NnueInt16=true | all | 4 runners | **no: tree changes, NPS only** | **-7.73 [-8.36, -7.09]** | **-13.13 [-13.46, -12.80]** | | | not met |
| PROF | SW | 1 | EPYC 9V45* | yes | -1.68 [-2.66, -0.70] | -0.56 [-1.62, +0.52] | -0.16 [-0.82, +0.50] | +0.08 [-0.62, +0.78] | not met |
| PROF | SW | 2 | EPYC 7763 | yes | -1.47 [-2.72, -0.20] | -1.55 [-2.16, -0.94] | -0.11 [-0.67, +0.46] | -0.20 [-0.55, +0.16] | not met |
| PROF | SW | all | 2 runners | | **-1.58 [-2.32, -0.83]** | **-1.06 [-1.63, -0.48]** | -0.13 [-0.54, +0.27] | -0.06 [-0.42, +0.31] | not met |
| PROF | OPT bench_prof | all | 2 runners | yes | **-1.07 [-1.68, -0.45]** | **-1.17 [-1.57, -0.77]** | | | not met |
| ALL | SW | 1 | Xeon 8370C* | yes | +3.84 [+3.56, +4.11] | +3.80 [+3.57, +4.03] | +0.02 [-0.28, +0.31] | +0.13 [-0.00, +0.27] | MET |
| ALL | SW | 2 | EPYC 7763 | yes | +4.64 [+3.38, +5.91] | +2.50 [+1.24, +3.78] | -0.15 [-1.25, +0.97] | +0.35 [-0.38, +1.10] | not met |
| ALL | SW | all | 2 runners | | **+4.24 [+3.60, +4.88]** | **+3.15 [+2.51, +3.79]** | -0.06 [-0.62, +0.50] | +0.24 [-0.13, +0.62] | MET |
| DRIFT | SW | 1 | EPYC 7763 | yes | +0.13 [-0.76, +1.02] | -0.37 [-1.85, +1.13] | -0.21 [-0.76, +0.34] | -0.02 [-0.86, +0.83] | not met |
| DRIFT | SW | 2 | Xeon 6973P-C* | yes | -0.63 [-2.87, +1.65] | +0.43 [-2.57, +3.52] | +3.18 [+0.93, +5.47] | +1.23 [-0.12, +2.59] | not met |
| DRIFT | SW | all | 2 runners | | **-0.25 [-1.42, +0.93]** | **+0.03 [-1.55, +1.63]** | +1.47 [+0.34, +2.61] | +0.60 [-0.13, +1.34] | not met |

Per-rep OPT rows (S13, LAZY, INT16, PROF) are in `logs/summary_cpu_bench.md`.

## PC (R3-2) vs quiet runner: which effects reproduce

| switch | PC NPS Δ% | quiet runners, d16 / d20 | verdict |
|---|---|---|---|
| NOZERO | -4.16 [-4.60, -3.72], d20 -4.39 | +1.56 [+1.29, +1.83] / +1.71 [+1.37, +2.05] | **Not reproduced: layout of the PC exe.** On quiet runners the switch is a small real gain, as S14 found (+1.25..+2.70%). Rule not met (lower bounds +1.29 / +1.37). |
| O2, AVX2 kernels active (x86-64-v3) | n/a: the PC's znver5 build compiles the kernels out | +3.13 [+2.85, +3.42] / +2.99 [+2.74, +3.24] | **Feature.** Rule met in the all-runner row and on 5 of 6 runners alone. Applies to AVX2 builds, not to the PC lock recipe. |
| O2, x86-64-v4 (kernels compiled out, as on the PC) | +0.13 [-0.24, +0.51] at one head, +3.04 [+2.15, +3.94] at the other | +4.06 [+3.53, +4.59] / +3.95 [+3.10, +4.81] (1 runner, Xeon 8573C) | **Not "layout only":** without its AVX2 kernels, the O2 build was still about 4% faster on this AVX-512 runner. Likely cause, not isolated: O2's 64-byte Accumulator alignment, which matters once the compiler widens the portable loops to 512 bits. So the PC's +3.04% may be real and its +0.13% the layout-hit one. One Intel runner only. |
| SPEEDSTACK | +0.59 [+0.09, +1.08] | +0.51 [+0.16, +0.85] / +1.06 [-0.30, +2.43] | **Reproduced**: a small real gain. Rule not met. |
| S13 switch | -0.70 [-1.76, +0.37] | -0.13 / -0.12, CIs about ±0.5 | No effect in either place. |
| S13 TtChildPrefetch | -0.10 [-1.40, +1.22] | +0.02 / +0.23 | No effect in either place. |
| LAZY switch | +4.36 [+2.92, +5.81] | +0.53 [-0.20, +1.28] / -0.26 [-0.80, +0.29] | **Not reproduced: PC layout.** |
| LAZY NnueLazyAcc | -1.05 [-2.52, +0.44] | +0.06 / +0.29 | No effect in either place. |
| INT16 switch | +1.79 [+0.70, +2.89] | -0.28 [-1.41, +0.86] / -0.11 [-0.55, +0.33]; per runner from -1.16 to +1.41 | **Not reproduced.** The sign follows the runner, which is a layout signature. |
| INT16 NnueInt16 (tree changes: NPS only) | -8.78 [-9.88, -7.66] | -7.73 [-8.36, -7.09] / -13.13 [-13.46, -12.80] | **Reproduced**: the int16 path costs NPS. |
| PROF switch | -7.24 (vs base_h3) | -1.58 [-2.32, -0.83] / -1.06 [-1.63, -0.48] | **Partly reproduced.** A real cost of about 1-1.5% on Linux; the PC's extra ~6% fits S08fix's MinGW emulated-TLS finding (platform), possibly plus layout. |
| PROF counting (bench_prof) | -1.10 [-2.02, -0.17] | -1.07 [-1.68, -0.45] / -1.17 [-1.57, -0.77] | **Reproduced.** |
| ALL switches, options off | not measured on the PC | +4.24 [+3.60, +4.88] / +3.15 [+2.51, +3.79] | Roughly the sum of O2 (AVX2) + NOZERO + SPEEDSTACK − PROF. The rule is met in the all-runner row (not by rep 2 alone), but the gain rests on O2's AVX2 kernels, which the PC recipe does not build. |
| DRIFT: head vs first-pass head, OFF | H3DRIFT -4.61 [-5.20, -4.01] | -0.25 [-1.42, +0.93] / +0.03 [-1.55, +1.63] | **Not reproduced: PC layout.** |

## Findings
- **Features** (reproduce on quiet runners in sign and size):
  - SPEEDSTACK, about +0.5%;
  - PROF counting, about -1.1%;
  - the NnueInt16 option, -8 to -13% with a different tree;
  - O2's AVX2 kernels, about +3%;
  - the PROF build's cost on Linux, about -1 to -1.5%.
- **PC layout** (does not reproduce): NOZERO -4.2% (quiet: +1.6/+1.7%), LAZY switch +4.4% (quiet: about 0), INT16 switch +1.8% (quiet: about 0, sign varies by runner), and the -4.6% head drift (quiet: 0 ± 1.5).
- **nm on R3-2's PC exes supports the layout reading** (`logs/pc_layout_nm.log`).
  - The S13 exe is the only switch exe that keeps search, qsearch, TT probe, static_evaluate and nnue::update at the OFF addresses; only MovePicker::next moved. Its PC row is 0.
  - NOZERO moves these functions by -0x1c0 to -0x240, LAZY by +0x4c0, and INT16 by +0xf80.
  - base_h3 moved them by only -0x40 and ran 4.61% slower.
- **Speed-eligibility rule** (lower bound ≥ +2% at d16 and d20):
  - Met by:
    - O2 with its AVX2 kernels (all-runner lower bounds +2.85 / +2.74);
    - the single O2 v4 row (+3.53 / +3.10);
    - ALL, which contains O2.
  - Not met by every other switch or option. NOZERO is real but the rule is not met, as in S14.
- **The runner pool is mixed.** Seen: AMD EPYC 7763 (Zen 3, AVX2 only), EPYC 9V45 (Zen 5), EPYC 9V74 (Zen 4), and Xeon Platinum 8370C, 8573C and 6973P-C. So "two runners" often means two different CPUs, and the all-runner row is a mean over CPU types.
- **Some runners change speed mid-comparison.** EPYC 9V45 and Xeon 6973P-C runners shifted by up to 27% inside one comparison (logged as uptime 1-4 min at job start; the cause may be boot-time background work).
  - The spread column flags these runs. ABBA pairing absorbs most of the shift, but those rows have wide CIs.
  - The two A/A intervals that exclude 0 are LAZY-2 at d20 (+1.08) and DRIFT-2 at d16 (+3.18).

## UNVERIFIED / left
- **No Zen 5 coverage for the key rows.** No NOZERO, O2-v4 or DRIFT job landed on a Zen 5 runner (EPYC 9V45, the PC's core family). The only Zen 5 LAZY row (rep 3) is noisy. So "PC layout" vs "Zen 5-specific behaviour" is separated only by the cross-CPU consistency of the runner rows and by the nm evidence.
- **The O2 v4 row is one Intel runner.** Its cause (Accumulator alignment) is a hypothesis, not isolated.
- **The runners do not run the PC binaries.** They build with Linux g++-14; the PC exes (MinGW g++ 15.2, znver5) cannot run there. A runner row measures the same source, not the same binary.
- **The `defs [...]` field in `builds_*.log` is misleading.** It greps all of build.ninja, so the OFF builds list FORGE_DATAGEN, FORGE_DEBUG_HOOKS and FORGE_NNUE_INT16 from other targets. The forge target itself is OFF: identical OFF sha256 in every job, the lock pins hold, and every switch build differs from OFF.
- Every Linux build prints 34 compiler warnings (mostly -Wconversion), identical in OFF and switch builds. They predate this job.

## Files
- `quiet_nps.py`, `ci_quietnps.sh`, `analyze_quietnps.py`, `README.md`, `IDEA_SOURCE.md`.
- `logs/ci_40582060957/`, `ci_40583387872/`, `ci_40583577693/`, `ci_40583751865/`: raw per-run JSON, logs, runner_*.txt and build logs.
- `logs/summary_{cpu_bench,cpu_total,wall}.{md,json}`, `logs/pc_smoke/`, `logs/pc_layout_nm.log`.
- `FILES.txt` and `SHA256SUMS` (`sha256sum -c` OK).
