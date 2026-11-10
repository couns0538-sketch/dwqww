# Proposed quiet-ABBA protocol (for Engine QA)

A proposal only. QA owns the schedule, the run and the verdict. This job edited no queue, manifest, lock or gate file and started no ABBA for decision. Times are Europe/Vienna.

## What to time

| Order | Item | Switches (all default 0 in the patch) | Why this order |
|---|---|---|---|
| 0 | A/A calibration | lock against itself (`-Calibration`) | the adapter's own tolerance check |
| 1 | `BUNDLE4` | `FORGE_SPD_WITNESS_NOPIN=1 FORGE_SPD_EVADE_LEGAL=1 FORGE_SPD_PAWN_CAPMASK=1 FORGE_SPD_CHECKERS_KL=1` | the four new candidates in one exe; the realistic lock candidate |
| 2 | `BUNDLE` (five) | the four above plus `FORGE_SPD_KING_PAWN_CACHE=1` | only if the owner accepts `KING_PAWN_CACHE`, whose mechanism was built before (DUPCHECK.md) |
| 3 | singles | one switch each | only if a bundle result needs explaining; each single is expected inside timing noise |

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
$LOCK = '<QA copy of the lock exe E1284F7F>'
powershell -NoProfile -ExecutionPolicy Bypass -File $A -Calibration -Cand $LOCK -Baseline $LOCK -Tag aa_<date> -OutputRoot <new folder>
powershell -NoProfile -ExecutionPolicy Bypass -File $A -Cand <BUNDLE4 exe> -Baseline $LOCK -Tag bundle4_<date> -OutputRoot <new folder>
```

## Which exe

Preferred: QA rebuilds from the pack with QA's own script, as for QUIET_FLAG v1.2 (`out\packs\<NAME>\BUILD_RECIPE.txt`):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\forge_qa\quiet_abba_e4_c2_20261109\c_t2_build_extradefs.ps1 `
  -Tag bundle4 -Src <unzipped pack source> -OutRoot <QA build folder> -Workload <frozen_train_cmds.txt> `
  -ExtraDefs '-DFORGE_SPD_WITNESS_NOPIN=1','-DFORGE_SPD_EVADE_LEGAL=1','-DFORGE_SPD_PAWN_CAPMASK=1','-DFORGE_SPD_CHECKERS_KL=1'
```

Then the pins (bench d11/13/16/20/22 net on and net off, perft 5) on QA's exe before timing. This job's own switch-1 exes exist too (paths and hashes in `FILES.md` and each pack's `MD5SUMS.txt`); they were built with the lock's logged command lines on CPU 3 and pass the 12 pins, but they are not QA builds.

## What this job's own timing can and cannot say

`BENCH.md` section 3 holds A/B numbers taken on CPU 3 at Idle while gates ran on the other cores. They are **INDICATIVE**: the lock timed against itself there gave block ratios from -5.6 % to +7.0 % by wall clock and from -2.0 % to +2.3 % by CPU cycles, so a gain under 1 % cannot be shown that way. They are given with their spread and with a CPU-cycle ratio next to the wall ratio. They are not the ABBA and should not be read as one.

`BENCH.md` section 5 gives exact counters instead of times: how much work each switch removes over the frozen workload (bench 11, 13, 16). Those are repeatable and say which switch does what; they do not say what it is worth in nodes per second.

## Things QA may want to know before the run

- One switch changes the PGO profile and ThinLTO layout of the whole exe. Per-exe layout effects of a few percent have been seen in this project; a single switch can therefore time below or above its true effect. This is the reason to time the bundle as one exe.
- `KING_PAWN_CACHE` changes the pawn-cache entry from 40 to 64 bytes (one cache line per probe, 32,768 entries per worker as before, about 0.8 MiB more per thread).
- Net-off is not part of QA's adapter. `BENCH.md` reports net-off as information only.
- CPUs 4-6 of the Fable lane were not usable for this job: the running gate held the old mask (0xFF0) until its queue restarts.
