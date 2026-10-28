# R3-1 self-play checker (opus_r3/R3-1_selfplay)

Fast self-games between two processes of the same Forge build and options, with a protocol check after every
command; one run per configuration ("every option ON alone, every build switch ON alone, all ON together").
The test requirement (R3-1): no crash, no illegal move, no double bestmove over 500 fast self-games per config.

## Files
| file | what |
|---|---|
| `opus_selfplay_check.py` | the checker for one config (python-chess; `--help` lists every check) |
| `run_matrix.py` | runs the configs of a config file one after the other (re-read before each), then writes `MATRIX.md` + `matrix_summary.json` (sha256 of every log) |
| `configs_final.json` | the final-head set (36 configs, two runners A/B, lower per-move budgets, activation lines to expect) |
| `configs.json`, `configs_2047348a.json` | the sets used on the base head 2432670b and prepared for 2047348a |
| `build_engines.sh` | builds the engine set of a head (base, one exe per build switch, all switches; PC recipe) |
| `make_nets.py` | writes the v2 nets the configs load (lock replicas and stand-alone copies, all function-preserving) |
| `fault_proxy.py`, `selftest_faults.py` | harness self-test: a proxy that breaks the protocol once per fault; the harness must report each |
| `repro_late_info.py` | minimal repro of the HardDeadline finding (info line after the watchdog's bestmove); 0 late lines on a fixed head |
| `finish_final.sh` | after the hand-back: `status` (runners alive? finished configs), `resume` (restart runners A/B for the configs without a complete summary; refuses while any runner/checker of the head lives), `collect` (MATRIX.md, copy evidence, FILES/SHA256SUMS) |
| `logs/` | small evidence (matrix tables, summaries, preflights, self-test, repro, build and bench logs); big logs stay in `F:\opus_scratch\r3\selfplay\` (sha256 in `logs/*/matrix_summary.json`) |

## Run (PC; Git Bash; everything at nice 19, outputs on F:)
```
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
S=/f/opus_scratch/r3/selfplay
# engines (base, o2, nozero, s13, speedstack, lazyacc, prof, int16, initonce, allsw = every switch)
bash opus_r3/R3-1_selfplay/build_engines.sh "$PWD" $S/engines/<head>
# nets (replicas from src/nnue_weights.inc; the PureNnue net is O4's material-trained smoke net)
nice -n 19 $PY -I -B opus_r3/R3-1_selfplay/make_nets.py "$PWD" F:/opus_scratch/r3/selfplay/nets \
    F:/opus_scratch/o4/r4/o4_cpu_material/epoch004-step000000780.fnn2
# freeze the checker for the run (edits in the worktree then cannot reach a running matrix)
H=$S/harness/final_<head>; mkdir -p $H; cp opus_r3/R3-1_selfplay/{opus_selfplay_check.py,run_matrix.py,configs_final.json} $H/
# preflight of every config (options advertised + accepted, activation lines, go depth 5, bench 11)
nice -n 19 $PY -I -B $H/run_matrix.py --engines F:/opus_scratch/r3/selfplay/engines/<head> \
    --nets F:/opus_scratch/r3/selfplay/nets --out F:/opus_scratch/r3/selfplay/runs/preflight_<head> --git-head <head> \
    --configs $H/configs_final.json --epd "$PWD/tools/openings/forge-10000.epd" --preflight-only
# the matrix: two runners sharing one --out (same command with --runner A --log-name matrix_A.log and
# --runner B --log-name matrix_B.log, --out .../runs/<head>), then the whole table:
nice -n 19 $PY -I -B $H/run_matrix.py ... --out F:/opus_scratch/r3/selfplay/runs/<head> --report-only
# harness self-test (about 4 minutes) and the HardDeadline repro
nice -n 19 $PY -I -B opus_r3/R3-1_selfplay/selftest_faults.py --engine $S/engines/<head>/opus_r3sp_base.exe --out $S/runs/selftest_<head>
nice -n 19 $PY -I -B opus_r3/R3-1_selfplay/repro_late_info.py $S/engines/<head>/opus_r3sp_base.exe --deadline 1 --threads 2 --movetime 30 --n 600
```
run_matrix.py reads the configs file again before every config (configs can be added, removed or reordered
while it runs; top-level "parallel" / "parallel_smp" / "harness_args" keys apply from the next config on), so a
running matrix is steered or ended between configs by editing its configs file, without stopping processes.
`--runner X` takes only the configs with `"runner": "X"`; per-config `"expect"` lists are activation lines the
preflight must print. Lower per-move budgets: "harness_args" (`--nodes-min`, `--nodes-max`, `--mix`).

Per config the checker writes `<name>.games.jsonl` (one record per game: config, opening, result, termination,
plies, command counts, latencies, errors with the offending lines and the last 40 transcript lines),
`<name>.summary.json`, `<name>.preflight.json/.log`, `<name>.pgn`, `<name>.events.log`, and
`errgames/<name>_g<game>.log` (full timestamped transcripts of both engines for every game with an error).
Exit status: 0 clean, 1 errors, 3 preflight failed, 4 fewer games than requested.

## What one game does
Opening: a random position of `tools/openings/forge-10000.epd` (seed:game, so game i is the same in every
config); colours alternate. Both engines: `ucinewgame` + `isready`. Each move: (3%: a stray `stop` to the idle
engine) `position fen ... moves ...`, `isready` -> `readyok` (barrier: a late or unsolicited bestmove of the
previous search would arrive before it), then one of (default mix; the final run used nodes 200-2000 and
58/8/10/8/6/5/5): `go nodes 300-5000` (50%), clocked `go wtime/btime/winc/binc` from the game clock (0.2-2 s +
0/10/20/30/50 ms, 15%), `go movetime 5-30` (8%), `go depth 1-6` (8%), `go infinite` + `stop` after 5-50 ms (7%),
`go ponder` + `ponderhit` (6%), ponder miss: `go ponder` on another opponent move + `stop`, then a clocked go on
the real position (6%); 30% of infinite/ponder searches also get an `isready` mid-search. End: mate, stalemate,
insufficient material, threefold, 50-move rule, or 200 plies. Engine pairs restart every 25 games (exit status 0
checked at quit).
