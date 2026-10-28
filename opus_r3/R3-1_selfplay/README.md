# R3-1 self-play checker (opus_r3/R3-1_selfplay)

Fast self-games between two processes of the same Forge build and options, with a protocol check after every
command; one run per configuration ("every option ON alone, every build switch ON alone, all ON together").
The test requirement (R3-1): no crash, no illegal move, no double bestmove over 500 fast self-games per config.

## Files
| file | what |
|---|---|
| `opus_selfplay_check.py` | the checker for one config (python-chess; `--help` lists every check) |
| `run_matrix.py` | runs every config of a config file, one after the other, then writes `MATRIX.md` + `matrix_summary.json` (sha256 of every log) |
| `configs.json` | configs for the base head 2432670b (28 + 3 optional CorrHistPlus levels) |
| `configs_2047348a.json` | configs for heads from 2047348a on: + `sw_nnue_lazy_acc` (S12), `sw_prof` (S08fix), both in the all-ON build |
| `make_nets.py` | writes the v2 nets the configs load (lock replicas and stand-alone copies, all function-preserving) |
| `fault_proxy.py`, `selftest_faults.py` | harness self-test: a proxy that breaks the protocol once per fault; the harness must report each |
| `repro_late_info.py` | minimal repro of the HardDeadline finding (info line after the watchdog's bestmove); must print 0 late lines on a fixed head |
| `logs/` | small evidence (matrix tables, summaries, self-test, build and bench logs); big logs stay in `F:\opus_scratch\r3\selfplay\` (sha256 in `logs/`) |

## Run (PC; Git Bash; everything at nice 19, outputs on F:)
```
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
E=/f/opus_scratch/r3/selfplay/engines/<head>
# engines: base + one per build switch + all switches (FORGE_PROF needs FORGE_EXTRA_SRCS=src/profile.cpp)
nice -n 19 bash $T/build_pc.sh "$PWD" $E/opus_r3sp_base.exe
nice -n 19 bash $T/build_pc.sh "$PWD" $E/opus_r3sp_o2.exe -DFORGE_NNUE_O2=1          # nozero, s13, speedstack, lazyacc likewise
FORGE_EXTRA_SRCS=src/profile.cpp nice -n 19 bash $T/build_pc.sh "$PWD" $E/opus_r3sp_prof.exe -DFORGE_PROF=1
FORGE_EXTRA_SRCS=src/profile.cpp nice -n 19 bash $T/build_pc.sh "$PWD" $E/opus_r3sp_allsw.exe -DFORGE_NNUE_O2=1 \
    -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_S13_TT_CHILD_PREFETCH=1 -DFORGE_SPEEDSTACK=1 -DFORGE_NNUE_LAZY_ACC=1 -DFORGE_PROF=1
# nets (replicas from src/nnue_weights.inc; the PureNnue net is O4's material-trained smoke net)
nice -n 19 $PY -I -B opus_r3/R3-1_selfplay/make_nets.py "$PWD" F:/opus_scratch/r3/selfplay/nets \
    F:/opus_scratch/o4/r4/o4_cpu_material/epoch004-step000000780.fnn2
# all configs (preflight of one config: add --preflight-only; one config: --only name)
nice -n 19 $PY -I -B opus_r3/R3-1_selfplay/run_matrix.py --engines F:/opus_scratch/r3/selfplay/engines/<head> \
    --nets F:/opus_scratch/r3/selfplay/nets --out F:/opus_scratch/r3/selfplay/runs/<head> --git-head <head> \
    --configs opus_r3/R3-1_selfplay/configs_2047348a.json
# harness self-test (about 3 minutes)
nice -n 19 $PY -I -B opus_r3/R3-1_selfplay/selftest_faults.py --engine $E/opus_r3sp_base.exe --out F:/opus_scratch/r3/selfplay/runs/selftest
```
run_matrix.py reads the configs file again before every config (configs can be added, removed or reordered
while it runs; top-level "parallel" / "parallel_smp" / "harness_args" keys apply from the next config on), so a
running matrix is steered or ended between configs by editing its configs file, without stopping processes.
Several runners can share one `--out` with different `--log-name`; `--report-only` then rebuilds MATRIX.md for
the whole config list. Lower per-move budgets: `--harness-arg=--nodes-min=200` etc. or "harness_args".

Per config the checker writes `<name>.games.jsonl` (one record per game: config, opening, result, termination,
plies, command counts, latencies, errors with the offending lines and the last 40 transcript lines),
`<name>.summary.json`, `<name>.preflight.json/.log`, `<name>.pgn`, `<name>.events.log`, and
`errgames/<name>_g<game>.log` (full timestamped transcripts of both engines for every game with an error).
Exit status: 0 clean, 1 errors, 3 preflight failed, 4 fewer games than requested.

## What one game does
Opening: a random position of `tools/openings/forge-10000.epd` (seed:game, so game i is the same in every
config); colours alternate. Both engines: `ucinewgame` + `isready`. Each move: (3%: a stray `stop` to the idle
engine) `position fen ... moves ...`, `isready` -> `readyok` (barrier: a late or unsolicited bestmove of the
previous search would arrive before it), then one of: `go nodes 300-5000` (50%), clocked
`go wtime/btime/winc/binc` from the game clock (0.2-2 s + 0/10/20/30/50 ms, 15%), `go movetime 5-30` (8%),
`go depth 1-6` (8%), `go infinite` + `stop` after 5-50 ms (7%), `go ponder` + `ponderhit` (6%), ponder miss:
`go ponder` on another opponent move + `stop`, then a clocked go on the real position (6%); 30% of
infinite/ponder searches also get an `isready` mid-search. End: mate, stalemate, insufficient material,
threefold, 50-move rule, or 200 plies. Engine pairs restart every 25 games (exit status 0 checked at quit).
