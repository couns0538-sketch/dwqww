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
nice -n 19 $PY -I -B opus_r3/R3-6/smp_ttd.py --positions opus_r3/R3-6/positions30.tsv \
  --config "off=<exe>" \
  --config "on=<exe>|SmpExactNodes=true,SmpBestThread=true,LocklessTT=true" \
  --config "on2=<exe>|SmpExactNodes=true,SmpBestThread=true,LocklessTT=true,CorrHistPlus=7,CorrMargins=1,CorrExt=1,CuckooRep=true,HistRework=2,MaterialKeyTable=true" \
  --threads 1,2,3 --reps 3 --hash 64 --out <out>/ttd_main.jsonl
```
One fresh engine process per run (uci, options, ucinewgame, position, `go depth D`, quit); the
(config, threads) order is shuffled per repetition and position. Resumable: rerunning skips the runs
already in `--out`. `--config-threads NAME=2,3` restricts a config to some thread counts.

## 4. Summaries
```
nice -n 19 $PY -I -B opus_r3/R3-6/summarize.py <out>/ttd_main.jsonl --by-class --tsv opus_r3/R3-6/logs/ttd_per_position.tsv
nice -n 19 $PY -I -B opus_r3/R3-6/trace_summary.py <out>/ttd_trace.jsonl --tsv opus_r3/R3-6/logs/trace_per_run.tsv
nice -n 19 $PY -I -B opus_r3/R3-6/sysload.py --windows 6 --seconds 5      # PC load snapshot
```

## 5. Planted bugs for the new option
```
nice -n 19 $PY -I -B opus_r3/R3-6/mutation_check.py . /f/opus_scratch/build/r3_R3-6/<fresh_dir>
```
