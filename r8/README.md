# R8: fast self-play data generation (`forge_selfplay_fast`)

A native (C++) replacement for the Python orchestration of `forge-nnue-tools/forge_selfplay.py`. It drives the
**unchanged engine binary** over UCI exactly like the live script (same commands, same rules, same output lines),
so the data are the same by construction; the line-by-line equivalence test proves it. Nothing here replaces the
live workers: switching is the owner's decision. **v5** (2026-10-29) carries the fixes of the R8 code review.

## Build (MSYS2 ucrt64 g++, Git Bash, from the branch root)
```
python -I -B r8/tools/run_pinned.py --mask 0x000F -- r8/tools/build_driver.py <repo root> <dir>\forge_selfplay_fast.exe
```
(`run_pinned.py` keeps the compiler on CPUs 0-3 at BelowNormal.) The driver links Forge's own Board
(`src/board.cpp`, `src/bitboard.cpp` of this tree, Forge 6.2.0 release source) for the chess rules only; the
engine that searches is whatever `--engine` names. The build also puts `r8/tools/dedup_against_db.py` next to the
exe (the default `--post-script`); an existing copy there is never replaced (a different one is reported), so build
into a new folder after changing the tool.

## Run (the live configuration, written to a NEW folder)
```
forge_selfplay_fast.exe --engine C:\Users\Administrator\grok-pc\nnue\forge.exe --out D:\grok-pc-data\selfplay_out_fast ^
    --workers 2 --nodes 5000 --hash 16 --pos --progress-seconds 60
```
- The driver itself runs at **BelowNormal**, pinned to `--cpus` (default **12-15**), inside a **job object** with
  kill-on-close: its engines and post-steps end with it, also after `taskkill /F` of the driver alone.
- Engines start at Idle priority (`--priority belownormal` to change), each worker on its own slice of `--cpus`
  (2 workers on 12-15 -> 12-13 and 14-15), like the live script otherwise.
- `--out` must not exist; `--resume` continues in an existing folder (see "Stop, kill, resume"). One driver per
  folder (`<prefix>.lock`, held open for the run).
- **Seed**: `--seed S` reproduces a run; without it the seed is `random_device ^ time ^ pid` and is printed at the
  start (`seed=...`) and written into every `.pos.info`, so a restart never replays the same games.
- **Engine deadline**: every answer (uciok, readyok, bestmove) must arrive within `--engine-timeout` seconds
  (default 180). A silent engine is killed and restarted, its game dropped; a dead engine (pipe closed) is restarted
  the same way. After `--max-restarts` + 1 failures in a row (default 6) the worker gives up.
- **Shards**: data are written to `<prefix>_NNN.txt.part` (+ `.pos.part` with `--pos`) and renamed to `.txt` / `.pos`
  (+ `.pos.info`) only when the shard is complete: after `--lines-per-file` lines (default **1,000,000**) or
  `--rotate-minutes` (default **30**). A final `.txt` always means a complete shard. Buffers reach the file at game
  boundaries at least every `--flush-seconds` (default 5).
- **Memory**: run-local de-duplication in a bounded table of `--dedup-mb` MB (default **64**; `--dedup exact` = an
  exact set for tests); `.pos` boards stream to the `.pos.part` file, only 3 bytes per record wait in memory for the
  file's tail. Measured: driver 70.9 MB working set with the real engine, 75.6 MB peak over a full 1M-line shard;
  each engine 25 MB; job peak commit 120 MB for 1 worker (v4: about 0.9 GB with its 512 MB table and 350 MB .pos
  buffer). Every progress line prints the driver's and the engines' RSS and the job's peak commit; `--job-memory-mb`
  can cap the whole job (default off).
- **Global de-duplication** (the live pipeline drops positions already in its 7.5 GB hash DB): after each finished
  shard the driver runs `dedup_against_db.py --shard` (one at a time, BelowNormal, in the job) against the live DB
  `--dedup-db` (default `D:\grok-pc-data\selfplay_out\forge_seen_hashes.sqlite3`, opened read only and immutable,
  never written) and its own DB `<out>\<prefix>_seen.sqlite3` (keys of all earlier shards of this folder).
  Results: `<prefix>_NNN.dedup.txt`, `.dedup.pos` + `.dedup.pos.info` (the files to train on), and
  `.dedup.json` (counts; written last = done), the tool's output in `.dedup.log`. `--no-global-dedup` skips it; that
  data change is printed at the start and written into every `.pos.info` (`global_dedup=OFF`).
  The live DB lookup is exact while the live pipeline is stopped (the normal case after switching). While it writes,
  the immutable connection sees stale pages: the tool retries a failed lookup on a fresh connection, finishes, and
  records `live_db.changed_during_scan` / `exact: false` in the JSON (a few keys can be missed). 1M lines took
  24.5-87 s; the post-step's own peak RSS was 224 MB.
- Every write, flush, rename and close is checked; an output error stops the run with exit code 4 and the `.part`
  files stay for `--resume`.
- Stops after `--max-minutes` or `--games-per-worker`, on the STOP file, on Ctrl+C / Ctrl+Break, or when every
  engine is dead; otherwise runs until the process is ended.
- `--openings FILE` plays fixed openings (one game per line, UCI moves) instead of random ones (used by the test).

## Stop, kill, resume
- Clean stop: create the STOP file (`--stop-file`, default `<out>\STOP`). The driver drops the games in progress,
  finishes the open shard, waits for the post-steps, exits 0. It does not start while the STOP file exists.
- Hard kill (`taskkill /T /F`, power loss of the process): the open shard stays as `.txt.part`. `--resume` keeps every
  complete line of it (a torn last line is cut), rebuilds its `.pos` from the text, publishes it as a shard and runs
  the missing post-steps; so a kill loses the games in progress plus at most `--flush-seconds` of finished games.
- Exit codes: 0 done; 2 usage / refused (existing `--out` without `--resume`, another driver in the folder, missing
  post-step tools); 3 every engine is dead; 4 output (I/O) error; 5 some workers gave up; 6 a post-step failed (the
  raw shard is complete; `--resume` runs the post-step again).

## Options that change the data (all OFF / at the live values by default)
`--own-book true` (the live script leaves the engine default `OwnBook=true`; the driver sets false, see the report),
`--hash` (live 16), `--nodes` (live 5000), `--opening-plies` (8), `--max-ply` (300), `--adjudicate-cp` (2000),
`--adjudicate-plies` (4), `--max-score` (3000), `--no-dedup`, `--no-global-dedup`, `--check-nodes N` (in-check
positions, which are never recorded, searched with N nodes instead of `--nodes`: same labels, a different game path
after them).

## Tests
- `r8/tests/test_driver_v5.py <driver.exe> <fake_engine.exe> <scratch> --cpus 2-3`: 15 checks of the v5 behaviour with
  the fault-injection engine `r8/tests/fake_engine.cpp` (build: `r8/tests/build_fake_engine.py`): refused `--out`,
  random vs fixed seed, engine hang -> kill -> restart, engine exit -> restart, all engines dead -> exit 3, rotation +
  STOP (no `.part` left, every `.pos` == its text), STOP blocks a start, hard kill (test hook) leaves a `.txt.part`
  and no engine alive, `--resume` salvages every complete line, write error -> exit 4, one driver per folder, the
  post-step tool (live DB, own DB, inside-shard, killed-attempt and stale-output cases), the post-step run by the
  driver, the RSS line. Logs: `r8/logs/v5/test_run{1,2}.log`.
- `r8/tools/equivalence_ref.py gen 60 <seed> openings.txt`, then `ref <engine> openings.txt ref.txt --cpus 2-3` (the
  live `play_game()` itself) and `forge_selfplay_fast --openings openings.txt --no-dedup --no-global-dedup ...`: the
  two text files must be byte-identical (`r8/logs/v5/eq.log`).
- `r8/tools/check_pos_vs_text.py <file.pos> <file.txt>`: the `.pos` holds exactly the text file's records.
- `r8/tools/quality_check.py base=<baseline.txt> fast=<driver.txt>`: score / result / ply spread, duplicates.
- `r8/tests/peak_rss.py <cmd...>`: peak working set of a command and its child processes.
