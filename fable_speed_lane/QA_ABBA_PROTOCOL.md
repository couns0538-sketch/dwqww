# Proposed quiet-ABBA protocol (for Engine QA)

A proposal only. QA owns the schedule, the run and the verdict. This job edited no queue, manifest, lock or gate file and started no ABBA for decision. Times are Europe/Vienna.

## Read this first: a fixed pair of exe files can mislead by several percent

Measured on this PC on 2026-11-10 under gate load (CPU 3, Idle priority; tables in `BENCH.md` section 3.1):

| When | Observation (CPU cycles) |
|---|---|
| 11:43 | `BUNDLE4` against the lock, one fixed file each: -3.65 % over 30 blocks, block ratios within a few tenths of a percent of each other |
| 11:57 | the five-bundle (the same four switches plus one) against the lock: +0.43 % over 30 blocks |
| 13:25 to 13:38 | `BUNDLE4` again, the same two files as at 11:43: -0.32 %, +0.44 %, +0.45 % (bench 16) and +0.30 % (bench 20) |
| 13:40 | lock against lock, two byte-identical copies made anew for each block: block ratios from -5.7 % to +6.1 % (12 blocks, SD 2.8 %; one file in all arms had given SD 0.9 % and 1.4 %). In three blocks the two copies were 3 to 6 % apart while two launches of each copy agreed within about 1 % |
| 13:51, 13:56 | a new copy for every arm: SD of block ratios 2.8 %; the same with every copy loaded at one fixed address: 2.5 %. The load address is not the cause |
| 14:04 | a new copy for every arm, 40 blocks: SD 1.4 %, median -0.02 %. The extra spread was gone |
| 14:17 | six copies, eight launches each in rotating order: no offset that belongs to a copy (SD between copies 0.26 %, p = 0.25) |
| 14:14 to 14:42 | `BUNDLE4` against the lock with a new copy for every arm, 100 blocks: -0.70 % |

So at times an exe file carried its own offset of several percent for many minutes, and a timing of two fixed files was then off by that much while looking tight; at other times there was no such offset. I could not establish the cause (physical placement of the file's pages is a candidate) and I measured only on the loaded machine. Whether it happens in a quiet gate gap is the open question, and it is cheap to answer:

1. **A/A between two copies.** Run the calibration with `-Cand <copy 1 of the lock>` and `-Baseline <copy 2 of the lock>`, each copy made just before the run, and repeat with new copies four or five times. If every repeat stays inside the adapter's tolerance (median 0.5 %, range 3 %), the quiet machine did not show the effect in that gap. `tools/file_effect.py` is the same check in one command (six copies, eight launches each, about three minutes on a free CPU).
2. **If the copies differ:** a single ABBA of two files is then the patch plus one draw per file. Either time several fresh copies of each exe (for example five copies each, one ABBA per pair, verdict on the median), or make a new copy for every letter. `tools/spd_uci.py abba --recopy <dir> --recopy-per arm --alternate` does the second and is what `BENCH.md` section 3.2 used.

The same question exists for gates, where both engines are fixed files for hours. I did not measure a gate and make no claim about one; an owner may want a lock-against-copy-of-lock gate as a check.

## What to time

| Order | Item | Switches (all default 0 in the patch) | Why this order |
|---|---|---|---|
| 0 | A/A calibration, between copies | two copies of the lock | the adapter's own tolerance check, and the check above |
| 1 | `BUNDLE3` | `FORGE_SPD_EVADE_LEGAL=1 FORGE_SPD_PAWN_CAPMASK=1 FORGE_SPD_CHECKERS_KL=1` | the bundle without the switch that timed slower under load. This job's own timing of it was stopped at 34 of 100 blocks: -0.22 % (interval -0.90 .. +0.47), so "within about 1 % of the lock" is all it says |
| 2 | `BUNDLE4` | the three above plus `FORGE_SPD_WITNESS_NOPIN=1` | under gate load it read -0.70 % (100 blocks) and `WITNESS_NOPIN` alone -1.02 % (60 blocks). A quiet machine may read it differently (README, "Why `WITNESS_NOPIN` can cost time"); if it does, that difference is itself worth knowing before a lock |
| 3 | `BUNDLE` (five) | the four plus `FORGE_SPD_KING_PAWN_CACHE=1` | only if the owner accepts `KING_PAWN_CACHE`, whose mechanism was built before (DUPCHECK.md) |
| 4 | singles | one switch each | only if a bundle result needs explaining; each single is expected inside timing noise |

No item of this job has a complete cold run of its own (the job was wrapped up at 16:56 with those runs in flight; `BENCH.md` section 2 gives the rows done, all equal to the lock's). Before an item is locked, its cold run should be completed: `STATUS.md` has the command.

Baseline for every run: the combo29 lock exe, sha256 `e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e`.

## Settings: QA's adapter, unchanged

`D:\forge_qa\quiet_abba_e4_c2_20261109\adapter\abba_combo29.ps1` as it stands:

| Setting | Value |
|---|---|
| Threads, CPU, priority | 1 thread, one logical CPU (`-LogicalCpu`), Idle |
| Options | `UseNNUE=true, Threads=1, Hash=16, OwnBook=false` |
| Per letter | fresh engine; warm `bench 13` (must give 862329); timed `bench 16` (must give 3024920) |
| Blocks | 10 x ABBA (`-Blocks 10`), ratio per block = sqrt(B1*B2 / (A1*A2)) |
| A/A tolerance | the adapter's: median 0.5 %, full range 3 % |
| Quiet check | the adapter's `quiet_one_core.py` before and after |

Because every candidate is node-identical, the adapter's node checks pass unchanged; a node mismatch would be a defect of the candidate and must stop the run.

```powershell
$A = 'D:\forge_qa\quiet_abba_e4_c2_20261109\adapter\abba_combo29.ps1'
$LOCK1 = '<copy 1 of the lock exe E1284F7F>'; $LOCK2 = '<copy 2 of the lock exe E1284F7F>'
powershell -NoProfile -ExecutionPolicy Bypass -File $A -Calibration -Cand $LOCK1 -Baseline $LOCK2 -Tag aa_<date> -OutputRoot <new folder>
powershell -NoProfile -ExecutionPolicy Bypass -File $A -Cand <BUNDLE3 exe> -Baseline $LOCK1 -Tag bundle3_<date> -OutputRoot <new folder>
```

## Which exe

Preferred: QA rebuilds from the pack with QA's own script, as for QUIET_FLAG v1.2 (`out\packs\<NAME>\BUILD_RECIPE.txt`):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\forge_qa\quiet_abba_e4_c2_20261109\c_t2_build_extradefs.ps1 `
  -Tag bundle3 -Src <unzipped pack source> -OutRoot <QA build folder> -Workload <frozen_train_cmds.txt> `
  -ExtraDefs '-DFORGE_SPD_EVADE_LEGAL=1','-DFORGE_SPD_PAWN_CAPMASK=1','-DFORGE_SPD_CHECKERS_KL=1'
```

Then the pins (bench d11/13/16/20/22 net on and net off, perft 5) on QA's exe before timing. This job's own switch-1 exes exist too (paths and hashes in `FILES.md` and each pack's `MD5SUMS.txt`); they were built with the lock's logged command lines on CPU 3 and pass the 12 pins, but they are not QA builds.

## What this job's own timing can and cannot say

`BENCH.md` section 3.2 holds the numbers to read: every arm from a new copy of its exe, bench 16, CPU cycles, with lock against lock as the null result next to each candidate. They were taken on one shared CPU at Idle priority under gate load and are **INDICATIVE**; they are not the ABBA. Section 3.3 holds the first timing step, which used one fixed file per exe; those rows are single draws of the per-file effect and should not be read as results.

`BENCH.md` section 5 gives exact counters instead of times: how much work each switch removes over the frozen workload (bench 11, 13, 16). Those are repeatable and say which switch does what; they do not say what it is worth in nodes per second.

## Things QA may want to know before the run

- `bench` builds its own 16 MB table for every call and clears it per position; the `Hash` option does not reach it. To time with another table size, use `go` (`tools/pos_cycles.py` does, position by position).
- One switch changes the PGO profile and ThinLTO layout of the whole exe. This is the reason to time the bundle as one exe.
- `KING_PAWN_CACHE` changes the pawn-cache entry from 40 to 64 bytes (one cache line per probe, 32,768 entries per worker as before, about 0.8 MiB more per thread).
- Net-off is not part of QA's adapter. `BENCH.md` reports net-off as information only.
- CPUs 4-6 of the Fable lane were not usable for this job: the running gate held the old mask (0xFF0) all day.
