# R3-2 interaction matrix: how to run

Branch `opus-r3-matrix` (base `2432670b` = opus-r3-stack@467a59b3 + the CMake test fix). Tools only; no engine
change. Run everything from Git Bash at idle priority; outputs go to `F:\opus_scratch` (paths below are the
defaults of the scripts).

```
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
cd /f/opus_scratch/worktrees/opus_r3_matrix
# 1. seven exes (PC lock recipe, one g++ at a time) + lock-pin identity of each (base --full)
nice -n 19 bash opus_r3/R3-2/build_all.sh "$PWD" /f/opus_scratch/build/r3_R3-2 > build_all.log
#    after merging a newer stack head: rebuild the switch set (byte compare with step 1) + the new switches
nice -n 19 bash opus_r3/R3-2/build_h2.sh "$PWD" /f/opus_scratch/build/r3_R3-2 > build_h2.log
# 2. function-preserving v2 replica nets (+ the r1 weights flagged stand-alone for PureNnue)
nice -n 19 $PY -I -B opus_r3/R3-2/r3_matrix.py nets
# 3. the configurations (64; configurations whose exe is missing are skipped)
$PY -I -B opus_r3/R3-2/r3_matrix.py list
# 4. nodes pass + NPS pass + report tables (about 1.5 h on the loaded PC)
nice -n 19 bash opus_r3/R3-2/run_matrix.sh 8            # 8 = fresh processes per side
#    single configurations / reruns / more pairs for a configuration measured before:
nice -n 19 $PY -I -B opus_r3/R3-2/r3_matrix.py nodes --only CHP7_CM,CM --reps 2
nice -n 19 $PY -I -B opus_r3/R3-2/r3_matrix.py nps --only CHP7_CM --runs 8
nice -n 19 $PY -I -B opus_r3/R3-2/r3_matrix.py nps --only CHP7_CM --runs 8 --append
$PY -I -B opus_r3/R3-2/r3_matrix.py report --md table.md                  # --metric cycles (default) | cpu | wall
```

## What the script measures
- **Builds** (`build_all.sh`): `base` (no switch), `base_copy` (byte copy, A/A control), `o2`
  (`-DFORGE_NNUE_O2=1`), `nozero` (`-DFORGE_NOZERO_MOVE_BUFFERS=1`), `s13` (`-DFORGE_S13_TT_CHILD_PREFETCH=1`),
  `speedstack` (`-DFORGE_SPEEDSTACK=1`), `ss_s13` (both of the last two).
- **Configuration** = exe + UCI options + Threads + the single configurations it combines (`parts`). The list is
  `configs()` in `r3_matrix.py`; `expect` says whether the configuration is node-exact by design (bench must equal
  the lock pins) or changes the tree; `ref` holds the branch reports' ON pins where they exist.
- **Nodes** (`nodes`): `bench 11`, `bench 13`, `bench 16` in one process; two fresh processes per configuration
  (determinism). Records transient ERROR lines before `readyok` (a half-set v2 request while the options arrive one
  at a time; the engine resolves or exits at `isready`), ERROR lines after `readyok`, the exit status and the
  `info string` setup lines (v2 "active" line, Syzygy, TtChildPrefetch).
- **NPS** (`nps`): ABBA order (A B B A ...), A = `base.exe` with no option at the same Threads, B = the
  configuration; one fresh process per run, created at IDLE priority. T1: `bench 16`. T2: the 8 bench positions,
  each `ucinewgame` / `position fen` / `go depth 16` at Threads 2, Hash 16 (bench always searches with one worker:
  `forge::Searcher bench_searcher(16)` in `src/uci.cpp`, so Threads never reaches bench). CPU time is taken right
  before the measured command and right after its last line, so start-up and net loading are excluded, in two
  ways: `QueryProcessCycleTime` (CPU time of all threads counted with the TSC at every context switch; the
  default metric) and `GetProcessTimes` (user + kernel, as in `nps_ab.py`). On the loaded PC the latter is
  tick-sampled (15.625 ms ticks charged to whichever thread runs at the interrupt) and about 5x noisier: A/A
  per-run sd 3.8-4.9% vs 0.7-1.0% (`logs/nps.log`, AA_T1). Wall time is recorded too. The interval is the paired
  one: the mean log ratio of the ABBA pairs with a Student t quantile; the Welch interval of `nps_ab.py` is kept in
  the notes. FORGE_PROF configurations that count use `bench_prof` (the UCI `Profile` option never reaches bench).
- **Report** (`report`): the matrix table, the pair analysis (log-additive prediction, interaction with its
  interval, leave-one-out contribution of each part) and the flags; `--metric cpu|cycles|wall` picks the NPS
  measure. `analysis.json` in the results folder holds every estimate.

Machine exclusive: no. Every NPS figure is advisory.
