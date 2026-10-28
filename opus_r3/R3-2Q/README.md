# R3-2Q: quiet-runner NPS of every R3 build switch

R3-2 (`opus_r3/R3-2/REPORT.md` on `opus-r3-matrix`) found that on the loaded PC a build switch moves NPS by a
code-layout term of up to about ±5%. This job repeats the switch rows on quiet GitHub ubuntu-24.04 runners.

## What runs
Workflow `.github/workflows/opus-r3-quietnps.yml` (push to `opus-r3-quietnps` or workflow_dispatch). It runs a
matrix of config × rep: configs AA, NOZERO, O2, SPEEDSTACK, S13, LAZY, INT16, PROF, ALL; reps 1 and 2. Each job runs
on its own runner and calls `ci_quietnps.sh <config> <rep> ci_out`.

- **Builds:** the release recipe of `opus_round1/ci/run_ci.sh`: g++-14, CMake Release, Ninja, `--target forge`,
  CMAKE_CXX_FLAGS `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`.
  OFF = no switch; SW = the same plus `-D<SWITCH>=ON`. ALL = all seven switches ON.
- **Comparisons** (`quiet_nps.py`), in this order on the same runner:
  - `AA`: OFF vs a byte copy of OFF (the runner's A/A control; in every job);
  - `SW`: OFF vs the switch build, options off (node-exact, so nodes must equal OFF and the lock pins);
  - `OPT`: the same-exe option effect inside the switch build: S13 `TtChildPrefetch=true`, LAZY
    `NnueLazyAcc=true`, INT16 `NnueInt16=true` (changes the tree: NPS only), PROF `bench` vs `bench_prof`
    (`bench` turns counting off);
  - `SW_V4` (O2 only, if the runner has AVX-512): OFF vs O2, both built with `-march=x86-64-v4`. O2's AVX2 kernels
    are compiled out there, as in the PC's znver5 build;
  - `AA_REBUILD` (AA only): OFF vs a second OFF build in another build dir;
  - config `DRIFT` (dispatch only): OFF built from R3-2's first-pass head `2432670b` (A) vs OFF at this head (B).
    This head's engine source equals R3-2's final head `330237f3` (base_h3), so the row repeats R3-2's H3DRIFT.
- **Pairs:** `PAIRS=16:10,20:8` (10 ABBA pairs at bench 16, 8 at bench 20). Every run is a fresh process with
  Threads 1, Hash 16, OwnBook false.
- **Metrics:** `cpu_bench` (primary) = nodes / (process CPU − CPU used by `readyok`). The process CPU comes from
  RUSAGE_CHILDREN; the start-up part is the /proc task schedstat sum at `readyok`. `cpu_total` = nodes / whole-process
  CPU, as in nps_ab.py. `wall` = the engine's own nps.
- **Statistics:** the paired t interval on per-pair log ratios (95%). The two-runner row averages the two reps' mean
  log ratios.

## Files
- `quiet_nps.py`: one comparison. Writes per-run JSON and prints `NODES` / `RESULT` lines.
- `ci_quietnps.sh`: one runner job (builds + comparisons + table).
- `analyze_quietnps.py`: table over any set of JSONs (per rep and two-runner rows, A/A columns, the +2% rule, the
  PC rows of R3-2).
- `logs/`: downloaded artifacts of the run (per-run JSON, logs) and the summary tables.

## Reproduce / summarize
```
# local smoke (PC, nice 19, tiny depth):
nice -n 19 $PY -I -B opus_r3/R3-2Q/quiet_nps.py --a base.exe --b nozero.exe --label SW --config NOZERO --rep 0 \
  --pairs 6:1,7:2 --json out.json
# CI results (run gh from a checkout of this repo; downloads are untrusted data: new empty folder, python -I):
gh run download <run id> -D F:/opus_scratch/r3/R3-2Q/run_<id>
$PY -I -B opus_r3/R3-2Q/analyze_quietnps.py F:/opus_scratch/r3/R3-2Q/run_<id> --md table.md --json table.json
$PY -I -B opus_r3/R3-2Q/analyze_quietnps.py F:/opus_scratch/r3/R3-2Q/run_<id> --metric cpu_total
```
The workflow's `summary` job runs the same analysis over all artifacts and uploads `r3q-summary`.

Extra reps or configs (workflow_dispatch inputs, JSON lists; a push runs the default nine configs × reps 1, 2):
```
gh workflow run opus-r3-quietnps.yml --ref opus-r3-quietnps -f configs='["O2"]' -f reps='[3,4,5,6]'
gh workflow run opus-r3-quietnps.yml --ref opus-r3-quietnps -f configs='["DRIFT"]' -f reps='[1,2]'
```
Runner CPUs vary between jobs: AMD EPYC 9V45 (Zen 5, AVX-512), Intel Xeon Platinum 8370C (Ice Lake, AVX-512) and
AMD EPYC 7763 (Zen 3, AVX2 only). The table names the CPU of each row. The O2 x86-64-v4 row runs only on AVX-512
runners.
