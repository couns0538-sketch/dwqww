# R3-1L: Linux double-check of the R3-1 self-play acceptance (GitHub ubuntu-24.04, no PC CPU)

Acceptance (user): "each option ON alone and all ON together: no crash, no illegal move, no double bestmove over
500 fast self-games with illegal-move checker". The PC run is `opus_r3/R3-1_selfplay` (branch opus-r3-selfplay);
this job runs the same checker, the same 36 configs (`configs_final.json`, unchanged) and the same nets on quiet
GitHub runners, with CMake/g++-14 builds instead of the PC's static ucrt64 g++ 15.2 builds, plus sanitizer runs.

## Files
| file | what |
|---|---|
| `../../.github/workflows/opus-r3-sp-linux.yml` | the workflow: `plan` (job matrix from jobs.json, Syzygy download + cache) -> `selfplay` (one job per entry of jobs.json) -> `summary` (table of every job) |
| `jobs.json` | the job plan: 29 jobs = 36 release configs x 500 games (SMP configs one per job, the others two per job), all_on on ASan+UBSan (2 x 250 games, seeds 1 and 2), the 6 Threads=2 configs on TSan (100 games each); plus 6 `fin-*` jobs = the 4 final-head configs of `configs_final_head.json` x 500 games and its 2 Threads=2 configs on TSan (100 games). `push_jobs` = the jobs a push runs (now `["fin-*"]`; `["all"]` = every job) |
| `select_jobs.py` | picks the jobs of a run: `push` (= push_jobs), `all`, or ids / id prefixes with `*` (workflow_dispatch input `jobs`) |
| `configs_final_head.json` | the 4 configs that need the final stack head 34ef8a70 (engine 064af732): all_on_final (all_on + SmpHelpersPastDepth), smp_helpers_past_depth (Threads 2), spsa_plus10 / spsa_minus10 (the 20 SPSA spins at about +-10%); same format and budgets as configs_final.json |
| `collect.sh` | on the PC: downloads the finished jobs' artifacts of a run, rebuilds the table, copies the small evidence into `logs/run_<id>/` |
| `run_job.sh` | one job: CMake build of every exe its configs need (`--target forge`), identity check, nets, `run_matrix.py`, sanitizer-report check, per-job table |
| `job_configs.py` | writes the job's configs file (subset of configs_final.json, only the Syzygy path changed) and prints the exe keys |
| `summarize.py` | the table (`--single <job dir>` per job, `--jobs jobs.json --arts <artifacts>` for the whole run) with the pass rule |
| `get_syzygy.sh`, `syzygy345.sha256` | 3-4-5 Syzygy tables (145 WDL + 145 DTZ) from the lichess mirror (fallback sesse.net), every file checked against the sha256 of the PC copy |
| `nets/o4_material_epoch004-step000000780.fnn2` | copy of O4's material-trained stand-alone smoke net (the PC's PureNnue net), 394922 bytes, sha256 `70f915879d35c4bd06591d775d71e02cd73e5f8c3da4844c861a82f8796a982f`, fnv1a 1544ea643b9cd9a7 |
| `logs/` | smoke test of the invocation on the PC, run ids, the summary table of each run |

## Builds (run_job.sh; recipe of opus_round1/ci/run_ci.sh)
- release: `cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++-14
  -DCMAKE_CXX_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
  [-D<SWITCH>=ON]`, `cmake --build --target forge`; FMA count must be 0.
- asan: RelWithDebInfo, `-DFORGE_ENABLE_SANITIZERS=ON`, flags + `-fno-sanitize-recover=all`;
  `ASAN_OPTIONS=log_path=...:detect_leaks=1:abort_on_error=1`, `UBSAN_OPTIONS=log_path=...:print_stacktrace=1:halt_on_error=1`.
- tsan: RelWithDebInfo, flags + `-fsanitize=thread -fno-omit-frame-pointer`, linker `-fsanitize=thread`;
  `TSAN_OPTIONS=log_path=...:halt_on_error=1:second_deadlock_stack=1`.
- exe keys (build_engines.sh names): base, o2 (FORGE_NNUE_O2), nozero (FORGE_NOZERO_MOVE_BUFFERS), s13
  (FORGE_S13_TT_CHILD_PREFETCH), speedstack (FORGE_SPEEDSTACK), lazyacc (FORGE_NNUE_LAZY_ACC), prof (FORGE_PROF),
  int16 (FORGE_NNUE_INT16), initonce (FORGE_ATTACKS_INIT_ONCE), allsw = every `-DFORGE_*=` of
  `.github/workflows/opus-r3-switches.yml` (read at run time, so new switches join the all-ON build; today that
  set also has FORGE_DATAGEN, which the PC's allsw leaves out as engine-identical).
- Every build: `python3 opus_round1/ci/uci_check.py <forge>` (quick mode: bench 11/13/16 + perft5 startpos and
  kiwipete) must print ALL OK (every switch is node-exact with its UCI option off).
- python-chess 1.11.2 (the PC venv's version), pinned.

## Pass rule (the PC's)
Per config: all requested games (500 for every release config) played, 0 errors (crash, illegal move, double
bestmove, timeout, malformed output, info after bestmove, ...), preflight clean (options accepted, activation
lines present); per job: identity ALL OK (FMA 0) for every build; sanitizer jobs: 0 sanitizer reports. The
`summary` job prints the table (config, games, errors and errors by kind, plies, watchdog answers, HardDeadline
answers, sanitizer reports) and fails if any row fails or a job left no artifact.

## Results of a run
```
cd <worktree of opus-r3-sp-linux>
gh run list --branch opus-r3-sp-linux --workflow opus-r3-sp-linux --limit 3
gh run view <run id>                                  # job states
gh run download <run id> -n sp-summary -D F:/opus_scratch/r3/R3-1L/run_<run id>/summary   # SUMMARY.md + summary.json
gh run download <run id> -p 'sp-*' -D F:/opus_scratch/r3/R3-1L/run_<run id>/arts         # every job's logs
python3 -I -B opus_r3/R3-1L/summarize.py --jobs opus_r3/R3-1L/jobs.json --arts F:/opus_scratch/r3/R3-1L/run_<run id>/arts
```
(the last line rebuilds the table from the job artifacts, also for a run whose summary job has not run yet).

## Re-run on a newer stack head (main session)
```
cd F:/opus_scratch/worktrees/opus_r3_sp_linux
git fetch -q origin
git merge --no-edit origin/opus-r3-stack      # or <sha>
git merge --no-edit origin/opus-r3-selfplay   # if the checker/configs changed
git push -q -u origin opus-r3-sp-linux        # runs jobs.json "push_jobs" (now the 6 fin-* jobs) + opus-ci
gh workflow run opus-r3-sp-linux --ref opus-r3-sp-linux -f jobs=all          # every job (35) on the branch head
gh workflow run opus-r3-sp-linux --ref opus-r3-sp-linux -f jobs='fin-*,rel-all_on'   # a subset
```
Any push that changes something besides `*.md`, `opus_r3/**/logs/**`, FILES.txt or SHA256SUMS starts the
workflow with `push_jobs` (set it to `["all"]` in jobs.json to run everything on push); workflow_dispatch runs
the `jobs` input on the branch head without a new commit. New options or switches need a config (in
`R3-1_selfplay/configs_final.json` or `configs_final_head.json`) and a job entry in `jobs.json` (a config missing
from jobs.json is not run; `configs_file` names the configs file); new compile switches also need an exe key in
`run_job.sh` (`switch_args`) and, for the all-ON build, an entry in opus-r3-switches.yml (read automatically).
Runtime: a 1-config release job takes 10-11 min (500 games of all_on: 564 s), a TSan job 8 min (100 games);
the whole plan needs ~45 min only when ~20 runners are free (the account's limit is shared with other runs).
