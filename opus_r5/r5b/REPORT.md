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
| 00 baseline | forge_r5b_off_z5_b7c1772.exe | znver5 | 88e15c7d... | (running) | | | 0 | |

## M1: is O2 really on? (in progress)

## M2: reproducible NPS bench (pending)

## M3: per-switch and combined builds (pending)

## M4: non-regression evidence for N2 (pending)

## M5: proposal (pending)

## What to gate first (pending)

## What I did not finish (pending)
