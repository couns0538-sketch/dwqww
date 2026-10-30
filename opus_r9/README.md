# R9: SPSA tuning of Forge's search parameters (branch `opus-r9-spsa`)

Base: the AL1 lock `d4f4312` + the CI baseline `0d99f02`. Everything new for R9 is in `src/search.cpp`,
`src/uci.cpp`, `include/forge/search.hpp` (the `R9Tune` layer) and in this folder.

## Engine: `R9Tune`
- `option name R9Tune type check default false`. While it is off the search runs on the lock's values whatever
  else is set: bench and perft equal the lock pins (312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609).
- 74 tunables are advertised as spin options with the lock values as defaults: the lock's 51 `forge::tune` constants
  (LMR table, null move, RFP, razoring, futility, LMP, history pruning, SEE, singular, IIR, ProbCut, qsearch,
  aspiration, history bonus, check extension, correction weight, time manager, capture futility) and 23 former
  literals of the search (null-move eval margin / cap / verification depth, ProbCut improving / reduction, singular
  TT depth / double-extension margin / limit, the seven LMR adjustments in 1/1024 ply, history bonus offset / malus
  percent / depth margin, aspiration start depth and widening, the quiet check ordering bonus). Values set with
  `setoption` are kept while R9Tune is off and take effect when it is switched on.
- Example: `setoption name R9Tune value true`, `setoption name LmrQuietDivisor value 230`.

## Build and checks (all on CPUs 0-3, BelowNormal)
```
python -I -B opus_r9/tools/run_pinned.py --mask 0x000F -- opus_r9/tools/build_r9.py <tree> <out.exe>
python -I -B <lock>/2_build/uci_check.py <out.exe> --full                       # R9Tune off: ALL OK
python -I -B opus_r9/tools/identity_opts.py <out.exe> --full --opt R9Tune=true  # on at defaults: ALL OK
python -I -B opus_r9/tools/r9_option_check.py <out.exe> --depth 11              # advertised, gated, wired
JOBS=1 python -I -B opus_r9/tools/run_pinned.py --mask 0x000F -- opus_r9/tools/bash_run.py \
    opus_r9/tools/run_ctest_r9.sh <tree> <build dir> <ctest log>                 # CMake all targets + CTest
```

## Tuner
```
python -I -B opus_r9/tools/run_pinned.py --mask 0x000F -- opus_r9/tuner/r9_spsa.py run opus_r9/configs/stc_main.json <run_dir> [--max-pairs N] [--until HH:MM]
python -I -B opus_r9/tuner/r9_spsa.py status <run_dir>
python -I -B opus_r9/tuner/r9_spsa_report.py <run_dir> --out <dir> --exe <engine path for QA>
python -I -B opus_r9/tuner/test_r9_spsa_sim.py <scratch>     # no games: the update's sign, noise, resume
```
- Stop a run with the file `<run_dir>/STOP` (after the current batch); continue it with the same config and
  `--resume`. Everything in `<run_dir>` is append-only (`iterations.jsonl`, `history.csv`, `tuner.log`, `games/`).
- The governor plays a batch only with the concurrency the 70% CPU cap leaves (sampled between batches) and waits
  otherwise; free RAM must be at least 8 GB.
- Config format (`configs/*.json`): engine, fastchess, book, tc, hash, `pairs_planned` (N of the schedule),
  `pairs_per_batch`, alpha / gamma / A_ratio, seed, governor, and per parameter `name, start, min, max, c_end, r_end`.
