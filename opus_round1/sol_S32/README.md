# S32 self-play datagen v2 — how to build and run

In-engine self-play that writes the residual trainer's `.pos` (FPOS v1) and `.hce` (FHCE v1) files directly.
Same game rules, filters and labels as the PC generator `nnue/forge-nnue-tools/forge_selfplay.py`
(25/25 games identical move by move, see REPORT.md), without python-chess, UCI pipes, the text step or the
`fen2bin` + `hce_dump` conversion.

## Engine change (patch: `forge_sol_S32_datagen_20261027.patch`)
- `include/forge/datagen.hpp`, `src/datagen.cpp`: the generator, the shard writer and a text converter (in `forge_core`).
- `src/uci.cpp`: with the build switch `FORGE_DATAGEN`, `forge datagen ...` runs the generator; any other start is the
  normal UCI engine. **Default OFF**: without the switch the exe is the lock binary (5 PE header bytes differ).
- `CMakeLists.txt`: `option(FORGE_DATAGEN ... OFF)` for `forge`; always-built `forge_datagen` (= forge with the switch),
  `forge_datagen_tests` (C++ unit tests) and the CTest `datagen_cli_tests` (`tests/datagen_cli_tests.py`, stdlib only).

## Build
- PC box recipe (datagen exe): `FORGE_EXTRA_SRCS=src/datagen.cpp nice -n 19 bash build_pc.sh "$PWD" <out.exe> -DFORGE_DATAGEN=1`
- PC box recipe (engine, unchanged): `nice -n 19 bash build_pc.sh "$PWD" <out.exe>`
- CMake: `forge_datagen` target, or `-DFORGE_DATAGEN=ON` for `forge` itself.

## Run
```
forge datagen --out D:/data/w1/sp --games 1000 --nodes 5000 --seed 11            # one process
forge datagen --out D:/data/w2/sp --games 1000 --nodes 5000 --seed 12            # another process: own prefix
forge datagen --out out/conv --convert forge_selfplay_001.txt --positions-per-file 20000000   # text -> .pos/.hce
```
Options (defaults = forge_selfplay.py defaults): `--nodes 5000` | `--depth D`, `--random-plies 8`, `--max-ply 300`,
`--win-cp 2000 --win-plies 4` (0 = off), `--draw-cp C --draw-plies N --draw-min-ply P` (draw adjudication, off by
default), `--max-score 3000`, `--hash 16`, `--seed 1`, `--positions-per-file 1000000`, `--openings FILE` (EPD/FEN
starts; default startpos), `--text` (also `FEN | score | result` lines), `--games N` and/or `--positions N` (required).

Outputs for prefix `P`: `P_NNN.pos` + `P_NNN.hce` (same stem: pass `--hce-dir` = their folder to the trainer),
`P_NNN.info` (config + record count), `P_NNN.txt` with `--text`, and `P.games` (one tab-separated line per game:
index, attempt, start, result, termination, records, opening moves, searched moves; header lines carry the config).
A JSON summary goes to stdout. Exit codes: 0 ok, 1 runtime error (e.g. prefix in use), 2 bad command line.

Multi-process safety: every file is written as `<name>.part` with exclusive create and then renamed without replacing
(Windows `rename`, POSIX `link`); the `.pos` is published last, so a `.pos` means a complete shard. `P.games.part` is
created first and claims the prefix: a second process with the same prefix exits 1 before writing anything. Use one
prefix per process (e.g. per seed). A crashed run leaves only `.part` files (never a short `.pos`).

Records and labels (identical to forge_selfplay.py): positions whose best move is quiet (no capture/promotion), side to
move not in check, no mate score and |score| <= 3000; score = search score from the side to move (cp); result =
White's game result; `.hce` = `Evaluator::evaluate_uncached` (byte-identical to `hce_dump` built at 1ab50b2d: the HCE
sources are identical). Each game starts with `searcher.clear()` ("ucinewgame"). Same seed => byte-identical files.
Not done here: dedupe (forge_selfplay.py keeps a persistent hash set; use a merge/dedupe step such as S40).

## Job tools (this folder)
- `run_pinned.py`: runs a command at IDLE priority on CPUs 4-11 only (not 0-3 = NNUE training, not 12-15 = production
  self-play) and reports wall + process-tree CPU seconds.
- `s32_parity_selfplay.py`: replays each datagen game with forge_selfplay.py's own `play_game()` over UCI (forced
  opening) and compares moves, records and results.
- `s32_throughput.py`: alternating datagen / forge_selfplay.py blocks, positions per wall second and per CPU second.
- `s32_v3b_loadcheck.py`: loads `.pos/.hce` with the v3b trainer's `load_set` and `load_set_mmap` (from a renamed copy
  of the trainer) and feeds batches through `make_batch`/`pack_batch`; label/sign statistics.
- `logs/`: every step's output (see REPORT.md). `logs/determinism_runs.log` is a first attempt that failed on a
  relative exe path (Windows CreateProcess); the runs are `logs/determinism_runs2.log`.
