# R3-6 Lazy SMP scaling: how to run

All commands from the worktree root in Git Bash, every process at idle priority
(`nice -n 19`; the harness also starts each engine with `IDLE_PRIORITY_CLASS`).
`PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe`, outputs under `F:/opus_scratch/r3/R3-6/`.

## 1. Engines
```
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
nice -n 19 bash $T/build_pc.sh "$PWD" /f/opus_scratch/build/r3_R3-6/<name>.exe          # PC lock recipe
# diagnostic (trace) build: scratch copy of the tree with FORGE_SMP_TRACE counters
nice -n 19 $PY -I -B opus_r3/R3-6/make_trace_src.py . /f/opus_scratch/build/r3_R3-6/<fresh_dir>
nice -n 19 bash $T/build_pc.sh /f/opus_scratch/build/r3_R3-6/<fresh_dir> /f/opus_scratch/build/r3_R3-6/trace.exe -DFORGE_SMP_TRACE=1
```
The trace build prints `info string smptrace ...` after every search (per-worker iteration timeline,
exit time, thread CPU time, TT probes/hits/cutoffs, join latency). The branch's engine sources contain no
trace code.

## 2. Positions and depths
```
nice -n 19 $PY -I -B opus_r3/R3-6/calibrate_positions.py <exe> opus_round1/O3/positions50.fen \
    $LA <out>/positions30.tsv --log <out>/calibration.jsonl
```
30 positions (10 opening, 12 middlegame, 8 endgame; the candidate lists and the screen are in the script
docstring), each with the deepest depth whose Threads=1 time-to-depth is <= 5.5 s (2-10 s). The result
used here is `positions30.tsv` in this folder.

## 3. Time-to-depth runs
```
bash opus_r3/R3-6/run_matrix.sh main  <head_exe> <fix_exe> <trace_exe> <out_dir> 3   # 1170 runs
bash opus_r3/R3-6/run_matrix.sh trace <head_exe> <fix_exe> <trace_exe> <out_dir>     # 330 runs
```
`run_matrix.sh` calls `smp_ttd.py` with the five configs (`off`, `on`, `on2` on the head exe; `offP`, `onP`
with `SmpHelpersPastDepth=true` on the fix exe, Threads 2/3 only). One fresh engine process per run (uci,
options, ucinewgame, position, `go depth D`, quit); the (config, threads) order is shuffled per repetition
and position. Resumable: rerunning skips the runs already in the output file (so use a fresh `<out_dir>`
for other executables). `--config-threads NAME=2,3` restricts a config to some thread counts.

## 4. Summaries
```
bash opus_r3/R3-6/make_summaries.sh <out_dir> opus_r3/R3-6/logs      # tables + per-position / per-run TSVs
nice -n 19 $PY -I -B opus_r3/R3-6/sysload.py --windows 6 --seconds 5  # PC load snapshot
```

## 5. Planted bugs for the new option
```
nice -n 19 $PY -I -B opus_r3/R3-6/mutation_check.py . /f/opus_scratch/build/r3_R3-6/<fresh_dir>
```
